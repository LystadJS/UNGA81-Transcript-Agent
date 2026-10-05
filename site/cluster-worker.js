'use strict';
importScripts('numerics.js', 'cluster-core.js');
onmessage = async ({data}) => {
  try {
    const result = await UNClusters.run(data.records, data.vectors, data.options,
      async message => { postMessage({type:'progress', message}); });
    postMessage({type:'result', result});
  } catch(error) { postMessage({type:'error', message:error.message}); }
};
