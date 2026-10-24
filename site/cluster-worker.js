'use strict';
importScripts('numerics.js', 'meeting-scopes.js?v=1.34.1', 'mds-core.js?v=1.12.1','gmm-core.js?v=1.12.1','cluster-options.js?v=1.12.1',
  'nmf-options.js?v=1.12.1', 'passage-selection.js?v=1.12.1', 'text-units.js?v=1.34.1', 'passage-labels.js?v=1.34.1', 'position-comparison.js?v=1.34.1', 'issue-workflow.js?v=1.34.1', 'analysis-core.js?v=1.34.1', 'lsa-core.js?v=1.12.1', 'representation-metrics.js?v=1.12.1',
  'cluster-algorithms.js?v=1.12.1', 'hdbscan-core.js?v=1.12.1', 'cluster-core.js?v=1.12.1', 'cluster-stability.js?v=1.12.1');
onmessage = async ({data}) => {
  try {
    const result = await UNClusters.run(data.records, data.vectors, data.options,
      async message => { postMessage({type:'progress', message}); });
    postMessage({type:'result', result});
  } catch(error) { postMessage({type:'error', message:error.message}); }
};
