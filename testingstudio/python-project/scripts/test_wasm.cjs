const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {loadPyodide} = require('pyodide');
(async()=>{
  const root=path.resolve(__dirname,'..');
  const python=await loadPyodide();
  python.FS.writeFile('/home/pyodide/analysis.py',fs.readFileSync(path.join(root,'analysis.py'),'utf8'));
  await python.runPythonAsync(fs.readFileSync(path.join(root,'studio_engine.py'),'utf8'));
  const samples={original:fs.readFileSync(path.join(root,'cad0001_item_calculo.txt'),'utf8'),corrected:python.globals.get('CORRECTED_SAMPLE')};
  for(const [name,source] of Object.entries(samples)){
    python.globals.set('_test_request',JSON.stringify({source}));
    const data=JSON.parse(await python.runPythonAsync('browser_analyze(_test_request)'));
    assert.equal(data.ok,true);
    const result=data.result;
    assert.equal(result.cases.length,24);
    assert.equal(result.divergent,name==='original'?8:0);
    assert.equal(result.flow.vg,name==='original'?4:7);
    assert.equal(result.flow.vg,result.flow.E-result.flow.N+2);
    assert.ok(result.report.includes('Def-Uso'));
    console.log(JSON.stringify({runtime:'Pyodide 0.27.7',example:name,cases:result.cases.length,vg:result.flow.vg,divergent:result.divergent,mutants:result.mutations.generated}));
  }
  python.globals.set('_test_request',JSON.stringify({source:'def f(a):\n    return __import__("os").getcwd()'}));
  assert.equal(JSON.parse(await python.runPythonAsync('browser_analyze(_test_request)')).ok,false);
  console.log('WASM: resultados equivalentes ao Python nativo; fonte não permitido recusado.');
})().catch(error=>{console.error(error);process.exit(1);});
