'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{spawnSync}=require('node:child_process');
const Core=require('../site/meeting-report-core.js'),Package=require('../site/meeting-report-package.js'),F=require('./meeting_report_fixture.cjs');
(async()=>{
 const corpora=[await F.corpus(),await F.corpus(1)],report=Core.build(corpora,[F.meetings[0].slug],{mission:'Synthetic mission',notes:'Private fictional assessment 😀'});
 const bytes=await Package.build(report,corpora);assert.deepEqual(await Package.build(report,corpora),bytes);
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'un-package-test-')),file=path.join(directory,'report.zip');
 try{
  fs.writeFileSync(file,bytes);
  const check=spawnSync('python3',['-c',`
import hashlib,json,sys,zipfile
expected=json.load(sys.stdin)
with zipfile.ZipFile(sys.argv[1]) as z:
 assert z.namelist()==['report.html','report.json','evidence.csv','README.txt','manifest.json']
 assert z.testzip() is None
 assert all(i.compress_type==zipfile.ZIP_STORED and i.date_time==(1980,1,1,0,0,0) for i in z.infolist())
 m=json.loads(z.read('manifest.json'))
 assert m['schema']=='un.meeting-report-package.v1'
 assert m['model_status']=='withheld_not_accepted'
 assert m['generated_at']==expected['time'] and m['selected_segment_count']==4
 assert m['selected_meetings']==expected['selected'] and m['saved_source_scope']=='all_loaded_bundles'
 assert {x['path'] for x in m['files']}==set(z.namelist())-{'manifest.json'}
 for item in m['files']:
  data=z.read(item['path'])
  assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
 for name,value in expected['files'].items(): assert z.read(name)==value.encode('utf-8')
 saved=json.loads(z.read('report.json'))
 assert len(saved['corpora'])==2 and len(saved['selected_meetings'])==1
 assert len(m['source_revisions'])==len({(s['source_id'],s['sha256']) for c in saved['corpora'] for s in c['provenance']['sources']})
 assert 'fictional assessment' not in z.read('evidence.csv').decode()
 assert 'not encrypted' in z.read('README.txt').decode()
 print('PASS: independent ZIP/CRC/SHA-256/UTF-8 verification; exact exports and scoped manifest')
`,file],{input:JSON.stringify({time:report.generated_at,selected:report.selected_meetings,files:{'report.html':Core.standalone(report),'report.json':JSON.stringify(Core.savedReport(report,corpora)),'evidence.csv':Core.evidenceCSV(report.records)}}),encoding:'utf8'});
  assert.equal(check.status,0,check.stderr);process.stdout.write(check.stdout);
 }finally{fs.rmSync(directory,{recursive:true,force:true});}
 const limit=Core.LIMIT;
 try{
  Core.LIMIT=bytes.length;assert.equal((await Package.build(report,corpora)).length,bytes.length);
  Core.LIMIT=bytes.length-1;await assert.rejects(Package.build(report,corpora),/exceeds 25 MB/);
  Core.LIMIT=1;await assert.rejects(Package.build(report,corpora),/exceeds 25 MB/);
 }finally{Core.LIMIT=limit;}
 console.log('PASS: deterministic package, exact boundary and payload/container bounds; synthetic data only');
})().catch(e=>{console.error(e);process.exitCode=1;});
