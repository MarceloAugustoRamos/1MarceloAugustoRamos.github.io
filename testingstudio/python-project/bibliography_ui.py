"""Consulta das fontes, sem depender da API Gemini ou da análise de código."""
import streamlit as st

from bibliography import GROUPS, MODULE_SOURCES, REVIEW_DATE, SOURCES, SOURCE_NOTE, references_markdown


def render_references():
    st.title("Fontes e referências")
    st.write("De onde vêm as regras, os conceitos e as decisões deste laboratório.")
    st.caption("Revisão bibliográfica: " + REVIEW_DATE)
    st.info(SOURCE_NOTE)
    with st.expander("Qual fonte sustenta cada módulo?", expanded=True):
        for module, ids in MODULE_SOURCES.items():
            st.write(f"**{module}:** {', '.join(ids)}")
    st.download_button("Baixar referências (.md)", references_markdown().encode(),
                       "TestingStudio_Referencias.md", "text/markdown", key="download_references")
    for group in GROUPS:
        st.subheader(group)
        for source in SOURCES:
            if source["group"] != group:
                continue
            with st.container(border=True):
                st.markdown(f"**[{source['id']}] {source['title']}**")
                st.write(source["citation"])
                st.write(source["scope"])
                st.caption(source["location"])
                if source["url"]:
                    st.link_button("Consultar fonte ↗", source["url"])
                    st.caption("Acesso em: " + REVIEW_DATE)
    st.caption("Materiais da disciplina são identificados pelo arquivo e pelas páginas. Os PDFs de aula não são redistribuídos nesta seção.")
