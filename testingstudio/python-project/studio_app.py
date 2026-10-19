"""Interface Python/Streamlit com Gemini no servidor, tema preto e três módulos."""

from __future__ import annotations

import hashlib
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis import ORIGINAL_SHA256, csv_bytes, read_source
from gemini_service import AuditError, run_gemini
from gemini_credentials import ensure_key_available
from project_guide import PROTOCOLS, REQUIREMENTS
from traceability_ui import render_traceability
from studio_sidebar import render_sidebar
from studio_engine import AnalysisError, CORRECTED_SAMPLE, analyze, report_markdown
from bibliography import MODULE_SOURCES, references_markdown
from bibliography_ui import render_references


def signature(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def source_preset():
    st.session_state["source_editor"] = (CORRECTED_SAMPLE if st.session_state["source_preset"] == "Exemplo corrigido (Python)"
                                          else st.session_state["original_source"])
    st.session_state.pop("gemini_audit", None)


def frame(rows, rename=None):
    data = pd.DataFrame(rows)
    if rename:
        data = data.rename(columns=rename)
    st.dataframe(data, hide_index=True, width="stretch")


def boundary_plot(result, zoom=False):
    lower, epsilon = float(result["lower"]), float(result["epsilon"])
    rows = result["boundaries"]
    if zoom:
        rows = [row for row in rows if abs(float(row["value"]) - lower) <= epsilon * 1.01]
    labels = [row["point"] + "<br>" + row["display"] for row in rows]
    if not zoom:
        labels = [labels[0], "", "Fronteira<br>ver ampliação", "", labels[-1]]
    fig = go.Figure(go.Scatter(x=[float(row["value"]) for row in rows], y=[1] * len(rows),
                              mode="markers+text", text=labels, textposition="top center",
                              customdata=[row["display"] for row in rows],
                              hovertemplate="Valor: %{customdata}<extra></extra>",
                              marker={"size": 16, "color": ["#16825d" if r["valid"] else "#c24b62" for r in rows]}))
    padding = epsilon * 1.7 if zoom else 135
    fig.add_vline(x=lower, line_dash="dash", line_color="#7081a0")
    fig.update_layout(template="none", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=260, margin={"l": 15, "r": 15, "t": 40, "b": 35},
                      xaxis={"range": [lower-padding, lower+padding], "title": "Valor de entrada"},
                      yaxis={"visible": False, "range": [0.7, 1.6]},
                      title="Fronteira ampliada" if zoom else "Domínio completo")
    return fig


def main():
    st.set_page_config(page_title="TestingStudio Web", page_icon="🧪", layout="wide")
    st.markdown('''<style>
    .stApp,[data-testid="stAppViewContainer"]{background:light-dark(#f7f9fc,#07090d);color:light-dark(#182f40,#edf2fb)}
    .block-container{max-width:1350px;padding-top:2rem}
    h1{letter-spacing:-1.2px}h2,h3{letter-spacing:-.4px}
    [data-testid="stMetric"]{background:light-dark(#ffffff,#10141c);border:1px solid light-dark(#d1dce5,#293247);border-radius:12px;padding:17px}
    [data-testid="stMetricValue"]{color:light-dark(#08734d,#79e3bb)}
    .studio-flow-graph{max-height:620px;overflow:auto;border:1px solid light-dark(#d1dce5,#293247);border-radius:10px}
    .studio-flow-graph svg{display:block;width:100%;min-width:650px;background:light-dark(#f8fafc,#0c1018)!important}
    .studio-flow-graph rect{fill:light-dark(#ffffff,#131c2a)}
    .studio-flow-graph g text{fill:light-dark(#243e52,#edf4ff)}
    .studio-flow-graph g text:first-of-type{fill:light-dark(#52697b,#9baaca)}
    .studio-flow-graph [stroke="#49d7b0"]{stroke:light-dark(#16825d,#49d7b0)}
    .studio-flow-graph [stroke="#ef9d6c"]{stroke:light-dark(#a85921,#ef9d6c)}
    textarea{font-family:Consolas,monospace!important}
    </style>''', unsafe_allow_html=True)
    try:
        original, _, _ = read_source()
    except (OSError, UnicodeError, ValueError) as exc:
        st.error(f"Não foi possível ler cad0001_item_calculo.txt: {exc}")
        st.stop()
    st.session_state["original_source"] = original
    if "source_editor" not in st.session_state:
        st.session_state["source_editor"] = original
    view, precision, lower, null_policy, oracle_mode, equivalents, api_key, model = render_sidebar()

    st.caption("WORKSPACE / " + view.upper())
    if view == "Fontes e referências":
        render_references()
        return
    if view in MODULE_SOURCES:
        st.caption("Fontes deste módulo: " + ", ".join(MODULE_SOURCES[view]) + ". Consulte Fontes e referências no menu.")
    if view == "Requisitos e RTM":
        render_traceability()
        return
    st.title("Código em análise. Evidências em mãos.")
    st.write("PCE e AVL, grafo de controle, Def-Uso e mutação no mesmo laboratório Python.")
    with st.expander("Unidade de código · editar ou carregar exemplo", expanded=False):
        st.selectbox("Exemplo de partida", ["CAD0001 original", "Exemplo corrigido (Python)"], key="source_preset", on_change=source_preset)
        source = st.text_area("Fonte da unidade", height=270, key="source_editor", max_chars=24000)
        extras = st.text_area("Casos adicionais em JSON (opcional)", key="extra_cases", height=85,
                               placeholder="[[2,3,4], [null,10,5]]")
        st.caption("Python: uma função numérica com atribuições, if/else e return. O adaptador reconhece a função de cálculo CAD0001. Imports, chamadas e loops são recusados.")
    try:
        custom = json.loads(extras) if extras.strip() else None
        payload = {"source": source, "precision": None if precision == "Automático" else int(precision),
                   "lower": lower, "null_policy": null_policy, "oracle_mode": oracle_mode,
                   "custom_cases": custom, "equivalent_ids": [v.strip() for v in equivalents.split(",") if v.strip()]}
        current_signature = signature(payload)
    except (ValueError, TypeError):
        payload, current_signature = None, None
        st.error("Confira o JSON dos casos adicionais. Use números ou null em uma lista de listas.")
    run_clicked = st.button("Analisar código em Python", type="primary", key="analyze")
    if payload and (run_clicked or "studio_result" not in st.session_state):
        try:
            with st.spinner("Construindo os três módulos..."):
                st.session_state["studio_result"] = analyze(**payload)
                st.session_state["analyzed_payload"] = payload
                st.session_state["analysis_signature"] = current_signature
                st.session_state.pop("gemini_audit", None)
        except (AnalysisError, ValueError, TypeError, ArithmeticError, RecursionError) as exc:
            st.error(str(exc))
    result = st.session_state.get("studio_result")
    if result is None:
        st.stop()
    fresh = current_signature == st.session_state.get("analysis_signature")
    if not fresh:
        st.warning("Entrada alterada: as evidências abaixo ainda pertencem à última análise. Clique em Analisar código em Python para atualizar.")
    st.caption(f"Função: {result['function']} · {result['language']} · SHA-256: {result['source_hash'][:20]}…")
    cols = st.columns(4)
    cols[0].metric("Casos de teste", len(result["cases"]))
    cols[1].metric("Complexidade V(G)", result["flow"]["vg"])
    cols[2].metric("Divergências", result["divergent"])
    cols[3].metric("Mutation Score", "N/D" if result["mutations"]["score"] is None else f"{result['mutations']['score']:.1f}%")
    st.divider()

    if view == "Visão geral":
        st.subheader("Três perspectivas. Uma auditoria.")
        cards = st.columns(3)
        for col, name, text in zip(cards, ["01 · Caixa-preta", "02 · Caixa-branca", "03 · Def-Uso e mutação"],
                                  ["Classes, fronteiras e épsilon calculado.", "Grafo e complexidade ciclomática de McCabe.", "Definições, usos, falhas injetadas e Mutation Score."]):
            with col:
                st.subheader(name)
                st.write(text)
        if result["divergent"]:
            st.warning(f"{result['divergent']} caso(s) divergem do oráculo. O CAD0001 original não valida negativos.")
        st.info("NULL: o manual apresenta regra contraditória. A hipótese escolhida fica registrada no relatório. Sobreviventes de mutação não são automaticamente equivalentes.")
        st.write("Use o menu para abrir um módulo. A execução é uma simulação controlada; não conecta ao Informix/Logix.")
    elif view == "Caixa-preta":
        classes, boundaries, cases = st.tabs(["Classes PCE", "Fronteiras AVL", "Casos de teste"])
        with classes:
            st.subheader("Particionamento em classes de equivalência")
            frame(result["pce"], {"parameter": "Parâmetro", "class": "Classe", "domain": "Domínio", "representative": "Representante"})
            st.info(f"Hipótese NULL: {result['null_policy']}. Oráculo aplicado: {result['oracle']}.")
        with boundaries:
            st.subheader("A fronteira exata")
            st.write(f"ε = 10^(−{result['precision']}) = **{result['epsilon']}**. A menor variação acompanha a precisão escolhida.")
            st.plotly_chart(boundary_plot(result), width="stretch")
            st.plotly_chart(boundary_plot(result, True), width="stretch")
            frame(result["boundaries"], {"point": "Ponto", "value": "Valor", "display": "Exibição", "valid": "Válido"})
        with cases:
            only = st.checkbox("Mostrar apenas divergências", key="only_divergent")
            rows = [r for r in result["cases"] if r["status"] not in {"Conforme", "Sem oráculo externo"}] if only else result["cases"]
            frame([{**{k:v for k,v in row.items() if k != "path"}, "inputs": "; ".join(row["inputs"])} for row in rows])
            st.download_button("Baixar casos (.csv)", csv_bytes([{k:v for k,v in r.items() if k != "path"} for r in result["cases"]]), "TestingStudio_Casos.csv", "text/csv")
            st.caption("Saídas produzidas pelo interpretador restrito. Para testar entradas extras, informe-as no editor e reexecute a análise.")
    elif view == "Caixa-branca":
        flow = result["flow"]
        st.subheader("Grafo de Fluxo de Controle")
        st.code(flow["formula"], language=None)
        st.caption(f"Conferência: predicados + 1 = {flow['predicate_check']}. {flow['convention']}")
        st.html('<div class="studio-flow-graph">' + result["graph_svg"] + '</div>')
        st.download_button("Baixar grafo (.svg)", result["graph_svg"].encode(), "TestingStudio_Grafo.svg", "image/svg+xml")
        with st.expander("Nós, definições e usos"):
            frame(flow["nodes"])
        with st.expander("Caminhos estruturais (não têm viabilidade provada)"):
            for index, path in enumerate(flow["paths"], 1):
                st.text(f"{index:02d}: " + " → ".join(path))
            if flow["paths_truncated"]:
                st.caption("Listagem limitada a 128 caminhos.")
        with st.expander("Unidade Python analisada"):
            st.code(result["translated_source"], language="python")
    elif view == "Def-Uso e mutação":
        mutation = result["mutations"]
        st.subheader("Mutation Score")
        st.code(mutation["formula"], language=None)
        st.caption(mutation["method"])
        st.info(f"{mutation['killed']} mortos · {mutation['survived']} sobreviventes · {mutation['equivalent']} equivalentes declarados. Casos excluídos por erro na referência: {mutation['excluded_baseline_cases']}.")
        frame([{k:v for k,v in row.items() if k != "source"} for row in mutation["mutants"]])
        if mutation["mutants"]:
            selected = st.selectbox("Revisar um mutante", [m["id"] for m in mutation["mutants"]], key="selected_mutant")
            mutant = next(m for m in mutation["mutants"] if m["id"] == selected)
            st.code(mutant["source"], language="python")
        st.subheader("Rastreamento Def-Uso")
        st.write(f"Pares cobertos pela suíte: **{result['def_use_covered']}/{result['def_use_total']}**.")
        frame(result["def_use"], {"variable": "Variável", "definition": "Definição", "use": "Uso", "type": "Tipo", "covered": "Coberto"})
        st.caption("p-use: predicado. c-use: cálculo ou retorno. Redefinições interrompem o alcance da definição anterior.")
    elif view == "Gemini":
        st.subheader("Uma segunda leitura do seu código")
        if "nl_requirements" not in st.session_state:
            st.session_state["nl_requirements"] = st.session_state.get("saved_requirements", "")
        nl = st.text_area("Requisitos em linguagem natural", height=130, key="nl_requirements", max_chars=12000,
                          placeholder="Ex.: Os parâmetros devem ser não negativos; explique PCE, fronteiras, McCabe e falhas da suíte.")
        st.session_state["saved_requirements"] = nl
        st.caption("Ao executar, o fonte, os requisitos e as evidências da última análise são enviados ao Google. A chave é usada pelo servidor.")
        gemini_signature = signature({"analysis": st.session_state["analysis_signature"], "requirements": nl})
        old = st.session_state.get("gemini_audit")
        if old and old["signature"] != gemini_signature:
            st.session_state.pop("gemini_audit", None)
        if st.button("Executar auditoria com Gemini", type="primary", key="run_gemini"):
            st.session_state.pop("gemini_audit", None)
            if not fresh:
                st.error("Atualize a análise Python antes de enviar o fonte ao Gemini.")
            else:
                try:
                    ensure_key_available(api_key)
                    with st.spinner("Gemini está revisando os três módulos..."):
                        response = run_gemini(api_key, model, st.session_state["analyzed_payload"]["source"], result["source_hash"],
                                              result["null_policy"], result["source_hash"] == ORIGINAL_SHA256,
                                              studio_result=result, nl_requirements=nl)
                        st.session_state["gemini_audit"] = {"text": response, "model": model, "signature": gemini_signature}
                except AuditError as exc:
                    st.error(str(exc))
        st.button("Limpar análise Gemini", key="clear_gemini", on_click=lambda: st.session_state.pop("gemini_audit", None))
        audit = st.session_state.get("gemini_audit")
        if audit:
            st.caption("Resposta recebida da API · Modelo solicitado: " + audit["model"])
            st.markdown(audit["text"])
        else:
            st.info("Abra Conexão Gemini na barra lateral: use a chave do app sem senha ou informe sua própria API Key. As métricas locais não são uma resposta do Gemini.")
    else:
        st.subheader("Do kickoff ao produto")
        frame(REQUIREMENTS, {"page": "Página do PDF", "requirement": "Requisito", "implementation": "Implementação"})
        st.subheader("Protocolos do laboratório")
        for protocol in PROTOCOLS:
            st.write("• " + protocol)
        st.info("GitHub Pages executa o motor Python no navegador. O app Streamlit hospedado mantém a integração Gemini no servidor. As duas versões compartilham o mesmo motor.")
        with st.expander("Limitações e método", expanded=True):
            for warning in result["warnings"]:
                st.write("• " + warning)

    report = report_markdown(result)
    if st.session_state.get("gemini_audit"):
        report += "\n## Revisão Gemini\n\n" + st.session_state["gemini_audit"]["text"]
    report += "\n\n" + references_markdown()
    st.divider()
    col1, col2 = st.columns(2)
    col1.download_button("Baixar relatório completo (.md)", report.encode(), "TestingStudio_Relatorio.md", "text/markdown", key="download_report")
    col2.download_button("Baixar auditoria (.json)", json.dumps(result, ensure_ascii=False, indent=2).encode(), "TestingStudio_Auditoria.json", "application/json", key="download_json")
    st.caption("TestingStudio Web · Python + Streamlit + Gemini · Fonte original preservado · Resultados exigem revisão humana")
