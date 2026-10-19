"""Chave do app lida apenas no servidor, disponível para a avaliação pública."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

SAVED_SOURCE = "Chave salva no app"
MANUAL_SOURCE = "Informar minha chave"


@dataclass(frozen=True, repr=False)
class SavedCredentials:
    api_key: str = ""

    @property
    def ready(self):
        return bool(self.api_key)


def get_saved_credentials():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except (FileNotFoundError, KeyError):
        return SavedCredentials()
    return SavedCredentials(key.strip() if isinstance(key, str) else "")


def render_key_connection():
    # Encerra os estados do antigo formulário após uma atualização sem reinício.
    for name in ("_gemini_saved_key_access", "gemini_access_password", "_gemini_saved_key_error"):
        st.session_state.pop(name, None)
    config = get_saved_credentials()
    if config.ready:
        source = st.selectbox("Chave para a auditoria", [SAVED_SOURCE, MANUAL_SOURCE], key="gemini_key_source")
        if source == SAVED_SOURCE:
            st.success("Chave do app disponível, sem senha de acesso.")
            st.caption("A chave fica no servidor. Verifique o modelo ou execute a auditoria. O uso compartilha a cota do projeto.")
            # A chave do servidor não é preenchida em widget, cookie ou exportação.
            return config.api_key

    key = st.text_input("Gemini API Key", type="password", key="api_key", placeholder="Cole a chave do Google AI Studio",
                        help="Para usar sua própria chave, cole somente o valor, sem aspas ou parênteses.")
    st.caption("Chave adicionada nesta sessão." if key.strip() else "A chave digitada é usada somente nesta sessão.")
    if not config.ready:
        st.caption("Para disponibilizar a chave do app: configure GEMINI_API_KEY em Settings → Secrets do Streamlit.")
    return key


def ensure_key_available(api_key):
    if not api_key.strip():
        from gemini_service import AuditError
        raise AuditError("Insira sua Gemini API Key ou configure a chave do app nos Secrets.")
