/* Worker lifecycle: exactly one active task; terminate to cancel CPU-bound kernels. */
(function(root) {
  'use strict';
  class TaskController {
    constructor(workerURL, createWorker) {
      this.workerURL=workerURL;
      this.makeWorker=createWorker || (url=>new Worker(url));
      this.sequence=0;
      this.active=null;
    }
    start(action, fields={}, progress=()=>{}) {
      this.cancel();
      const id=++this.sequence;
      const worker=this.makeWorker(this.workerURL);
      return new Promise((resolve,reject)=>{
        const task={id,worker,reject};
        this.active=task;
        const finish=(callback,value)=>{
          if(this.active !== task)return;
          this.active=null;
          worker.terminate();
          callback(value);
        };
        worker.onerror=event=>finish(reject, new Error(event.message || 'Worker execution failed.'));
        worker.onmessage=event=>{
          const data=event.data || {};
          if(this.active !== task || data.id !== id)return;
          if(data.type==='progress')progress(data);
          else if(data.type==='result')finish(resolve,data);
          else if(data.type==='error')finish(reject,new Error(data.message || 'Worker error.'));
        };
        try { worker.postMessage({id,action,...fields}); }
        catch(error) { finish(reject,error); }
      });
    }
    cancel() {
      const task=this.active;
      if(!task)return false;
      this.active=null;
      task.worker.terminate();
      task.reject(new Error('Cancelled. No incomplete result was retained.'));
      return true;
    }
    get busy() { return Boolean(this.active); }
  }
  if (typeof module !== 'undefined' && module.exports) module.exports={TaskController};
  else root.UNMethodLabTasks={TaskController};
})(globalThis);
