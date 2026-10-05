'use strict';
importScripts('numerics.js', 'meeting-scopes.js?v=1.2.0', 'cluster-options.js?v=1.5.0',
  'analysis-core.js?v=1.5.0', 'lsa-core.js?v=1.5.0', 'representation-metrics.js?v=1.5.0',
  'cluster-core.js?v=1.5.0', 'cluster-stability.js?v=1.5.0');
onmessage = async ({data}) => {
  try {
    const result = await UNClusters.run(data.records, data.vectors, data.options,
      async message => { postMessage({type:'progress', message}); });
    postMessage({type:'result', result});
  } catch(error) { postMessage({type:'error', message:error.message}); }
};
