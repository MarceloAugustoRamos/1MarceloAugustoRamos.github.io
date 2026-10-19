"use strict";
document.addEventListener("DOMContentLoaded",()=>{
  const $=id=>document.getElementById(id),sample=window.TESTING_STUDIO.traceability;
  let result=sample.result,source=sample.scenario,sourceKey=JSON.stringify(source),executions={},busy=false,dirty=false,provenance="Exemplo pré-calculado";
  const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  function table(target,headers,rows){const wrap=node("div",undefined,"table-wrap"),t=node("table"),head=node("thead"),h=node("tr"),body=node("tbody");headers.forEach(v=>h.append(node("th",v)));head.append(h);t.append(head);rows.forEach(row=>{const tr=node("tr");row.forEach(v=>tr.append(node("td",v)));body.append(tr);});if(!rows.length){const tr=node("tr"),td=node("td","Nenhum registro.");td.colSpan=headers.length;tr.append(td);body.append(tr);}t.append(body);wrap.append(t);$(target).replaceChildren(wrap);}
  function notice(text,error=false){$("rtm-notice").textContent=text;$("rtm-notice").className="microcopy"+(error?" rtm-error":"");}
  function download(name,value,type){const url=URL.createObjectURL(new Blob([value],{type})),a=node("a");a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function setDirty(){dirty=true;notice("Cenário editado. Os resultados exibidos pertencem à última derivação. Recalcule para atualizar; os registros anteriores serão reiniciados.");$("rtm-save-execution").disabled=true;}
  function loadExecution(){const c=result.cases.find(c=>c.id===$("rtm-execution-case").value);$("rtm-execution-status").value=c?.status||"Não executado";$("rtm-evidence").value=c?.evidence||"";}
  function render(){
    $("rtm-title").textContent=result.scenario.title;$("rtm-runtime").textContent=provenance;if(location.hash==="#traceability"){$("runtime-status").textContent=provenance;$("runtime-status").className="status-pill"+(provenance==="Python executado"?" ready":"");}
    const metrics=[["REQUISITOS",result.requirements.length,"Especificação do cenário"],["CASOS DERIVADOS",result.cases.length,"Um CT por fluxo explícito"],["COBERTURA RTM",result.coverage+"%","Requisitos com CT planejado"],["CTs EXECUTADOS",result.execution.executed+"/"+result.cases.length,"Resultados registrados manualmente"]];
    $("rtm-metrics").replaceChildren(...metrics.map(([label,value,foot])=>{const m=node("div",undefined,"metric");m.append(node("span",label,"metric-label"),node("strong",String(value),"metric-value mint"),node("span",foot,"metric-foot"));return m;}));
    table("rtm-requirements",["ID","Requisito"],result.requirements.map(r=>[r.id,r.description]));
    $("rtm-usecases").replaceChildren(...result.scenario.use_cases.map(uc=>{const p=node("section",undefined,"panel");p.append(node("span",uc.id,"eyebrow"),node("h3",uc.title),node("p","Ator: "+uc.actor,"microcopy"));const pre=node("ul");uc.preconditions.forEach(v=>pre.append(node("li",v)));p.append(pre);uc.flows.forEach(flow=>{const c=result.cases.find(c=>c.flow===flow.id),f=node("div",undefined,"rtm-flow");f.append(node("span",c.flow_type,"tag"),node("strong",flow.id+" · "+flow.title),node("p",c.id+" → "+(flow.requirements.join(" · ")||"Sem requisito"),"microcopy"));p.append(f);});return p;}));
    $("rtm-assumptions").replaceChildren(...result.scenario.assumptions.map(a=>node("li",a)));
    $("rtm-case-list").replaceChildren(...result.cases.map(c=>{const detail=node("details",undefined,"rtm-case"),summary=node("summary",c.id+" · "+c.title+" · "+c.status);detail.append(summary,node("p",c.use_case+" / "+c.flow+" · "+c.flow_type+" → "+(c.requirements.join(", ")||"SEM REQUISITO"),"rtm-link"),node("p","Ator: "+c.actor));detail.append(node("h4","Pré-condições"));const pre=node("ul");c.preconditions.forEach(v=>pre.append(node("li",v)));detail.append(pre,node("h4","Passos"));const steps=node("ol");c.steps.forEach(v=>steps.append(node("li",v)));detail.append(steps);if(c.data.length){detail.append(node("h4","Dados de teste"),node("pre",JSON.stringify(c.data,null,2)));}detail.append(node("h4","Resultado esperado"),node("p",c.expected),node("p","Evidência: "+(c.evidence||"Não informada."),"microcopy"));if(c.note)detail.append(node("p",c.note,"callout"));return detail;}));
    const old=$("rtm-execution-case").value;$("rtm-execution-case").replaceChildren(...result.cases.map(c=>{const o=node("option",c.id+" · "+c.title);o.value=c.id;return o;}));if(result.cases.some(c=>c.id===old))$("rtm-execution-case").value=old;loadExecution();
    $("rtm-execution-tag").textContent=result.execution.Aprovado+" aprovados · "+result.execution.Reprovado+" reprovados · "+result.execution.Bloqueado+" bloqueados";
    table("rtm-matrix-table",["Requisito",...result.cases.map(c=>c.id),"Planejado","Todos aprovados"],result.requirements.map(r=>[r.id,...result.cases.map(c=>c.requirements.includes(r.id)?"●":"—"),r.covered?"Sim":"Não",r.approved?"Sim":"Não"]));
    table("rtm-reverse-table",["Caso de teste","Caso de uso / fluxo","Requisitos","Situação"],result.cases.map(c=>[c.id,c.use_case+" / "+c.flow,c.requirements.join(", ")||"SEM REQUISITO",c.status]));
    $("rtm-gaps").textContent="Requisitos sem CT: "+(result.uncovered_requirements.join(", ")||"nenhum")+". CTs sem requisito: "+(result.orphan_tests.join(", ")||"nenhum")+".";$("rtm-method").textContent=result.method;
    $("rtm-save-execution").disabled=dirty||busy||!result.cases.length;
  }
  async function calculate(scenario,nextExecutions={},executionOnly=false){
    if(busy)return;busy=true;$("rtm-run").disabled=true;$("rtm-save-execution").disabled=true;$("rtm-editor").disabled=true;$("rtm-reset").disabled=true;$("rtm-file").disabled=true;
    const status=executionOnly?$("rtm-execution-notice"):$("rtm-notice");status.textContent="Processando no motor Python…";
    try{const data=await window.runStudioPython("rtm",{scenario,executions:nextExecutions},m=>{status.textContent=m;});result=data;source=scenario;sourceKey=JSON.stringify(scenario);executions=nextExecutions;dirty=false;provenance="Python executado";status.textContent=executionOnly?"Resultado manual registrado. Confira as evidências exportadas.":"CTs derivados e RTM recalculada em Python. Cobertura planejada não comprova execução.";render();}
    catch(e){status.textContent=e.message;status.classList.add("rtm-error");}
    finally{busy=false;$("rtm-run").disabled=false;$("rtm-save-execution").disabled=dirty||!result.cases.length;$("rtm-editor").disabled=false;$("rtm-reset").disabled=false;$("rtm-file").disabled=false;}
  }
  document.querySelectorAll("[data-rtm-tab]").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll("[data-rtm-tab]").forEach(x=>x.classList.toggle("active",x===b));document.querySelectorAll(".rtm-tab").forEach(x=>x.hidden=x.id!=="rtm-"+b.dataset.rtmTab);}));
  $("rtm-edit-toggle").addEventListener("click",()=>{const p=$("rtm-editor-panel");p.hidden=!p.hidden;$("rtm-edit-toggle").setAttribute("aria-expanded",String(!p.hidden));});
  $("rtm-editor").value=JSON.stringify(source,null,2);$("rtm-editor").addEventListener("input",setDirty);
  $("rtm-run").addEventListener("click",()=>{try{const scenario=JSON.parse($("rtm-editor").value);calculate(scenario,JSON.stringify(scenario)===sourceKey?executions:{});}catch{notice("JSON inválido. Confira aspas, vírgulas e listas no cenário.",true);}});
  $("rtm-reset").addEventListener("click",()=>{$("rtm-editor").value=JSON.stringify(sample.scenario,null,2);setDirty();});
  $("rtm-file").addEventListener("change",async e=>{const file=e.target.files[0];if(!file)return;if(file.size>360000){notice("Importe um projeto de até 360 KB.",true);return;}try{const data=JSON.parse(await file.text()),scenario=data.scenario||data;$("rtm-editor").value=JSON.stringify(scenario,null,2);setDirty();await calculate(scenario,data.executions||{});}catch{notice("Não foi possível importar. Use um cenário ou projeto RTM em JSON.",true);}finally{e.target.value="";}});
  $("rtm-execution-case").addEventListener("change",loadExecution);
  $("rtm-save-execution").addEventListener("click",()=>{if(dirty)return;const next={...executions,[$("rtm-execution-case").value]:{status:$("rtm-execution-status").value,evidence:$("rtm-evidence").value}};calculate(source,next,true);});
  $("rtm-export-report").addEventListener("click",()=>download("TestingStudio_RTM.md",result.report,"text/markdown;charset=utf-8"));
  $("rtm-export-csv").addEventListener("click",()=>download("TestingStudio_Matriz_RTM.csv",result.matrix_csv,"text/csv;charset=utf-8"));
  $("rtm-export-project").addEventListener("click",()=>download("TestingStudio_Projeto_RTM.json",JSON.stringify({schema_version:1,scenario:result.scenario,scenario_hash:result.scenario_hash,executions:Object.fromEntries(result.cases.map(c=>[c.id,{status:c.status,evidence:c.evidence}]))},null,2),"application/json"));
  render();
});
