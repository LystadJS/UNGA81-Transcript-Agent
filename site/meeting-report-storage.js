/* One explicitly saved report in this browser profile; no network or dependencies. */
(function(root){
  'use strict';
  const NAME='un-meeting-report',STORE='draft',KEY='current',LIMIT=25000000;
  function request(action,value){
    return new Promise((resolve,reject)=>{
      if(!root.indexedDB)return reject(Error('Device storage is unavailable. Download report JSON instead.'));
      let open,settled=false;
      const fail=message=>{if(!settled){settled=true;reject(Error(message));}};
      try{open=root.indexedDB.open(NAME,1);}catch{fail('Device storage is unavailable. Download report JSON instead.');return;}
      open.onblocked=()=>fail('Device storage is blocked by another tab. Close it or download report JSON.');
      open.onerror=()=>fail('Could not open device storage. Download report JSON instead.');
      open.onupgradeneeded=()=>{if(!open.result.objectStoreNames.contains(STORE))open.result.createObjectStore(STORE);};
      open.onsuccess=()=>{
        const db=open.result;db.onversionchange=()=>db.close();
        if(settled){db.close();return;}
        let tx,result;
        try{
          tx=db.transaction(STORE,action==='write'||action==='remove'?'readwrite':'readonly');
          const store=tx.objectStore(STORE),op=action==='write'?store.put(value,KEY):action==='remove'?store.delete(KEY):action==='exists'?store.count(KEY):store.get(KEY);
          op.onsuccess=()=>{result=op.result;};
          tx.oncomplete=()=>{db.close();if(!settled){settled=true;resolve(result);}};
          tx.onabort=()=>{db.close();fail('Device storage did not complete. The previous saved report is unchanged; download JSON instead.');};
          tx.onerror=()=>{}; // Abort is the final transaction outcome.
        }catch{db.close();fail('Device storage is unavailable. Download report JSON instead.');}
      };
    });
  }
  const api={exists:()=>request('exists').then(Boolean),read:()=>request('read'),remove:()=>request('remove'),write:value=>{
    if(typeof value!=='string'||new TextEncoder().encode(value).length>LIMIT)return Promise.reject(Error('Use a saved report under 25 MB.'));
    return request('write',value);
  }};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNReportStorage=api;
})(globalThis);
