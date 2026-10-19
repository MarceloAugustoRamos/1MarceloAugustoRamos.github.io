/* A single runtime shared by code analysis and requirements traceability. */
"use strict";
(() => {
  let worker, active, sequence=0;
  function dispose(message){if(worker)worker.terminate();worker=null;if(active){clearTimeout(active.timer);active.reject(new Error(message));active=null;}}
  window.runStudioPython=(task,payload,progress=()=>{})=>new Promise((resolve,reject)=>{
    if(active){reject(new Error("Há uma análise Python em andamento. Aguarde sua conclusão."));return;}
    if(!worker){worker=new Worker("assets/engine-worker.js?v=3.0.0");worker.onmessage=event=>{const d=event.data;if(!active)return;if(d.type==="progress"){active.progress(d.message);return;}if(d.type!=="result"||d.id!==active.id)return;const request=active;active=null;clearTimeout(request.timer);if(d.ok)request.resolve(d.result);else request.reject(new Error(d.error||"Confira os dados da análise."));};worker.onerror=()=>dispose("Não foi possível carregar o Python. Confira o endereço HTTPS e o acesso ao CDN do Pyodide.");}
    const id=++sequence;active={id,resolve,reject,progress,timer:setTimeout(()=>dispose("A análise excedeu 90 segundos. Confira sua conexão e tente novamente."),90000)};
    worker.postMessage({id,task,payload});
  });
})();
