"""Chave persistida em Streamlit Secrets, desbloqueada apenas na sessão autorizada."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass

import streamlit as st

SAVED_SOURCE = "Chave salva no app"
MANUAL_SOURCE = "Informar minha chave"
AUTH_STATE = "_gemini_saved_key_access"
PASSWORD_STATE = "gemini_access_password"
ERROR_STATE = "_gemini_saved_key_error"


@dataclass(frozen=True, repr=False)
class SavedCredentials:
    api_key: str = ""
    password: str = ""

    @property
    def ready(self):
        return bool(self.api_key) and len(self.password) >= 12

    @property
    def fingerprint(self):
        if not self.ready:
            return ""
        return hashlib.sha256(json.dumps([self.api_key, self.password], ensure_ascii=False).encode()).hexdigest()


def get_saved_credentials():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        password = st.secrets.get("GEMINI_ACCESS_PASSWORD", "")
    except (FileNotFoundError, KeyError):
        return SavedCredentials()
    return SavedCredentials(key.strip() if isinstance(key, str) else "",
                            password if isinstance(password, str) else "")


def is_unlocked(config, state):
    return config.ready and hmac.compare_digest(str(state.get(AUTH_STATE, "")), config.fingerprint)


def unlock_saved_key():
    config = get_saved_credentials()
    password = st.session_state.get(PASSWORD_STATE, "")
    st.session_state[PASSWORD_STATE] = ""
    st.session_state.pop(AUTH_STATE, None)
    if config.ready and hmac.compare_digest(password.encode(), config.password.encode()):
        st.session_state[AUTH_STATE] = config.fingerprint
        st.session_state.pop(ERROR_STATE, None)
    else:
        st.session_state[ERROR_STATE] = "Senha de acesso incorreta ou configuração alterada."


def lock_saved_key():
    for key in (AUTH_STATE, ERROR_STATE, PASSWORD_STATE, "gemini_audit"):
        st.session_state.pop(key, None)


def render_key_connection():
    config = get_saved_credentials()
    if config.ready:
        source = st.selectbox("Chave para a auditoria", [SAVED_SOURCE, MANUAL_SOURCE], key="gemini_key_source")
        if source == SAVED_SOURCE:
            if is_unlocked(config, st.session_state):
                st.success("Chave salva liberada nesta sessão.")
                st.caption("Senha aceita. Use Verificar chave e modelo para consultar o acesso no Google.")
                st.button("Bloquear acesso", icon=":material/lock:", key="gemini_saved_lock", on_click=lock_saved_key)
                # A chave nunca é colocada em um widget, cookie ou exportação.
                return config.api_key
            with st.form("gemini_saved_key_form"):
                st.text_input("Senha de acesso", type="password", key=PASSWORD_STATE,
                              placeholder="Senha definida nos Secrets")
                st.form_submit_button("Usar chave salva", on_click=unlock_saved_key, width="stretch")
            if st.session_state.get(ERROR_STATE):
                st.error(st.session_state[ERROR_STATE])
            st.caption("A chave fica no servidor. A senha libera seu uso somente nesta sessão.")
            st.caption("A senha tem pelo menos 12 caracteres e é diferente da API key copiada do AI Studio.")
            return ""
    elif config.api_key:
        st.warning("Configure GEMINI_ACCESS_PASSWORD com pelo menos 12 caracteres nos Secrets para liberar a chave salva.")

    key = st.text_input("Gemini API Key", type="password", key="api_key", placeholder="Cole a chave do Google AI Studio",
                        help="Cole somente a chave, sem aspas ou parênteses. Este campo não recebe a senha de acesso do app.")
    st.caption("Chave adicionada nesta sessão." if key.strip() else "A chave digitada é usada somente nesta sessão.")
    if not config.ready:
        st.caption("Para salvar uma vez: configure GEMINI_API_KEY e GEMINI_ACCESS_PASSWORD em Settings → Secrets do Streamlit.")
    return key


def ensure_key_available(api_key):
    if not api_key and st.session_state.get("gemini_key_source") == SAVED_SOURCE and get_saved_credentials().ready:
        from gemini_service import AuditError
        raise AuditError("Abra Conexão Gemini e informe sua senha de acesso para usar a chave salva.")
