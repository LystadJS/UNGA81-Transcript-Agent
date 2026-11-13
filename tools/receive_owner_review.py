"""Recipient-encrypted, bounded private owner intake. Never train or publish labels."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import re
import uuid
import zipfile
import zlib

from tools.export_owner_training import encrypt_bundle, decrypt_bundle, public_key, training_zip
from un_transcript.models.review_intake import IDENTITY, reconcile
from un_transcript.snapshots import HFStorage, RemoteEntryMissing, StorageRequestError, encode, sha

MAX_RETURN = 2 * 1024 * 1024
MAX_CIPHER = 256 * 1024
PART_CHARS = 48000
MAX_PARTS = 8
LATEST = 'owner-intake/train/latest.json'
POINTER_FIELDS = {'schema','prefix','revision','manifest_sha256','input_sha256','cipher_sha256','key_id'}


def bounded_id(value, width):
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{'+str(width)+'}', value):
        raise ValueError('Invalid immutable identity')
    return value


def strict_json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('Duplicate JSON field')
            result[k] = v
        return result
    def invalid(_):
        raise ValueError('Nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def utc(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp requires timezone')
    return parsed


def optional(storage, path, revision, maximum=16384):
    try:
        return storage.read(path, revision, maximum)
    except RemoteEntryMissing:
        return None  # Authentication, outages and unknown absence never enter here.


def private_info(storage):
    if storage.private is not True:
        raise ValueError('Private dataset required')
    return storage.info()[0]


def commit_files(storage, files, parent, message, *, prefix=None):
    info, used = storage.budget_info()
    if info.sha != parent:
        raise ValueError('Private repository changed; retry with a new run')
    if used + sum(len(v) for v in files.values()) + 1_000_000 > storage.budget_bytes:
        raise ValueError('Private storage budget exceeded')
    if prefix:
        storage._immutable_prefix(prefix, parent)
    revision = storage._commit(files, parent, message)
    bounded_id(revision, 40)
    storage._verify_remote(files, revision)
    return revision, used


def prepare_recipient(storage, now=None):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    info = private_info(storage)
    now = now or datetime.now(timezone.utc)
    key_id = uuid.uuid4().hex
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM,
                                           serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    meta = {'schema':'un.owner-intake-key.v1', 'key_id':key_id,
            'created_at':now.isoformat(), 'expires_at':(now+timedelta(hours=24)).isoformat(),
            'public_key':public, 'private_sha256':sha(private)}
    prefix = 'owner-intake/keys/'+key_id+'/'
    revision, _ = commit_files(storage, {prefix+'private.pem':private, prefix+'metadata.json':encode(meta)},
                               info.sha, 'Prepare private owner-intake recipient', prefix=prefix)
    return {'schema':'un.owner-intake-recipient.v1', 'key_id':key_id, 'key_revision':revision,
            'public_key':public, 'expires_at':meta['expires_at'],
            'max_return_bytes':MAX_RETURN, 'part_chars':PART_CHARS, 'max_parts':MAX_PARTS}


def key_metadata(storage, key_id, revision, now=None, allow_expired=False):
    bounded_id(key_id, 32); bounded_id(revision, 40)
    meta = strict_json(storage.read('owner-intake/keys/'+key_id+'/metadata.json', revision, 16384))
    if (not isinstance(meta, dict) or set(meta) !=
            {'schema','key_id','created_at','expires_at','public_key','private_sha256'}
            or meta['schema'] != 'un.owner-intake-key.v1' or meta['key_id'] != key_id):
        raise ValueError('Invalid private recipient metadata')
    bounded_id(meta['private_sha256'], 64)
    public_key(meta['public_key'].encode())
    now = now or datetime.now(timezone.utc)
    created, expires = utc(meta['created_at']), utc(meta['expires_at'])
    if not timedelta(0) < expires-created <= timedelta(hours=24) or now < created:
        raise ValueError('Invalid recipient lifetime')
    if not allow_expired and now > expires:
        raise ValueError('Recipient expired')
    return meta


def make_dispatches(raw, recipient, now=None):
    fields = {'schema','key_id','key_revision','public_key','expires_at','max_return_bytes','part_chars','max_parts'}
    if (not isinstance(recipient, dict) or set(recipient) != fields or
            recipient['schema'] != 'un.owner-intake-recipient.v1' or
            type(recipient['max_return_bytes']) is not int or recipient['max_return_bytes'] != MAX_RETURN or
            type(recipient['part_chars']) is not int or recipient['part_chars'] != PART_CHARS or
            type(recipient['max_parts']) is not int or recipient['max_parts'] != MAX_PARTS):
        raise ValueError('Unsupported recipient contract')
    bounded_id(recipient['key_id'], 32); bounded_id(recipient['key_revision'], 40)
    if (now or datetime.now(timezone.utc)) > utc(recipient['expires_at']):
        raise ValueError('Recipient expired')
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_RETURN:
        raise ValueError('Returned review exceeds transfer bound')
    if not isinstance(strict_json(raw), dict):
        raise ValueError('Returned review must be a JSON object')
    cipher = encrypt_bundle(zlib.compress(raw, 9), recipient['public_key'].encode())
    if len(cipher) > MAX_CIPHER:
        raise ValueError('Encrypted review exceeds bounded multipart capacity')
    encoded = base64.b64encode(cipher).decode()
    parts = [encoded[i:i+PART_CHARS] for i in range(0, len(encoded), PART_CHARS)]
    if not 1 <= len(parts) <= MAX_PARTS:
        raise ValueError('Invalid part count')
    common = {k:recipient[k] for k in ('key_id','key_revision')}
    common.update(cipher_sha256=sha(cipher), part_count=str(len(parts)))
    dispatches = [{'ref':'main', 'inputs':{**common, 'action':'part', 'part_number':str(i+1),
                                          'ciphertext_part':part}} for i, part in enumerate(parts)]
    dispatches.append({'ref':'main', 'inputs':{**common, 'action':'finalize'}})
    return dispatches


def transfer_identity(key_id, revision, cipher_sha, count):
    bounded_id(key_id, 32); bounded_id(revision, 40); bounded_id(cipher_sha, 64)
    if type(count) is not int or not 1 <= count <= MAX_PARTS:
        raise ValueError('Invalid part count')
    return {'schema':'un.owner-intake-transfer.v1', 'key_id':key_id, 'key_revision':revision,
            'cipher_sha256':cipher_sha, 'part_count':count}


def receive_part(storage, key_id, revision, cipher_sha, count, number, data, now=None):
    transfer = transfer_identity(key_id, revision, cipher_sha, count)
    if (type(number) is not int or not 1 <= number <= count or not isinstance(data, str) or
            not 0 < len(data) <= PART_CHARS or len(data) % 4 or
            not re.fullmatch('[A-Za-z0-9+/]+={0,2}', data) or
            (number < count and (len(data) != PART_CHARS or '=' in data))):
        raise ValueError('Invalid encrypted part')
    info = private_info(storage)
    key_metadata(storage, key_id, revision, now)
    if optional(storage, 'owner-intake/keys/'+key_id+'/consumed.json', info.sha) is not None:
        raise ValueError('Recipient already consumed')
    prefix = 'owner-intake/transfers/'+key_id+'/'+cipher_sha+'/'
    path = prefix+str(number)+'.b64'
    manifest = encode(transfer)
    old_meta = optional(storage, prefix+'manifest.json', info.sha)
    if old_meta is not None and old_meta != manifest:
        raise ValueError('Transfer identity conflict')
    previous = optional(storage, path, info.sha, PART_CHARS)
    if previous is not None:
        if previous != data.encode() or old_meta is None:
            raise ValueError('Immutable encrypted part conflict')
        return {'schema':'un.owner-intake-receipt.v1','status':'verified_duplicate_part',
                'key_id':key_id,'part_number':number,'part_count':count}
    files = {path:data.encode()}
    if old_meta is None:
        files[prefix+'manifest.json'] = manifest
    commit_files(storage, files, info.sha, 'Store encrypted owner-intake part')
    return {'schema':'un.owner-intake-receipt.v1','status':'verified_encrypted_part',
            'key_id':key_id,'part_number':number,'part_count':count}


def original_inputs(storage):
    # Reuse the pinned, checksum-bound training-only allowlist, including registration metadata.
    with zipfile.ZipFile(io.BytesIO(training_zip(storage, include_registration=True))) as archive:
        prefix = '01_training/provenance/'
        draft = strict_json(archive.read(prefix+'original-training-draft.json'))
        registration = strict_json(archive.read(prefix+'registration.json'))
        reviewer = strict_json(archive.read(prefix+'reviewer-manifest.json'))
    return draft, registration, {k:reviewer[k] for k in IDENTITY}


def expand_return(compressed):
    reader = zlib.decompressobj()
    raw = reader.decompress(compressed, MAX_RETURN+1)
    if not 0 < len(raw) <= MAX_RETURN or not reader.eof or reader.unused_data or reader.unconsumed_tail:
        raise ValueError('Invalid or oversized compressed return')
    return raw


def clarifications(validated):
    return {'schema':'un.owner-intake-clarifications.v1','role':'assistant_provisional_qa',
            'owner_choices_changed':False,
            'flags':[{'pair_id':row['pair_id'],
                      'reason':'recorded_collective_but_national_attribution_confirmed',
                      'resolution':'owner_clarification_required'}
                     for row in validated['rows']
                     if row.get('capacity')=='collective' and row.get('national_attribution_valid') is True]}


def read_accepted(storage, raw_pointer, originals):
    pointer = strict_json(raw_pointer)
    if (not isinstance(pointer, dict) or set(pointer) != POINTER_FIELDS or
            pointer['schema'] != 'un.owner-intake-pointer.v1'):
        raise ValueError('Invalid private intake pointer')
    for name, width in (('revision',40),('manifest_sha256',64),('input_sha256',64),('cipher_sha256',64),('key_id',32)):
        bounded_id(pointer[name], width)
    prefix = pointer['prefix']
    if not isinstance(prefix, str) or not re.fullmatch(
            'owner-intake/submissions/'+pointer['input_sha256']+'/[0-9]{1,20}-[0-9]{1,6}/', prefix):
        raise ValueError('Invalid private intake prefix')
    manifest_raw = storage.read(prefix+'manifest.json', pointer['revision'], 16384)
    if sha(manifest_raw) != pointer['manifest_sha256']:
        raise ValueError('Private intake manifest mismatch')
    manifest = strict_json(manifest_raw)
    if (set(manifest) != {'schema','input_sha256','registration_sha256','code_revision','files'} or
            manifest['schema'] != 'un.private-owner-intake.v1' or
            manifest['input_sha256'] != pointer['input_sha256']):
        raise ValueError('Invalid private intake manifest')
    bounded_id(manifest['code_revision'], 40)
    draft, registration, identity = originals
    if manifest['registration_sha256'] != draft['registration_sha256']:
        raise ValueError('Stored review registration mismatch')
    entries = manifest['files']
    if (not isinstance(entries, list) or len(entries) != 3 or
            {e.get('path') for e in entries} != {'owner-return.json','validated-training.json','clarifications.json'}):
        raise ValueError('Unexpected private intake files')
    contents = {}
    for entry in entries:
        if set(entry) != {'path','bytes','sha256'} or type(entry['bytes']) is not int or not 0 < entry['bytes'] <= MAX_RETURN:
            raise ValueError('Invalid private intake file bound')
        bounded_id(entry['sha256'], 64)
        data = storage.read(prefix+entry['path'], pointer['revision'], entry['bytes'])
        if len(data) != entry['bytes'] or sha(data) != entry['sha256']:
            raise ValueError('Private intake file checksum mismatch')
        contents[entry['path']] = data
    if sha(contents['owner-return.json']) != pointer['input_sha256']:
        raise ValueError('Original returned bytes mismatch')
    returned, validated = (strict_json(contents[name]) for name in ('owner-return.json','validated-training.json'))
    if reconcile(draft, registration, returned, identity, previous=validated) != validated:
        raise ValueError('Stored review no longer reconciles')
    if strict_json(contents['clarifications.json']) != clarifications(validated):
        raise ValueError('Private clarification ledger mismatch')
    return pointer, validated


def result(pointer, validated, total, status):
    return {'schema':'un.owner-intake-receipt.v1', 'status':status,
            'key_id':pointer['key_id'], 'private_revision':pointer['revision'],
            'confirmed_examples':len(validated['rows']), 'total_examples':total,
            'clarification_count':len(clarifications(validated)['flags']),
            'original_bytes_preserved':True, 'remote_files_verified':True,
            'training_started':False, 'model_accepted':False}


def finalize(storage, key_id, revision, cipher_sha, count, run_id, code_revision, now=None):
    transfer = transfer_identity(key_id, revision, cipher_sha, count)
    if not isinstance(run_id, str) or not re.fullmatch('[0-9]{1,20}-[0-9]{1,6}', run_id):
        raise ValueError('Invalid run identity')
    bounded_id(code_revision, 40)
    info = private_info(storage)
    consumed_path = 'owner-intake/keys/'+key_id+'/consumed.json'
    consumed = optional(storage, consumed_path, info.sha)
    if consumed is not None:
        originals = original_inputs(storage)
        pointer, validated = read_accepted(storage, consumed, originals)
        if pointer['cipher_sha256'] != cipher_sha or pointer['key_id'] != key_id:
            raise ValueError('Recipient reused for another payload')
        return result(pointer, validated, len(originals[0]['rows']), 'verified_duplicate_intake')
    meta = key_metadata(storage, key_id, revision, now)
    prefix = 'owner-intake/transfers/'+key_id+'/'+cipher_sha+'/'
    if strict_json(storage.read(prefix+'manifest.json', info.sha, 16384)) != transfer:
        raise ValueError('Transfer manifest mismatch')
    encoded = ''.join(storage.read(prefix+str(i)+'.b64', info.sha, PART_CHARS).decode()
                      for i in range(1, count+1))
    cipher = base64.b64decode(encoded, validate=True)
    if not 0 < len(cipher) <= MAX_CIPHER or sha(cipher) != cipher_sha:
        raise ValueError('Encrypted transfer checksum mismatch')
    private = storage.read('owner-intake/keys/'+key_id+'/private.pem', revision, 8192)
    if sha(private) != meta['private_sha256']:
        raise ValueError('Private recipient checksum mismatch')
    raw = expand_return(decrypt_bundle(cipher, private))
    returned = strict_json(raw)
    originals = original_inputs(storage)
    draft, registration, identity = originals
    accepted_path = 'owner-intake/accepted/'+sha(raw)+'.json'
    already = optional(storage, accepted_path, info.sha)
    if already is not None:
        pointer, validated = read_accepted(storage, already, originals)
        if pointer['input_sha256'] != sha(raw):
            raise ValueError('Accepted input index mismatch')
        return result(pointer, validated, len(draft['rows']), 'verified_duplicate_intake')
    previous_raw = optional(storage, LATEST, info.sha)
    previous = read_accepted(storage, previous_raw, originals)[1] if previous_raw is not None else None
    validated = reconcile(draft, registration, returned, identity, previous=previous)
    merged = encode(validated)
    if len(merged) > MAX_RETURN:
        raise ValueError('Reconciled labels exceed private file bound')
    prefix = 'owner-intake/submissions/'+sha(raw)+'/'+run_id+'/'
    files = {'owner-return.json':raw, 'validated-training.json':merged,
             'clarifications.json':encode(clarifications(validated))}
    manifest = {'schema':'un.private-owner-intake.v1','input_sha256':sha(raw),
                'registration_sha256':draft['registration_sha256'],'code_revision':code_revision,
                'files':[{'path':name,'bytes':len(data),'sha256':sha(data)} for name,data in files.items()]}
    files['manifest.json'] = encode(manifest)
    remote = {prefix+name:data for name,data in files.items()}
    staged, _ = commit_files(storage, remote, info.sha, 'Stage validated private owner review', prefix=prefix)
    pointer = {'schema':'un.owner-intake-pointer.v1','prefix':prefix,'revision':staged,
               'manifest_sha256':sha(files['manifest.json']),'input_sha256':sha(raw),
               'cipher_sha256':cipher_sha,'key_id':key_id}
    pointer_raw = encode(pointer)
    read_accepted(storage, pointer_raw, originals)  # Independently reread and reconcile before activation.
    # One atomic commit activates only this review namespace, never warehouse latest.json.
    activated = storage._commit({LATEST:pointer_raw, accepted_path:pointer_raw, consumed_path:pointer_raw},
                                staged, 'Activate verified private owner review')
    storage._verify_remote({LATEST:pointer_raw, accepted_path:pointer_raw, consumed_path:pointer_raw}, activated)
    return result(pointer, validated, len(draft['rows']), 'verified_private_owner_intake')


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', choices=['pack'])
    parser.add_argument('--recipient', type=Path); parser.add_argument('--returned', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.mode == 'pack':
        if not args.recipient or not args.returned or not args.output:
            raise ValueError('Pack requires recipient, returned and output paths')
        if args.recipient.stat().st_size > 16384 or args.returned.stat().st_size > MAX_RETURN:
            raise ValueError('Local transfer input exceeds bound')
        dispatches = make_dispatches(args.returned.read_bytes(), strict_json(args.recipient.read_bytes()))
        args.output.mkdir(parents=True, exist_ok=False)
        for i, dispatch in enumerate(dispatches, 1):
            (args.output/(str(i)+'.json')).write_bytes(encode(dispatch))
        print(json.dumps({'status':'encrypted_dispatches_prepared','parts':len(dispatches)-1}))
        return
    action = os.environ.get('OWNER_INTAKE_ACTION')
    if action not in ('prepare','part','finalize'):
        raise ValueError('Unsupported intake action')
    storage = HFStorage(os.environ['HF_DATASET_REPO'])
    if action == 'prepare':
        receipt = prepare_recipient(storage)
    else:
        common = [os.environ['OWNER_KEY_ID'], os.environ['OWNER_KEY_REVISION'],
                  os.environ['OWNER_CIPHER_SHA256']]
        count = os.environ['OWNER_PART_COUNT']
        if not re.fullmatch('[1-8]', count):
            raise ValueError('Invalid part count')
        if action == 'part':
            number = os.environ['OWNER_PART_NUMBER']
            if not re.fullmatch('[1-8]', number):
                raise ValueError('Invalid part number')
            receipt = receive_part(storage, *common, int(count), int(number), os.environ['OWNER_CIPHERTEXT_PART'])
        else:
            receipt = finalize(storage, *common, int(count),
                               os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT'],
                               os.environ['GITHUB_SHA'])
    # This explicit return object is the only public artifact; no input/payload/key dump.
    (Path(os.environ['RUNNER_TEMP'])/'owner-intake-result.json').write_bytes(encode(receipt))
    print(json.dumps({'status':'recipient_prepared' if action=='prepare' else receipt['status']}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        safe = {'status':'failed','error_type':type(error).__name__}
        if isinstance(error, StorageRequestError):
            safe.update(operation=error.operation, http_status=error.status_code)
        print(json.dumps(safe))
        raise SystemExit(1)
