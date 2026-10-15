/* Python runs in a worker; received user code goes only to the restricted AST interpreter. */
let pythonReady;
const CDN = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
async function initialize() {
  self.postMessage({type:"progress",message:"Carregando o motor Python… A primeira execução precisa de internet."});
  importScripts(CDN + "pyodide.js");
  const python = await loadPyodide({indexURL:CDN});
  const [analysis, engine] = await Promise.all([fetch("../analysis.py",{cache:"no-cache"}), fetch("../studio_engine.py",{cache:"no-cache"})]);
  if (!analysis.ok || !engine.ok) throw new Error("Não foi possível carregar os arquivos do motor Python.");
  python.FS.writeFile("/home/pyodide/analysis.py", await analysis.text());
  await python.runPythonAsync(await engine.text());
  self.postMessage({type:"ready"});
  return python;
}
self.onmessage = async event => {
  const {id,payload} = event.data;
  try {
    if (!pythonReady) pythonReady = initialize();
    const python = await pythonReady;
    python.globals.set("_browser_payload", JSON.stringify(payload));
    const response = await python.runPythonAsync("browser_analyze(_browser_payload)");
    self.postMessage({id,type:"result",...JSON.parse(response)});
  } catch(error) {
    self.postMessage({id,type:"result",ok:false,error:"O motor Python não pôde concluir a análise. Confira sua conexão e o acesso ao CDN do Pyodide. Detalhe: " + String(error.message).slice(0,180)});
    pythonReady = undefined;
  }
};
