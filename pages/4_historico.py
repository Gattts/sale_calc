import streamlit as st
from utils.ui import carregar_css
from utils.db import run_query

st.set_page_config(page_title="Histórico de Entradas", layout="wide", page_icon="🕒")
carregar_css()

st.title("🕒 Histórico de Entradas")

# Filtros
col1, col2 = st.columns([3, 1])
busca = col1.text_input("🔍 Buscar por nome, SKU ou fornecedor")
ordem = col2.selectbox("Ordenar por", ["Mais Recente", "Mais Antigo", "Maior Valor"])

# Query Dinâmica
query_base = """
    SELECT id, data_compra, sku, nome, fornecedor, nro_nf, quantidade, preco_partida 
    FROM produtos 
"""

params = {}
where_clause = ""

if busca:
    where_clause = "WHERE nome LIKE :b OR sku LIKE :b OR fornecedor LIKE :b"
    params['b'] = f"%{busca}%"

order_clause = "ORDER BY id DESC"
if ordem == "Mais Antigo": order_clause = "ORDER BY id ASC"
elif ordem == "Maior Valor": order_clause = "ORDER BY preco_partida DESC"

final_query = f"{query_base} {where_clause} {order_clause}"
df = run_query(final_query, params if params else None)

# Exibição
if not df.empty:
    st.dataframe(
        df,
        column_config={
            "data_compra": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "preco_partida": st.column_config.NumberColumn("Valor Unit.", format="R$ %.2f"),
            "nro_nf": "Nota Fiscal",
            "quantidade": "Qtd"
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )
else:
    st.warning("Nenhum registro encontrado.")