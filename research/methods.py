"""Check research accounting against executable IDs and the original D1 gates."""
import ast
import json
from pathlib import Path
import re


def inventory(root=None, catalog=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    catalog = catalog if catalog is not None else json.loads((root/'research/catalog.json').read_text(encoding='utf-8'))
    methods = catalog['methods']
    def ensure(value, message):
        if not value: raise ValueError(message)
    r_ids = set()
    for file, variable in [('engines.R', 'i6_ids'), ('engines_more.R', 'i7_ids')]:
        code = (root/'research'/file).read_text(encoding='utf-8')
        definition = re.search(r'\b'+variable+r'\s*<-\s*c\(([^)]+)\)', code).group(1)
        r_ids.update(re.findall(r"'(M\d{2})'", definition))
    tree = ast.parse((root/'research/neural.py').read_text(encoding='utf-8'))
    py_ids = set(next(ast.literal_eval(s.value) for s in tree.body if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'NEURAL_IDS' for t in s.targets)))
    adapters = (root/'un/R/09_method_registry.R').read_text(encoding='utf-8').split('d1_adapters <- function() list(', 1)[1].split('\n\n', 1)[0]
    daily_ids = set(re.findall(r'\b(M\d{2})\s*=\s*list\(', adapters))
    registry = json.loads((root/'un/design/D1/config/method_registry.json').read_text(encoding='utf-8'))['methods']
    original = {m['method_id']: m for m in registry}
    ensure(len({m['id'] for m in methods}) == len(methods), 'Duplicate catalog ID')
    ensure(not r_ids & py_ids, 'Duplicate engine ownership')
    ensure({m['id'] for m in methods} == set(original)-daily_ids, 'Research backlog differs from daily registry')
    for m in methods:
        ensure(m['required_gates'] == original[m['id']]['required_gates'].split('|'), 'Original publication prerequisites changed')
        ensure(m['daily_adapter_integrated'] is False and m['publication_eligible'] is False, 'Research catalog promotes publication')
        implemented = m['id'] in r_ids | py_ids
        ensure((m['research_kernel'] == 'synthetic_tested') == implemented, 'Catalog/engine implementation mismatch')
        if implemented:
            expected = 'neural.py' if m['id'] in py_ids else 'run.R'
            ensure(m['runner'] == expected, 'Wrong research runner')
    remaining = sorted(set(original)-daily_ids-r_ids-py_ids)
    ensure(catalog['daily_adapters'] == len(daily_ids) and catalog['synthetic_kernels'] == len(r_ids | py_ids) and catalog['remaining_kernels'] == len(remaining) and catalog['backlog_methods'] == len(methods), 'Catalog count mismatch')
    return {'registered': len(original), 'daily_adapters': len(daily_ids), 'r_research_kernels': len(r_ids),
            'python_research_kernels': len(py_ids), 'remaining': remaining, 'publication_change': False}


if __name__ == '__main__':
    print(json.dumps(inventory(), indent=2))
