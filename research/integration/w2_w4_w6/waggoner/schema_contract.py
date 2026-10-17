"""Dependency-free validator for this closed schema's explicitly supported subset.

Not a general JSON Schema engine. Unknown validation keywords fail closed.
Cross-check the contract with the independent jsonschema implementation in tests.
"""
import json
import math
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

class SchemaError(ValueError):
    pass

@lru_cache(maxsize=1)
def contract():
    return json.loads((Path(__file__).with_name('schema')/'us_relative.schema.json').read_text())


def validate(value, source=False):
    root=contract()
    known={'$schema','$id','title','description','$defs','$ref','type','const','enum','anyOf','allOf',
        'if','then','else','required','properties','additionalProperties','propertyNames','maxProperties',
        'items','minItems','maxItems','uniqueItems','pattern','format','maxLength','minimum','maximum','exclusiveMinimum'}
    def equal(a,b):
        # JSON booleans are not the integers 0 and 1.
        return type(a) is type(b) and a==b or type(a) in (int,float) and type(b) in (int,float) and a==b
    def check(v,s):
        if s is True:return
        if s is False:raise SchemaError('Forbidden field')
        if not isinstance(s,dict) or set(s)-known:raise SchemaError('Unsupported schema keyword')
        if '$ref' in s:
            if not s['$ref'].startswith('#/$defs/'):raise SchemaError('External schema forbidden')
            check(v,root['$defs'][s['$ref'].split('/')[-1]])
        typ=s.get('type')
        types={'null':v is None,'boolean':type(v) is bool,'number':type(v) in (int,float) and math.isfinite(v),
            'integer':type(v) in (int,float) and math.isfinite(v) and float(v).is_integer(),
            'string':type(v) is str,'array':type(v) is list,'object':type(v) is dict}
        if typ and not types.get(typ,False):raise SchemaError('Wrong JSON type')
        if 'const' in s and not equal(v,s['const']):raise SchemaError('Constant mismatch')
        if 'enum' in s and not any(equal(v,x) for x in s['enum']):raise SchemaError('Enum mismatch')
        def accepts(schema):
            try:check(v,schema);return True
            except SchemaError:return False
        if 'anyOf' in s and not any(accepts(x) for x in s['anyOf']):raise SchemaError('No admissible variant')
        for x in s.get('allOf',[]):check(v,x)
        if 'if' in s:check(v,s.get('then' if accepts(s['if']) else 'else',{}))
        if type(v) is dict:
            if not all(type(k) is str for k in v):raise SchemaError('Non-string property')
            if set(s.get('required',[]))-set(v):raise SchemaError('Missing fields')
            if len(v)>s.get('maxProperties',len(v)):raise SchemaError('Object resource bound')
            for k,x in v.items():
                if 'propertyNames' in s:check(k,s['propertyNames'])
                if k in s.get('properties',{}):check(x,s['properties'][k])
                elif 'additionalProperties' in s:check(x,s['additionalProperties'])
        if type(v) is list:
            if not s.get('minItems',0)<=len(v)<=s.get('maxItems',len(v)):raise SchemaError('Array resource bound')
            if s.get('uniqueItems'):
                keys=[json.dumps(x,sort_keys=True,allow_nan=False) for x in v]
                if len(set(keys))!=len(keys):raise SchemaError('Duplicate array items')
            if 'items' in s:
                for x in v:check(x,s['items'])
        if type(v) is str:
            if len(v)>s.get('maxLength',len(v)):raise SchemaError('String resource bound')
            if 'pattern' in s and not re.search(s['pattern'],v):raise SchemaError('String pattern')
            if s.get('format')=='date':
                try:date.fromisoformat(v)
                except ValueError as e:raise SchemaError('Invalid date') from e
        if type(v) in (int,float):
            if not math.isfinite(v):raise SchemaError('Nonfinite JSON number')
            if v<s.get('minimum',v) or v>s.get('maximum',v):raise SchemaError('Number range')
            if 'exclusiveMinimum' in s and v<=s['exclusiveMinimum']:raise SchemaError('Number boundary')
    check(value,root['$defs']['source'] if source else root)
    return True
