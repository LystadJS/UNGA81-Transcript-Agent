"""Retain exact upstream license and model-card evidence with every candidate."""
from pathlib import Path
import re
from .contracts import digest

NAMES = {'LICENSE':'UPSTREAM_LICENSE', 'README.md':'UPSTREAM_MODEL_CARD.md', 'NOTICE':'UPSTREAM_NOTICE'}


def load_upstream_notices(base, revision):
    if not isinstance(revision,str) or not re.fullmatch(r'[a-f0-9]{40}',revision):
        raise ValueError('Notices require an immutable upstream revision')
    base=Path(base);files={}
    for source,target in NAMES.items():
        path=base/source
        if source=='NOTICE' and not path.exists():continue
        if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=1024*1024:
            raise ValueError('Missing, unsafe or oversized upstream notice')
        files[target]=path.read_bytes()
    card=files['UPSTREAM_MODEL_CARD.md'].decode('utf-8')
    front=re.match(r'\A---\s*\n(.*?)\n---(?:\s|$)',card,re.S)
    license_match=re.search(r'^license:\s*([a-z0-9][a-z0-9.-]{0,63})\s*$',front.group(1),re.M) if front else None
    if not license_match:
        raise ValueError('Upstream model card has no unambiguous license identifier')
    record={'declared_license':license_match.group(1),
            'upstream_revision':revision,
            'upstream_model':'distilbert/distilbert-base-uncased',
            'source_url':'https://huggingface.co/distilbert/distilbert-base-uncased/tree/'+revision,
            'notice_sha256':{name:digest(data) for name,data in files.items()},
            'scope':'Upstream model notices only; no UN transcript or annotation redistribution license is implied.'}
    return record,files


def preserve_upstream_notices(output, files):
    root=Path(output)
    for name,data in files.items():
        if name not in NAMES.values():raise ValueError('Unknown upstream notice filename')
        path=root/name
        if path.is_symlink():raise ValueError('Unsafe upstream notice destination')
        if path.exists():
            if not path.is_file() or path.read_bytes()!=data:
                raise ValueError('Existing candidate notice differs from pinned upstream source')
        else:
            with path.open('xb') as stream:stream.write(data)
