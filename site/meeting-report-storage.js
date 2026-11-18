/* Explicit browser-profile report library. Atomic limits and revision checks; no network. */
(function(root){
  'use strict';
  const NAME='un-meeting-report',STORE='reports',LIMIT=25000000,MAX_REPORTS=8;
  const bytes=text=>new TextEncoder().encode(text).length;
  const validID=id=>typeof id==='string'&&/^[a-zA-Z0-9-]{1,80}$/.test(id);
  const summary=row=>({id:row.id,title:row.title,saved_at:row.saved_at,bytes:row.bytes,version:row.version});
  function entry(json,id,version,saved_at){
    let title='Unverified saved report';try{const value=JSON.parse(json);if(typeof value.settings?.title==='string'&&value.settings.title.trim())title=value.settings.title.slice(0,200);}catch{}
    return {id,json,title,bytes:bytes(json),version,saved_at};
  }
  function request(action,id='current',value,expected){
    return new Promise((resolve,reject)=>{
      if(!validID(id))return reject(Error('Invalid device report identifier.'));
      if(action==='write'&&(typeof value!=='string'||bytes(value)>LIMIT))return reject(Error('Use a saved report under 25 MB.'));
      let open,settled=false,reason;
      const fail=message=>{if(!settled){settled=true;reject(Error(message));}};
      try{if(!root.indexedDB)throw Error();open=root.indexedDB.open(NAME,2);}catch{fail('Device storage is unavailable. Download report JSON instead.');return;}
      open.onblocked=()=>fail('Device storage is blocked by another tab. Close it or download report JSON.');
      open.onerror=()=>fail(reason||'Could not open device storage. Download report JSON instead.');
      open.onupgradeneeded=()=>{
        const db=open.result,store=db.createObjectStore(STORE,{keyPath:'id'});
        // Copy the original single slot within the upgrade transaction, then remove
        // its duplicate store. A failed migration rolls back both changes.
        if(db.objectStoreNames.contains('draft')){
          const previous=open.transaction.objectStore('draft').get('current');
          previous.onsuccess=()=>{
            try{
            if(previous.result!==undefined){
              if(typeof previous.result!=='string'||bytes(previous.result)>LIMIT){reason='Earlier device data could not be upgraded within the library limits. It has been retained; open a downloaded JSON copy instead.';open.transaction.abort();return;}
              store.put(entry(previous.result,'current',1,null));
            }
            db.deleteObjectStore('draft');
            }catch{reason='The device library upgrade did not complete. Earlier data is unchanged; use a downloaded JSON copy or retry.';open.transaction.abort();}
          };
        }
      };
      open.onsuccess=()=>{
        const db=open.result;db.onversionchange=()=>db.close();if(settled){db.close();return;}
        let tx,result;
        try{
          tx=db.transaction(STORE,['write','remove'].includes(action)?'readwrite':'readonly');
          const store=tx.objectStore(STORE),op=['write','list'].includes(action)?store.getAll():store.get(id);
          op.onsuccess=()=>{
            try{
              const rows=['write','list'].includes(action)?op.result:null,row=rows?rows.find(r=>r.id===id):op.result;
              if(expected!==undefined&&expected!==(row?.version||0))throw Error('Saved report changed in another tab. Refresh the device library before trying again.');
              if(action==='write'){
                if(!row&&rows.length>=MAX_REPORTS)throw Error('The device library holds at most eight reports. Remove a copy or download JSON.');
                if(rows.some(r=>typeof r.json!=='string'))throw Error('The device library contains unsupported data. Download JSON instead.');
                if(bytes(value)+rows.filter(r=>r.id!==id).reduce((n,r)=>n+bytes(r.json),0)>LIMIT)throw Error('The device library exceeds 25 MB of report JSON. Remove a copy or download JSON.');
                const version=(row?.version||0)+1;if(!Number.isSafeInteger(version))throw Error('Unsupported saved report revision.');
                const next=entry(value,id,version,new Date().toISOString());store.put(next);result=summary(next);
              }else if(action==='remove'){store.delete(id);}
              else if(action==='list')result=rows.map(summary).sort((a,b)=>(b.saved_at||'').localeCompare(a.saved_at||'')||a.id.localeCompare(b.id));
              else if(action==='exists')result=!!row;
              else result=row?.json;
            }catch(e){reason=e.message;tx.abort();}
          };
          tx.oncomplete=()=>{db.close();if(!settled){settled=true;resolve(result);}};
          tx.onabort=()=>{db.close();fail(reason||'Device storage did not complete. Existing reports are unchanged; download JSON instead.');};
          tx.onerror=()=>{};
        }catch{db.close();fail('Device storage is unavailable. Download report JSON instead.');}
      };
    });
  }
  const api={LIMIT,MAX_REPORTS,list:()=>request('list'),exists:(id='current')=>request('exists',id),read:(id='current',expected)=>request('read',id,undefined,expected),remove:(id='current',expected=0)=>request('remove',id,undefined,expected),write:(value,id='current',expected=0)=>request('write',id,value,expected)};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNReportStorage=api;
})(globalThis);
