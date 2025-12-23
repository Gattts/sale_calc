import streamlit as st
from utils.ui import carregar_css
from utils.db import run_query

st.set_page_config(page_title="Market Manager - Home", layout="wide", page_icon="🏢")
carregar_css()

st.title("🏢 Visão Geral")

# Métricas do Dashboard
try:
    df_prod = run_query("SELECT COUNT(*) as total FROM produtos")
    total_prods = df_prod['total'][0] if not df_prod.empty else 0
except:
    total_prods = 0

col1, col2, col3 = st.columns(3)
col1.metric("Empresas Ativas", "1") # Placeholder para o futuro
col2.metric("Produtos Cadastrados", f"{total_prods}")
col3.metric("Status do Sistema", "Online 🟢")

from utils.ui import card_meta
card_meta("100%")

st.divider()
st.info("👈 Selecione uma ferramenta no menu lateral para começar.")