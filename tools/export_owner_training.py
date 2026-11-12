"""Read only pinned training files; emit recipient-encrypted bytes, never plaintext artifacts."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import zipfile

MAGIC = b'UN-OWNER-EXPORT-v1\n'
MAX_BUNDLE = 16 * 1024 * 1024
PILOT_REVISION = '81735557d162fe8e4180ea035bea172c5c00a929'
PILOT_PREFIX = 'pilots/43156908706-1/'
REVIEWER_REVISION = 'd90a021976f4acca064930f73733926c54d91958'
REVIEWER_PREFIX = 'reviewers/43217469148-1/'


def public_key(value):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    if not isinstance(value, bytes) or len(value) > 8192:
        raise ValueError('Invalid recipient key')
    key = serialization.load_pem_public_key(value)
    if not isinstance(key, rsa.RSAPublicKey) or key.key_size != 4096 or key.public_numbers().e != 65537:
        raise ValueError('Recipient requires RSA-4096 with exponent 65537')
    return key


def encrypt_bundle(data, recipient):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BUNDLE:
        raise ValueError('Invalid owner bundle size')
    key = public_key(recipient)
    aes_key = AESGCM.generate_key(bit_length=256); nonce = os.urandom(12)
    wrapped = key.encrypt(aes_key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    der = key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    header = json.dumps({'schema':'un.encrypted-owner-export.v1',
        'recipient_sha256':hashlib.sha256(der).hexdigest(),
        'wrapped_key':base64.b64encode(wrapped).decode(), 'nonce':base64.b64encode(nonce).decode()},
        sort_keys=True,separators=(',',':')).encode()
    encrypted = AESGCM(aes_key).encrypt(nonce, data, MAGIC+header)
    return MAGIC+struct.pack('>I',len(header))+header+encrypted


def decrypt_bundle(data, recipient_private):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not data.startswith(MAGIC) or len(data) > MAX_BUNDLE+8192:
        raise ValueError('Invalid encrypted owner export')
    offset=len(MAGIC); length=struct.unpack('>I',data[offset:offset+4])[0]
    if not 0 < length <= 4096: raise ValueError('Invalid encrypted header')
    raw=data[offset+4:offset+4+length]; header=json.loads(raw)
    if set(header) != {'schema','recipient_sha256','wrapped_key','nonce'} or header['schema']!='un.encrypted-owner-export.v1':
        raise ValueError('Unexpected encrypted header')
    private=serialization.load_pem_private_key(recipient_private,password=None)
    if not isinstance(private,rsa.RSAPrivateKey) or private.key_size!=4096:
        raise ValueError('Invalid recipient private key')
    der=private.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
    if hashlib.sha256(der).hexdigest()!=header['recipient_sha256']:
        raise ValueError('Wrong recipient')
    nonce=base64.b64decode(header['nonce'],validate=True)
    if len(nonce)!=12:raise ValueError('Invalid encryption nonce')
    key=private.decrypt(base64.b64decode(header['wrapped_key'],validate=True),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    plain=AESGCM(key).decrypt(nonce,data[offset+4+length:],MAGIC+raw)
    if not 0<len(plain)<=MAX_BUNDLE:raise ValueError('Invalid decrypted bundle size')
    return plain


def training_zip(storage):
    """Exact allowlist: no calibration/test originals, annotations or credentials."""
    from un_transcript.snapshots import sha
    storage.info()  # Requires the repository to remain private.
    reviewer_raw=storage.read(REVIEWER_PREFIX+'manifest.json',REVIEWER_REVISION,1024*1024)
    reviewer=json.loads(reviewer_raw)
    if (reviewer.get('schema')!='un.private-reviewer.v1' or reviewer.get('split')!='train'
            or reviewer.get('examples')!=180 or reviewer.get('dataset_revision')!=PILOT_REVISION
            or reviewer.get('packet_prefix')!=PILOT_PREFIX):
        raise ValueError('Unexpected training reviewer identity')
    packet_raw=storage.read(PILOT_PREFIX+'packet-manifest.json',PILOT_REVISION,1024*1024)
    if sha(packet_raw)!=reviewer['manifest_sha256']:raise ValueError('Original pilot manifest mismatch')
    packet=json.loads(packet_raw); entries={entry['path']:entry for entry in packet['files']}
    files={'01_training/provenance/reviewer-manifest.json':reviewer_raw,
           '01_training/provenance/packet-manifest.json':packet_raw}
    for name, destination in [('train-draft.json','original-training-draft.json'),('review/train-review.csv','train-review.csv')]:
        item=entries[PILOT_PREFIX+name]
        if type(item['bytes']) is not int or not 0<item['bytes']<=MAX_BUNDLE:raise ValueError('Invalid training file bound')
        raw=storage.read(PILOT_PREFIX+name,PILOT_REVISION,item['bytes'])
        if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:raise ValueError('Training file checksum mismatch')
        files['01_training/provenance/'+destination]=raw
    draft=json.loads(files['01_training/provenance/original-training-draft.json'])
    if len(draft.get('rows',[]))!=180 or len({r['pair_id'] for r in draft['rows']})!=180 or any(r.get('split')!='train' or r.get('owner_confirmed') for r in draft['rows']):
        raise ValueError('Only the original unreviewed training split may be exported')
    html=storage.read(REVIEWER_PREFIX+'training-review.html',REVIEWER_REVISION,MAX_BUNDLE)
    if sha(html)!=reviewer['html_sha256']:raise ValueError('Private reviewer checksum mismatch')
    match=re.search(rb'<script id="packet" type="application/json">(.*?)</script>',html,re.S)
    if not match or json.loads(match[1])['draft']!=draft:raise ValueError('Reviewer payload differs from original training split')
    files['01_training/training-review.html']=html
    receipt={'schema':'un.owner-training-download.v1','examples':180,'split':'train',
             'pilot_revision':PILOT_REVISION,'reviewer_revision':REVIEWER_REVISION,
             'files':[{'path':path,'bytes':len(raw),'sha256':sha(raw)} for path,raw in sorted(files.items())]}
    files['01_training/provenance/download-manifest.json']=json.dumps(receipt,indent=2).encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path,raw in sorted(files.items()):archive.writestr(path,raw)
    if len(stream.getvalue())>MAX_BUNDLE:raise ValueError('Training ZIP exceeds transfer bound')
    return stream.getvalue()


def main():
    from un_transcript.snapshots import HFStorage
    recipient=base64.b64decode(os.environ['OWNER_RECIPIENT_PUBLIC_KEY'],validate=True)
    public_key(recipient)  # Validate before any private read.
    result=encrypt_bundle(training_zip(HFStorage(os.environ['HF_DATASET_REPO'])),recipient)
    path=Path(os.environ['RUNNER_TEMP'])/'owner-training.encrypted'
    path.write_bytes(result)
    print(json.dumps({'status':'recipient_encrypted','examples':180,'split':'train',
                      'ciphertext_bytes':len(result),'ciphertext_sha256':hashlib.sha256(result).hexdigest()}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'failed','error_type':type(error).__name__}))
        raise SystemExit(1)
