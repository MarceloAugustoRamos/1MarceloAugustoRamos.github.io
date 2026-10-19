"""Interface Streamlit para a Sprint de requisitos, casos de uso e RTM."""
import json

import pandas as pd
import streamlit as st

from traceability import LIBRARY_SCENARIO, STATUSES, TraceabilityError, analyze_traceability
from bibliography import references_markdown


def render_traceability():
    st.title("Requisitos conectados. Testes com propósito.")
    st.write("Nova Sprint · Derivação de casos de teste e rastreabilidade bidirecional · Aula de 14/10/2026")
    if "rtm_source" not in st.session_state:
        st.session_state["rtm_source"] = json.dumps(LIBRARY_SCENARIO, ensure_ascii=False, indent=2)
    with st.expander("Editar cenário estruturado ou importar projeto"):
        upload = st.file_uploader("Projeto RTM (.json)", type=["json"], key="rtm_upload")
        if st.button("Carregar arquivo selecionado", key="rtm_import", disabled=upload is None):
            try:
                if upload.size > 360000:
                    raise TraceabilityError("Importe um projeto de até 360 KB.")
                data = json.loads(upload.getvalue())
                scenario = data.get("scenario", data)
                imported = analyze_traceability(scenario, data.get("executions"))
                if data.get("executions") and data.get("scenario_hash") != imported["scenario_hash"]:
                    raise TraceabilityError("Os registros de execução pertencem a outro cenário ou não possuem sua identificação. Importe o cenário sem registros para iniciar nova rodada.")
                st.session_state["rtm_source"] = json.dumps(scenario, ensure_ascii=False, indent=2)
                st.session_state["rtm_result"] = imported
                st.session_state["rtm_input"] = st.session_state["rtm_source"]
            except (ValueError, TypeError, AttributeError, KeyError) as exc:
                st.error(f"Não foi possível importar: {exc}")
        if st.button("Carregar biblioteca", key="rtm_reset"):
            st.session_state["rtm_source"] = json.dumps(LIBRARY_SCENARIO, ensure_ascii=False, indent=2)
        source = st.text_area("Cenário em JSON", key="rtm_source", height=400, max_chars=180000)
        st.caption("Edite title, requirements e use_cases. Fluxos: principal, alternativo ou excecao; informe requirements, steps e expected. Um CT é derivado por fluxo explícito. Não há interpretação automática de texto livre.")
    derive = st.button("Derivar CTs e RTM em Python", type="primary", key="rtm_derive")
    if derive or "rtm_result" not in st.session_state:
        try:
            # Uma alteração do cenário exige uma nova rodada de execução.
            old = st.session_state.get("rtm_result", {})
            executions = ({c["id"]: {"status": c["status"], "evidence": c["evidence"]} for c in old.get("cases", [])}
                          if st.session_state.get("rtm_input") == source else {})
            st.session_state["rtm_result"] = analyze_traceability(json.loads(source), executions)
            st.session_state["rtm_input"] = source
        except (ValueError, TypeError, KeyError, RecursionError) as exc:
            st.error(f"Confira o cenário: {exc}")
    result = st.session_state.get("rtm_result")
    if not result:
        return
    fresh = st.session_state.get("rtm_input") == source
    if not fresh:
        st.warning("Cenário editado: os resultados exibidos pertencem à última derivação. Recalcule para atualizar; os registros anteriores serão reiniciados.")
    st.subheader(result["scenario"]["title"])
    cols = st.columns(4)
    for col,label,value in zip(cols,["Requisitos", "Casos derivados", "Cobertura RTM", "CTs executados"],
                               [len(result["requirements"]), len(result["cases"]), f"{result['coverage']}%", f"{result['execution']['executed']}/{len(result['cases'])}"]):
        col.metric(label, value)
    st.caption("Motor Python executado · Cobertura RTM = planejamento; execução = resultados manuais informados.")
    scenario_tab,cases_tab,matrix_tab = st.tabs(["Requisitos e fluxos", "Casos derivados", "Matriz RTM"])
    with scenario_tab:
        st.dataframe(pd.DataFrame(result["scenario"]["requirements"]).rename(columns={"id": "ID", "description": "Requisito"}), hide_index=True, width="stretch")
        st.info("Principal: sucesso esperado. Alternativo: variação aceitável ou limite. Exceção: bloqueio que protege a operação.")
        for uc in result["scenario"]["use_cases"]:
            with st.expander(uc["id"] + " · " + uc["title"], expanded=True):
                st.write("Ator: " + uc["actor"])
                st.write("Pré-condições: " + "; ".join(uc["preconditions"]))
                for f in uc["flows"]:
                    c = next(c for c in result["cases"] if c["flow"] == f["id"])
                    st.write(f"**{f['id']} · {c['flow_type']} · {f['title']}**")
                    st.caption(c["id"] + " → " + (", ".join(c["requirements"]) or "SEM REQUISITO"))
        with st.expander("Premissas e pontos a refinar", expanded=True):
            for text in result["scenario"]["assumptions"]:
                st.write("• " + text)
    with cases_tab:
        st.caption("CT01, CT02 e CT03 seguem o rastreio da aula. CT04 e CT05 são extensões propostas no exemplo.")
        for c in result["cases"]:
            with st.expander(f"{c['id']} · {c['title']} · {c['status']}"):
                st.write(f"Rastreio: {c['use_case']} / {c['flow']} · {c['flow_type']} → {', '.join(c['requirements']) or 'SEM REQUISITO'}")
                st.write("Ator: " + c["actor"])
                st.write("Pré-condições: " + "; ".join(c["preconditions"]))
                for i,step in enumerate(c["steps"],1):
                    st.write(f"{i}. {step}")
                if c["data"]:
                    st.dataframe(pd.DataFrame(c["data"]), hide_index=True, width="stretch")
                st.write("**Esperado:** " + c["expected"])
                st.write("Evidência: " + (c["evidence"] or "Não informada."))
                if c["note"]:
                    st.info(c["note"])
        st.subheader("Registrar uma execução manual")
        st.caption("Execute o caso no sistema sob teste e descreva a evidência. Este laboratório não executa uma biblioteca nem envia e-mails.")
        if result["cases"]:
            selected = st.selectbox("Caso de teste", [c["id"] for c in result["cases"]], key="rtm_selected")
            c = next(c for c in result["cases"] if c["id"] == selected)
            context = result["scenario_hash"][:16] + selected
            with st.form("rtm_execution_form"):
                status = st.selectbox("Situação", STATUSES, index=STATUSES.index(c["status"]), key="rtm_status_" + context)
                evidence = st.text_area("Evidência / resultado observado / justificativa", c["evidence"], max_chars=6000, key="rtm_evidence_" + context)
                if st.form_submit_button("Salvar resultado em Python", disabled=not fresh):
                    try:
                        executions = {row["id"]: {"status": row["status"], "evidence": row["evidence"]} for row in result["cases"]}
                        executions[selected] = {"status": status, "evidence": evidence}
                        st.session_state["rtm_result"] = analyze_traceability(result["scenario"], executions)
                        st.rerun()
                    except TraceabilityError as exc:
                        st.error(str(exc))
    with matrix_tab:
        rows = []
        for r in result["requirements"]:
            rows.append({"Requisito": r["id"], **{c["id"]: "X" if r["id"] in c["requirements"] else "—" for c in result["cases"]},
                         "Planejado": "Sim" if r["covered"] else "Não", "Todos aprovados": "Sim" if r["approved"] else "Não"})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.subheader("CT → requisito")
        st.dataframe(pd.DataFrame([{ "CT": c["id"], "Caso de uso": c["use_case"], "Fluxo": c["flow"], "Requisitos": ", ".join(c["requirements"]) or "SEM REQUISITO", "Situação": c["status"]} for c in result["cases"]]), hide_index=True, width="stretch")
        st.write("Requisitos sem CT: " + (", ".join(result["uncovered_requirements"]) or "Nenhum"))
        st.write("CTs sem requisito: " + (", ".join(result["orphan_tests"]) or "Nenhum"))
        st.info(result["method"])
    st.divider()
    st.caption("Exporte para guardar cenário e registros; os dados ficam na sessão até a exportação.")
    cols = st.columns(3)
    cols[0].download_button("Relatório RTM (.md)", (result["report"] + "\n\n" + references_markdown()).encode(), "TestingStudio_RTM.md", "text/markdown")
    cols[1].download_button("Matriz RTM (.csv)", result["matrix_csv"].encode(), "TestingStudio_Matriz_RTM.csv", "text/csv")
    project = {"schema_version": 1, "scenario": result["scenario"], "scenario_hash": result["scenario_hash"],
               "executions": {c["id"]: {"status": c["status"], "evidence": c["evidence"]} for c in result["cases"]}}
    cols[2].download_button("Projeto RTM (.json)", json.dumps(project, ensure_ascii=False, indent=2).encode(), "TestingStudio_Projeto_RTM.json", "application/json")
