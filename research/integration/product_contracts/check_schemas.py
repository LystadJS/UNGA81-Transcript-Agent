"""Independent standard-schema, canonical-hash and negative mutation checks.

Use generated synthetic metadata only. jsonschema is required: never skip it.
This validates shape, not upstream source authenticity or diplomatic findings.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator


def main(directory: str) -> None:
    root = Path(directory)
    lock = json.loads((root / 'interface-lock.json').read_text())
    for name, expected in lock['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('interface_hash_mismatch')
    schemas = {p.name.split('.')[0]: json.loads(p.read_text()) for p in root.glob('*.schema.json')}
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    cases = json.loads((root / 'examples.json').read_text())
    checks = 0
    for case in cases.values():
        for kind in ('query', 'capability', 'product'):
            validator = Draft202012Validator(schemas[kind])
            validator.validate(case[kind])
            checks += 1
            mutated = copy.deepcopy(case[kind])
            mutated['private_raw_transcript'] = 'C0_SYNTHETIC_PRIVATE_SENTINEL'
            if validator.is_valid(mutated):
                raise AssertionError('unknown_field_accepted')
            checks += 1
        for name in ('query', 'capability'):
            wire = json.dumps(case[name], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            if hashlib.sha256(wire.encode()).hexdigest() != case['product'][name + '_sha256']:
                raise AssertionError('cross_language_digest_mismatch')
            checks += 1
    product = cases['ready_candidate']['product']
    validator = Draft202012Validator(schemas['product'])
    for wrong in (True, -1, 0.5, 1000001, None, '2'):
        mutated = copy.deepcopy(product)
        mutated['fit_population']['eligible'] = wrong
        if validator.is_valid(mutated):
            raise AssertionError('invalid_integer_accepted')
        checks += 1
    # Reject extra fields at every actual object boundary, not only the root.
    def paths(value, prefix=()):
        if isinstance(value, dict):
            yield prefix
            for key, child in value.items():
                yield from paths(child, prefix + (key,))
        elif isinstance(value, list):
            for i, child in enumerate(value):
                yield from paths(child, prefix + (i,))
    for path in paths(product):
        mutated = copy.deepcopy(product)
        node = mutated
        for key in path:
            node = node[key]
        node['private_debug'] = 'SYNTHETIC_ONLY'
        if validator.is_valid(mutated):
            raise AssertionError('nested_unknown_field_accepted')
        checks += 1
    print(json.dumps({'independent_schema_checks': checks, 'failed': 0, 'skipped': 0,
                      'source_authentication': 'not_run', 'publication_eligible': False}))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python check_schemas.py GENERATED_DIRECTORY')
    main(sys.argv[1])
