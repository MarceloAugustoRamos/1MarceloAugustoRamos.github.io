"""Executar: python -m streamlit run app.py"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from analysis import (NULL_POLICIES, boundary_rows, build_report, case_rows, csv_bytes,
                      expected_value, format_decimal, parse_input, pce_rows,
                      read_source, simulate_original)
from charts import boundary_chart
from gemini_service import DEFAULT_MODEL, AuditError, run_gemini

st.set_page_config(page_title="TestingStudio | Sprint 1", page_icon="🧪", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1280px; padding-top: 2rem;}
h1 {letter-spacing: -1px;}
[data-testid="stMetric"] {background: #f0f5fb; border: 1px solid #e1e8f1; border-radius: 12px; padding: 15px;}
[data-testid="stMetricValue"] {color: #142f50;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🧪 TestingStudio")
    st.caption("SPRINT 1 · AUDITORIA DE CAIXA-PRETA")
    st.divider()
    st.subheader("Google AI Studio")
    api_key = st.text_input("Gemini API Key", type="password", key="api_key",
                            help="A chave fica nesta sessão; não é incluída nos relatórios.")
    st.link_button("Obter chave no AI Studio", "https://aistudio.google.com/apikey")
    model = st.text_input("Modelo Gemini", value=os.getenv("GEMINI_MODEL", DEFAULT_MODEL), key="model")
    st.caption("Use um modelo habilitado na sua conta. O nome pode ser alterado aqui.")
    with st.expander("Hipótese para valores nulos"):
        null_policy = st.selectbox("Tratamento de NULL no oráculo", options=list(NULL_POLICIES),
                                   format_func=lambda value: NULL_POLICIES[value], key="null_policy")
        st.caption("O manual é contraditório. A hipótese padrão segue seu exemplo de função: NULL → 0.")
    st.divider()
    st.caption("Teste de Software I · 62371\n\nProf. Frank Piffer · 2026.2")

st.caption("LABORATÓRIO / CAD0001")
st.title("Auditoria de Caixa-Preta")
st.write("Classes de equivalência, valores limite e comparação da regra de cálculo do CAD0001.")

try:
    source, digest, original = read_source()
except (OSError, UnicodeError, ValueError) as exc:
    st.error(f"Não foi possível ler cad0001_item_calculo.txt: {exc}")
    st.info("Mantenha o arquivo original ao lado de app.py e execute novamente.")
    st.stop()

signature = (digest, null_policy)
audit = st.session_state.get("gemini_audit")
if audit and audit["signature"] != signature:
    del st.session_state["gemini_audit"]
    audit = None

cases = case_rows(null_policy, original)
divergent = sum(row["Comparação"] == "Divergente" for row in cases)
cols = st.columns(4)
for col, label, value in zip(cols, ["Parâmetros", "Casos planejados", "Épsilon", "Divergências simuladas"],
                             ["3", str(len(cases)), "R$ 0,01", str(divergent) if original else "N/D"]):
    col.metric(label, value)

if original:
    st.warning("O TXT original não rejeita negativos. O manual exige retorno -1; a auditoria registra essa divergência.")
else:
    st.warning("O fonte foi alterado. As tabelas mostram o oráculo do manual; a simulação do TXT original está desativada. Refaça a inspeção com Gemini.")

with st.expander("Fonte CAD0001 · arquivo real lido do disco", expanded=True):
    st.text_area("cad0001_item_calculo.txt", value=source, height=210, disabled=True, key=f"source_{digest}")
    st.caption(f"SHA-256: {digest}")

left, right = st.columns([2, 1])
run_clicked = left.button("Executar auditoria com Gemini", type="primary", width="stretch", key="run_gemini")
right.button("Limpar análise Gemini", width="stretch", key="clear_gemini",
             on_click=lambda: st.session_state.pop("gemini_audit", None))
st.caption("As tabelas locais já estão disponíveis. A chamada ao Gemini envia o fonte e a análise de referência ao Google.")
if run_clicked:
    if not api_key.strip():
        st.error("Insira sua Gemini API Key na barra lateral para executar a integração exigida pelo manual.")
    elif not model.strip():
        st.error("Informe o nome do modelo Gemini na barra lateral.")
    else:
        # Uma falha na nova solicitação não deve deixar uma análise antiga parecendo atual.
        st.session_state.pop("gemini_audit", None)
        with st.spinner("Gemini está analisando PCE e AVL..."):
            try:
                text = run_gemini(api_key, model, source, digest, null_policy, original)
                st.session_state["gemini_audit"] = {"signature": signature, "text": text, "model": model.strip()}
                st.success("Análise recebida do Gemini. Confira o relatório antes de apresentar.")
            except AuditError as exc:
                st.error(str(exc))

audit = st.session_state.get("gemini_audit")
report = build_report(digest, null_policy, original,
                      audit["text"] if audit else None, audit["model"] if audit else None)
tab_report, tab_chart, tab_cases, tab_delivery = st.tabs([
    "Relatório (PCE & AVL)", "Gráfico de Fronteira", "Casos de Teste", "Entrega da Sprint",
])

with tab_report:
    st.subheader("1. Classes de equivalência")
    st.dataframe(pd.DataFrame(pce_rows(null_policy)), hide_index=True, width="stretch")
    st.info(f"NULL: o texto do manual o declara inválido, mas o exemplo e o TXT o normalizam para zero. Hipótese atual: {NULL_POLICIES[null_policy]}.")
    st.subheader("2. Valor limite e épsilon")
    st.markdown("`DECIMAL(12,2)` usa duas casas decimais. Assim, **ε = 0,01**, e o primeiro valor fora da fronteira inferior é **−0,01**. **0,00 é válido**.")
    st.dataframe(pd.DataFrame(boundary_rows()).drop(columns="Valor"), hide_index=True, width="stretch")
    st.subheader("3. Análise do Gemini")
    if audit:
        st.caption(f"Resposta recebida pela API · Modelo solicitado: {audit['model']}")
        st.markdown(audit["text"])
    else:
        st.info("Insira sua chave e clique em Executar auditoria com Gemini. O conteúdo local não é uma resposta da API.")
    with st.expander("Critérios e limites da análise"):
        st.markdown("""Os casos derivam da regra do manual. A inspeção do fonte é complementar.

- Negativo em qualquer parâmetro: esperado **−1**.
- Demais valores: esperado **(p1 × p2) + p3**, com a hipótese de NULL indicada.
- Um parâmetro varia por vez; os outros permanecem válidos.
- A comparação local usa uma réplica Python. Não executa Informix nem banco Logix.
- Limite superior, overflow, transações e caixa-branca ficam fora desta entrega.
- A réplica usa Decimal com ROUND_HALF_UP. O arredondamento real do Informix precisa ser confirmado.""")

with tab_chart:
    st.subheader("Onde a regra muda de comportamento")
    st.caption("Vermelho: entradas negativas inválidas. Verde: entradas não negativas válidas segundo o manual.")
    st.plotly_chart(boundary_chart(), width="stretch", key="chart_full")
    st.plotly_chart(boundary_chart(zoom=True), width="stretch", key="chart_zoom")
    st.dataframe(pd.DataFrame(boundary_rows()).drop(columns="Valor"), hide_index=True, width="stretch")

with tab_cases:
    st.subheader("24 casos para a função de cálculo")
    st.caption("Esperado = oráculo do manual. Simulado = réplica do TXT original em Python. Não são testes executados no Informix.")
    only_divergent = st.checkbox("Mostrar apenas divergências", key="only_divergent")
    displayed = [row for row in cases if row["Comparação"] == "Divergente"] if only_divergent else cases
    st.dataframe(pd.DataFrame(displayed, columns=list(cases[0])), hide_index=True, width="stretch")
    st.download_button("Baixar casos de teste (.csv)", csv_bytes(cases), "casos_teste_cad0001.csv", "text/csv", key="download_cases")
    st.subheader("Conferir uma entrada")
    st.caption("Informe números com até duas casas. Vazio ou NULL representa valor nulo. Sem separador de milhar.")
    with st.form("calculator"):
        fields = st.columns(3)
        texts = [fields[0].text_input("p1", "-0,01", key="p1"),
                 fields[1].text_input("p2", "10,00", key="p2"),
                 fields[2].text_input("p3", "5,00", key="p3")]
        if st.form_submit_button("Comparar entrada"):
            try:
                values = tuple(parse_input(text) for text in texts)
                expected = expected_value(values, null_policy)
                st.write(f"**Esperado pelo oráculo:** {format_decimal(expected)}")
                if original:
                    simulated = simulate_original(values)
                    st.write(f"**Simulado pelo TXT original:** {format_decimal(simulated)}")
                    if any(v is not None and v < 0 for v in values):
                        st.warning("Há entrada negativa: o TXT não a valida, mesmo se o resultado numérico coincidir com -1.")
                else:
                    st.info("Simulação indisponível para fonte modificado.")
            except (ValueError, ArithmeticError) as exc:
                st.error(f"Entrada inválida: {exc}")

with tab_delivery:
    st.subheader("Checklist do manual")
    st.dataframe(pd.DataFrame([
        {"Requisito": "1. Leitura do CAD0001", "Evidência": "Arquivo real visível no formulário", "Situação": "Disponível"},
        {"Requisito": "2. Análise de PCE", "Evidência": "Classes, domínios e representantes por parâmetro", "Situação": "Disponível"},
        {"Requisito": "3. AVL com épsilon", "Evidência": "Justificativa de ε = 0,01 e cinco pontos", "Situação": "Disponível"},
        {"Requisito": "4. Dashboard gráfico", "Evidência": "Domínio completo, ampliação e tabela", "Situação": "Disponível"},
        {"Requisito": "Integração Gemini", "Evidência": "Análise recebida pela API", "Situação": "Resposta recebida" if audit else "Executar com sua chave"},
    ]), hide_index=True, width="stretch")
    st.download_button("Baixar relatório completo (.md)", report.encode("utf-8"),
                       "relatorio_sprint1.md", "text/markdown", key="download_report")
    st.markdown("""**Roteiro de apresentação:**

1. Mostre o fonte original lido do TXT.
2. Insira sua chave e execute a auditoria com Gemini.
3. Explique as classes e a hipótese para NULL.
4. Mostre o gráfico ampliado: −0,01 → erro, 0,00 → válido, 0,01 → válido.
5. Mostre CT02 e a diferença entre −1,00 esperado e 4,90 simulado.
6. Baixe o relatório e a tabela de casos para acompanhar a entrega.""")

st.divider()
st.caption("TestingStudio Web · Sprint 1 · PCE + AVL · Fonte original preservado · Simulação didática identificada")
