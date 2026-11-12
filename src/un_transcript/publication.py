"""Provision only the owner's dedicated public metadata dataset, never sources."""
import re
from .snapshots import HFStorage, RemoteEntryMissing, prepare_public_bundle

CARD = b'''# UN Transcript Agent public metadata

un-transcript-agent-public-metadata-v1

Source project: https://github.com/LystadJS/UNGA81-Transcript-Agent

This repository contains allowlisted meeting metadata, coverage, and source links.
Original transcripts, annotation packets, credentials, and unaccepted stance predictions
remain private. Topic retrieval is not stance. Follow latest.json for actual freshness;
a successful code deployment does not establish a fresh archive. Coverage can be partial.
No blanket redistribution license is asserted for UN sources or third-party material.
'''


def validate_target(private_repo, public_repo):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/UN-Transcript-Agent-Private', private_repo or ''):
        raise ValueError('Expected the configured private project dataset')
    if public_repo != private_repo.rsplit('/', 1)[0] + '/UN-Transcript-Agent-Public':
        raise ValueError('Only the same-owner dedicated public metadata dataset is permitted')


def provision_public(private_repo, public_repo, public_directory, *, api, storage_factory=HFStorage):
    validate_target(private_repo, public_repo)
    # Validate source/privacy contracts before creating even an empty public repo.
    manifest, files, expected_latest = prepare_public_bundle(public_directory)
    created = False
    try:
        info = api.repo_info(public_repo, repo_type='dataset')
    except Exception as error:
        if getattr(getattr(error, 'response', None), 'status_code', None) != 404:
            raise
        api.create_repo(repo_id=public_repo, repo_type='dataset', private=False, exist_ok=False)
        created = True
    else:
        if info.private is not False:
            raise ValueError('Refusing to change visibility of an existing private dataset')
    public = storage_factory(public_repo, private=False)
    info, _ = public.info()  # Recheck actual privacy and provider-accounted history.
    paths = api.list_repo_files(public_repo, repo_type='dataset', revision=info.sha)
    if set(paths) - {'.gitattributes'}:
        try:
            card = public.read('README.md', info.sha, 16_384)
        except RemoteEntryMissing:
            raise ValueError('Existing public repository lacks the project marker') from None
        if card != CARD:
            raise ValueError('Existing public repository has an unexpected project marker')
    else:
        api.upload_file(repo_id=public_repo, repo_type='dataset', path_in_repo='README.md',
                        path_or_fileobj=CARD, commit_message='Document source-free public metadata boundary')
    try:
        import json
        current = json.loads(public.read('latest.json', info.sha, 16*1024*1024))
    except RemoteEntryMissing:
        current = None
    if current == expected_latest:
        public._verify_remote(files, info.sha)
        latest = current
    else:
        latest = public.publish_public(public_directory)
    return {'schema': 'un.public-provision.v1', 'status': 'published', 'created': created,
            'public_repo': public_repo, 'snapshot_id': latest['snapshot_id'],
            'manifest_url': 'https://huggingface.co/datasets/' + public_repo + '/resolve/main/latest.json',
            'source_text_published': False, 'model_status': latest['model_status']}


def load_publication_config(path, private_repo, configured_repo=''):
    import json
    from pathlib import Path
    config = json.loads(Path(path).read_bytes())
    if not isinstance(config, dict) or set(config) != {'schema', 'public_repo', 'manifest_url'} or config['schema'] != 'un.publication.v1':
        raise ValueError('Invalid public publication configuration')
    repo = config['public_repo']
    validate_target(private_repo, repo)
    expected = 'https://huggingface.co/datasets/' + repo + '/resolve/main/latest.json'
    if config['manifest_url'] != expected:
        raise ValueError('Public manifest URL must match the configured repository')
    if configured_repo and configured_repo != repo:
        raise ValueError('HF_PUBLIC_DATASET_REPO conflicts with versioned public configuration')
    return config
