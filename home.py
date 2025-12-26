import streamlit as st
from utils.ui import carregar_css

# Configuração Global
st.set_page_config(page_title="Market Manager Pro", layout="wide", page_icon="🛍️")
carregar_css()

# --- Definição das Páginas ---
# Certifique-se que os arquivos estão na pasta views/

# GRUPO 1: OPERACIONAL
pg_calc = st.Page("views/calculadora.py", title="Calculadora de Margem", icon="🧮")
pg_cad = st.Page("views/cadastro.py", title="Cadastro de Produtos", icon="📦")
pg_hist = st.Page("views/historico.py", title="Histórico de Entradas", icon="🕒")

# GRUPO 2: FINANCEIRO
pg_fin_resumo = st.Page("views/fin_valuation.py", title="Valuation & Estoque", icon="💰")
pg_fin_contas = st.Page("views/fin_contas.py", title="Contas a Pagar", icon="💸")
pg_fin_proj = st.Page("views/fin_projecao.py", title="Projeção & Fixos", icon="📈")

# --- Navegação ---

pg = st.navigation({
    "Operacional": [pg_calc, pg_cad, pg_hist],
    "Financeiro": [pg_fin_resumo, pg_fin_contas, pg_fin_proj]
})

pg.run()
