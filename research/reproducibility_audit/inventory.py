"""Metadata-only method and executable-test inventory from registered public files."""
from __future__ import annotations
import json
from pathlib import Path
from protocol import sha256

SUITES = [
 ('parallel interchange','docs/parallel-work/validate-contract.cjs','node docs/parallel-work/validate-contract.cjs','Node 22'),
 ('research registry','research/test_methods.py','python3 research/test_methods.py','Python 3'),
 ('research neural','research/test_neural.py','python3 -m unittest research/test_neural.py','Python 3; optional neural dependencies'),
 ('research R kernels','research/test_engines.R','Rscript research/test_engines.R','R + declared CRAN dependencies'),
 ('research extended R','research/test_more.R','Rscript research/test_more.R','R + declared CRAN dependencies'),
 ('source-aware validation','research/validation_framework','read upstream test entrypoint before execution','Node 22'),
 ('corpus contract','research/corpus','read upstream test entrypoint before execution','Node 22'),
 ('browser latent','site/latent-core.js','read applicable .github workflow for command','Node 22'),
 ('reproducibility self-test','research/reproducibility_audit/test_protocol.py',
  'python3 -m unittest discover -s research/reproducibility_audit -p "test_*.py" -v','Python 3 stdlib'),
]


def build(repo_root: Path, *, catalog: dict | None = None) -> dict:
    root=Path(repo_root)
    path=root/'research/catalog.json'
    if catalog is None:
        catalog=json.loads(path.read_text(encoding='utf-8'))
        catalog_digest=sha256(path.read_bytes())
    else:
        catalog_digest=sha256((json.dumps(catalog,sort_keys=True)+'\n').encode())
    if catalog.get('schema')!='un.i8.catalog.v1':
        raise ValueError('unknown method registry schema')
    methods=catalog.get('methods')
    if not isinstance(methods,list) or len({m['id'] for m in methods})!=len(methods):
        raise ValueError('missing/duplicate research methods')
    records=[]
    for m in methods:
        runner=m.get('runner')
        if runner not in (None,'run.R','neural.py'):
            raise ValueError('unknown registered runner')
        if m.get('publication_eligible') is not False or m.get('daily_adapter_integrated') is not False:
            raise ValueError('registry publication bypass')
        records.append({'method_id':m['id'],'name':m['method'],
           'registered_state':m['research_kernel'],
           'runner':None if runner is None else 'research/'+runner,
           'runtime':None if runner is None else ('R' if runner=='run.R' else 'Python'),
           'required_gates':m['required_gates'],
           'execution_evidence':'inherited declaration; not independently executed',
           'publication_eligible':False})
    suites=[{'suite':label,'file':file,'command':command,'runtime':runtime,
             'present':(root/file).exists(),
             'execution_evidence':'NOT RUN; inventory only'}
            for label,file,command,runtime in SUITES]
    return {'schema':'un.research-method-inventory.v1','source_schema':catalog['schema'],
            'source_path':'research/catalog.json','source_sha256':catalog_digest,
            'count_registered':len(records),
            'count_declared_kernels':sum(m['registered_state']=='synthetic_tested' for m in records),
            'methods':records,'test_entrypoints':suites,
            'note':'Registration and declared synthetic status are not re-execution or research release.'}
