import streamlit as st
import pandas as pd
from utils.ui import carregar_css
from utils.db import run_query

st.set_page_config(page_title="Histórico do Produto", layout="wide", page_icon="🕒")
carregar_css()

st.title("🕒 Ficha de Entradas do Produto")

# 1. Carrega Lista de Produtos Únicos para o Selectbox
try:
    df_lista = run_query("SELECT DISTINCT sku, nome FROM produtos ORDER BY nome")
    if df_lista.empty:
        st.warning("Nenhum produto cadastrado.")
        st.stop()
        
    # Cria mapa para busca: "SKU - Nome"
    mapa_produtos = {f"{row['sku']} - {row['nome']}": row['sku'] for _, row in df_lista.iterrows()}
    
    # Selectbox de Busca
    escolha = st.selectbox("🔎 Selecione o Produto para ver o histórico:", 
                           ["Selecione..."] + list(mapa_produtos.keys()))

    if escolha != "Selecione...":
        sku_selecionado = mapa_produtos[escolha]
        
        # 2. Busca todo o histórico desse SKU específico
        query_hist = """
            SELECT data_compra, fornecedor, nro_nf, quantidade, 
                   preco_partida, preco_final, ipi_percent, icms_percent
            FROM produtos 
            WHERE sku = :sku 
            ORDER BY id DESC
        """
        df_hist = run_query(query_hist, {'sku': sku_selecionado})
        
        if not df_hist.empty:
            # Pega a linha mais recente (a primeira, pois ordenamos DESC)
            ultimo = df_hist.iloc[0]
            
            st.markdown("### 🆕 Resumo da Última Entrada")
            
            # Cards de Resumo da Última Entrada
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Data Entrada", pd.to_datetime(ultimo['data_compra']).strftime("%d/%m/%Y") if ultimo['data_compra'] else "-")
                c2.metric("Fornecedor", ultimo['fornecedor'])
                c3.metric("Nota Fiscal", ultimo['nro_nf'])
                c4.metric("Qtd. Comprada", f"{int(ultimo['quantidade'])}")
                
                st.divider()
                
                c5, c6, c7, c8 = st.columns(4)
                c5.metric("💵 Valor NF (Un.)", f"R$ {ultimo['preco_partida']:,.2f}")
                c6.metric("💰 Custo Final (Un.)", f"R$ {ultimo['preco_final']:,.2f}")
                c7.metric("IPI", f"{ultimo['ipi_percent']:.2f}%")
                c8.metric("ICMS Crédito", f"{ultimo['icms_percent']:.2f}%")

            # 3. Tabela com o Histórico Completo
            st.markdown("### 📜 Histórico de Registros Anteriores")
            st.dataframe(
                df_hist,
                column_config={
                    "data_compra": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "preco_partida": st.column_config.NumberColumn("Valor NF", format="R$ %.2f"),
                    "preco_final": st.column_config.NumberColumn("Custo Final", format="R$ %.2f"),
                    "ipi_percent": st.column_config.NumberColumn("IPI %", format="%.2f%%"),
                    "quantidade": "Qtd",
                    "nro_nf": "Nota Fiscal",
                    "fornecedor": "Fornecedor"
                },
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.warning("Erro: Produto listado mas sem histórico encontrado.")

except Exception as e:
    st.error(f"Erro ao carregar histórico: {e}")
