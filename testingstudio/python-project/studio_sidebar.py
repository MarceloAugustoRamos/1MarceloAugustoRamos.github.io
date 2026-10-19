"""Barra lateral do laboratório; navegação nativa e estilos locais."""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from gemini_service import AuditError, DEFAULT_MODEL, check_gemini_access
from gemini_credentials import render_key_connection

VIEWS = {
    "Visão geral": "dashboard",
    "Caixa-preta": "contrast",
    "Caixa-branca": "account_tree",
    "Def-Uso e mutação": "hub",
    "Requisitos e RTM": "grid_view",
    "Gemini": "auto_awesome",
    "Entrega": "folder_open",
}


def render_sidebar():
    css = (Path(__file__).resolve().parent / "assets" / "sidebar.css").read_text(encoding="utf-8")
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('''<div class="studio-brand">
          <div class="studio-brand-mark" aria-hidden="true">t<span>_</span></div>
          <div><div class="studio-brand-name">TestingStudio</div><div class="studio-brand-sub">WEB LABORATORY</div></div>
        </div>
        <div class="studio-workspace"><span class="studio-workspace-icon" aria-hidden="true">TS</span>
          <div><strong>Teste de Software I</strong><span>Seu espaço de auditoria · 2026.2</span></div>
        </div><div class="studio-section-label">EXPLORAR O LABORATÓRIO</div>''', unsafe_allow_html=True)
        view = st.radio("Laboratório", list(VIEWS), key="view", label_visibility="collapsed", width="stretch",
                        format_func=lambda name: f":material/{VIEWS[name]}: {name}")
        st.markdown('<div class="studio-section-label studio-tools-label">FERRAMENTAS</div>', unsafe_allow_html=True)
        with st.expander("Conexão Gemini", icon=":material/auto_awesome:", expanded=view == "Gemini"):
            st.caption("GOOGLE AI STUDIO")
            api_key = render_key_connection()
            model = st.text_input("Modelo Gemini", os.getenv("GEMINI_MODEL", DEFAULT_MODEL), key="model")
            if st.button("Verificar chave e modelo", key="verify_gemini", disabled=not api_key.strip(),
                         width="stretch", help="Consulta o modelo no Google, sem gerar uma auditoria. Não confirma a cota de geração."):
                try:
                    with st.spinner("Consultando acesso no Google..."):
                        check_gemini_access(api_key, model)
                    st.success("O Google aceitou a chave e permitiu consultar este modelo.")
                    st.caption("A auditoria ainda depende da cota de geração disponível.")
                except AuditError as exc:
                    st.error(str(exc))
            st.link_button("Obter chave no AI Studio", "https://aistudio.google.com/apikey",
                           icon=":material/open_in_new:", width="stretch")
        with st.expander("Parâmetros da análise", icon=":material/tune:"):
            precision = st.selectbox("Casas decimais", ["Automático", "0", "1", "2", "3", "4", "5", "6"], key="precision")
            lower = st.text_input("Limite inferior válido", "0", key="lower")
            null_policy = st.selectbox("Hipótese para NULL", ["zero", "reject"],
                                       format_func=lambda x: "Normalizar para zero" if x == "zero" else "Rejeitar como inválido", key="null_policy")
            oracle_mode = st.selectbox("Oráculo", ["cad0001", "differential"],
                                       format_func=lambda x: "Regra CAD0001 do manual" if x == "cad0001" else "Apenas comparação diferencial", key="oracle_mode")
            equivalents = st.text_input("Mutantes equivalentes confirmados", key="equivalents", placeholder="M02, M05")
            st.caption("Declare equivalência após revisão humana. Mutantes mortos não podem ser excluídos.")
        st.markdown('''<div class="studio-sidebar-footer"><span class="studio-engine-dot" aria-hidden="true"></span>
          <div><strong>Motor Python</strong><span>Teste de Software I · Ementa 62371</span></div></div>
          <div class="studio-sidebar-credit">Prof. Frank Piffer <span>·</span> v3.0</div>''', unsafe_allow_html=True)
    return view, precision, lower, null_policy, oracle_mode, equivalents, api_key, model
