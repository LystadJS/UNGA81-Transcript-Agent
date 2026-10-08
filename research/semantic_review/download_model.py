"""Acquire a fixed public encoder. This command accepts no transcript inputs."""
from __future__ import annotations
import argparse, json, urllib.request
from pathlib import Path
from encoder import REPOSITORY, REVISION, sha, verify_model


def download(destination: Path) -> None:
    lock = json.loads(Path(__file__).with_name('model-lock.json').read_text())
    if destination.exists():
        verify_model(destination, lock)
        print('Existing model matches all pinned hashes; no download needed')
        return
    destination.mkdir(parents=True)
    for name, item in lock['files'].items():
        url = f'https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}'
        if item['url'] != url:
            raise ValueError('Unexpected download location')
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read(item['bytes'] + 1)
        if len(data) != item['bytes'] or sha(data) != item['sha256']:
            raise ValueError('Downloaded bytes fail model lock: ' + name)
        with target.open('xb') as stream:
            stream.write(data)
    verify_model(destination, lock)
    print('Verified pinned model files; no transcript was accessed')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    download(parser.parse_args().destination)
