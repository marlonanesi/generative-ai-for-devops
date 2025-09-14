from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st
from dotenv import load_dotenv

# Carrega .env (um nível acima de app/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

API_HOST = os.getenv('API_HOST', '127.0.0.1')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_BASE = f"http://{API_HOST}:{API_PORT}"

st.set_page_config(page_title="Items UI", layout="wide")
st.title("Items UI")

TAB_LISTAR, TAB_CRIAR, TAB_EDITAR = st.tabs(["Listar / Filtrar", "Criar", "Editar / Excluir"])

client = httpx.Client(base_url=API_BASE, timeout=10.0)

STATUS_OPCOES = ["", "pending", "in_progress", "done"]

with TAB_LISTAR:
    st.subheader("Listar Itens")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.selectbox("Status", STATUS_OPCOES, index=0)
    with col_f2:
        limit = st.number_input("Limit", min_value=1, max_value=200, value=50)
    with col_f3:
        offset = st.number_input("Offset", min_value=0, value=0)

    if st.button("Carregar"):
        params = {"limit": limit, "offset": offset}
        if status_filter:
            params["status"] = status_filter
        try:
            r = client.get("/items", params=params)
            if r.status_code == 200:
                data = r.json()
                if data:
                    st.dataframe(data, use_container_width=True)
                else:
                    st.info("Nenhum item.")
            else:
                st.error(f"Erro: {r.status_code} - {r.text}")
        except Exception as e:
            st.error(f"Falha na requisição: {e}")

with TAB_CRIAR:
    st.subheader("Criar Item")
    with st.form("form_criar"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        status_val = st.selectbox("Status", ["pending", "in_progress", "done"], index=0)
        submitted = st.form_submit_button("Criar")
        if submitted:
            payload = {"title": title, "description": description or None, "status": status_val}
            try:
                r = client.post("/items", json=payload)
                if r.status_code == 201:
                    st.success(f"Criado: {r.json()['id']}")
                else:
                    st.error(f"Erro {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Falha: {e}")

with TAB_EDITAR:
    st.subheader("Buscar / Editar / Excluir")
    busc_id = st.text_input("ID do Item (UUID)")
    if st.button("Buscar") and busc_id:
        try:
            r = client.get(f"/items/{busc_id}")
            if r.status_code == 200:
                st.session_state["_item_edit"] = r.json()
            else:
                st.error("Não encontrado")
        except Exception as e:
            st.error(f"Falha: {e}")

    item_edit = st.session_state.get("_item_edit")
    if item_edit:
        st.write(f"Editando: {item_edit['id']}")
        with st.form("form_editar"):
            new_title = st.text_input("Title", value=item_edit["title"])
            new_description = st.text_area("Description", value=item_edit.get("description") or "")
            new_status = st.selectbox("Status", ["pending", "in_progress", "done"], index=["pending", "in_progress", "done"].index(item_edit["status"]))
            submitted_edit = st.form_submit_button("Salvar alterações")
            if submitted_edit:
                payload = {"title": new_title, "description": new_description or None, "status": new_status}
                try:
                    r = client.put(f"/items/{item_edit['id']}", json=payload)
                    if r.status_code == 200:
                        st.success("Atualizado")
                        st.session_state["_item_edit"] = r.json()
                    else:
                        st.error(f"Erro {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"Falha: {e}")
        if st.button("Excluir", type="primary"):
            try:
                r = client.delete(f"/items/{item_edit['id']}")
                if r.status_code == 204:
                    st.success("Excluído")
                    st.session_state.pop("_item_edit", None)
                else:
                    st.error(f"Erro {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Falha: {e}")

st.caption(f"Backend: {API_BASE}")
