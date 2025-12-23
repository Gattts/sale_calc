import streamlit as st
import pandas as pd
import plotly.express as px
from utils.ui import carregar_css
from utils.db import run_query

st.set_page_config(page_title="Financeiro", layout="wide", page_icon="💰")
carregar_css()

st.title("💰 Financeiro & Valuation")

# 1. Dados
df = run_query("""
    SELECT 
        sku, nome, quantidade, preco_partida, preco_final, 
        (preco_partida * quantidade) as total_investido,
        (preco_final * quantidade) as custo_real_total
    FROM produtos
""")

if df.empty:
    st.info("Nenhum dado financeiro disponível. Cadastre produtos primeiro.")
else:
    # 2. KPIs do Topo
    investimento_bruto = df['total_investido'].sum()
    custo_real_estoque = df['custo_real_total'].sum()
    creditos_fiscais = investimento_bruto - custo_real_estoque
    total_itens = df['quantidade'].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investimento em Estoque", f"R$ {investimento_bruto:,.2f}")
    c2.metric("Custo Real (Pós-Impostos)", f"R$ {custo_real_estoque:,.2f}")
    c3.metric("Créditos Recuperáveis", f"R$ {creditos_fiscais:,.2f}", help="ICMS + PIS/COFINS a recuperar")
    c4.metric("Itens em Estoque", f"{int(total_itens)}")

    st.markdown("---")

    # 3. Gráficos
    col_g1, col_g2 = st.columns([2, 1])

    with col_g1:
        st.subheader("💰 Distribuição de Valor por Produto")
        # Gráfico de Barras: Quais produtos seguram mais dinheiro
        top_produtos = df.nlargest(10, 'total_investido')
        fig = px.bar(top_produtos, x='nome', y='total_investido', 
                     title="Top 10 Produtos com Maior Valor em Estoque",
                     labels={'total_investido': 'Valor Investido (R$)', 'nome': 'Produto'},
                     text_auto='.2s')
        fig.update_layout(xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        st.subheader("📊 Composição")
        # Gráfico de Pizza: Representatividade
        fig2 = px.pie(top_produtos, values='total_investido', names='sku', 
                      title="Share de Estoque (Top 10)")
        st.plotly_chart(fig2, use_container_width=True)

    # 4. Tabela Detalhada
    with st.expander("🔎 Ver Tabela Financeira Completa"):
        st.dataframe(
            df[['sku', 'nome', 'quantidade', 'preco_partida', 'total_investido', 'custo_real_total']],
            column_config={
                "preco_partida": st.column_config.NumberColumn("Preço Unit.", format="R$ %.2f"),
                "total_investido": st.column_config.NumberColumn("Total Bruto", format="R$ %.2f"),
                "custo_real_total": st.column_config.NumberColumn("Custo Real", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )