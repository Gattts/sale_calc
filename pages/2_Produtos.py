import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Produtos", page_icon="📦", layout="wide")

# --- Função de Carregamento ---
def carregar_produtos():
    # Caminho absoluto para garantir que ache o arquivo na raiz
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    caminho_csv = os.path.join(raiz, 'produtos.csv')
    
    if not os.path.exists(caminho_csv):
        st.error("Arquivo produtos.csv não encontrado!")
        return pd.DataFrame()
    
    # Lê o CSV
    df = pd.read_csv(caminho_csv)
    # Garante que a data é data mesmo (para ordenar)
    df['data_compra'] = pd.to_datetime(df['data_compra'])
    return df

st.title("📦 Catálogo de Produtos e Histórico")
st.markdown("Visualize o preço atual e expanda para ver as últimas 5 compras.")

df = carregar_produtos()

if not df.empty:
    # --- FILTRO DE BUSCA ---
    busca = st.text_input("🔍 Buscar por Nome ou SKU", placeholder="Digite para filtrar...")
    
    if busca:
        df = df[df['nome'].str.contains(busca, case=False) | df['sku'].str.contains(busca, case=False)]

    # --- LÓGICA DE AGRUPAMENTO ---
    # Pegamos a lista de SKUs únicos para montar as "linhas"
    skus_unicos = df['sku'].unique()

    # Cabeçalho da "Tabela" visual
    cols = st.columns([1.5, 3, 1.5, 1.5, 1.5, 1.5, 1])
    cols[0].markdown("**SKU**")
    cols[1].markdown("**Produto**")
    cols[2].markdown("**R$ Partida**")
    cols[3].markdown("**Última NF**")
    cols[4].markdown("**Data**")
    cols[5].markdown("**R$ Final**")
    cols[6].markdown("**Qtd**")
    st.divider()

    # Loop para criar as linhas expansíveis
    for sku in skus_unicos:
        # Filtra todas as compras desse produto e ordena pela data (mais nova primeiro)
        historico = df[df['sku'] == sku].sort_values(by='data_compra', ascending=False)
        
        # Pega a compra mais recente (Topo da lista)
        atual = historico.iloc[0]

        # Formata os valores para exibição no título
        texto_partida = f"R$ {atual['preco_partida']:,.2f}"
        texto_final = f"R$ {atual['preco_final']:,.2f}"
        data_formatada = atual['data_compra'].strftime('%d/%m/%Y')

        # --- O TRUQUE VISUAL ---
        # Usamos o Expander como se fosse uma linha da tabela
        # O label do expander resume as informações principais
        label_expander = f"{atual['sku']}  |  {atual['nome']}  (Última: {data_formatada})"
        
        with st.expander(label_expander):
            # Parte de cima: Detalhes da última compra em destaque
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Preço Partida", texto_partida)
            c2.metric("IPI", f"{atual['ipi_percent']}%")
            c3.metric("ICMS", f"{atual['icms_percent']}%")
            c4.metric("Preço Final Calculado", texto_final)

            st.markdown("#### 🕒 Histórico das últimas 5 compras")
            
            # Mostra apenas as 5 primeiras do histórico (Paginação simplificada)
            top_5 = historico.head(5).copy()
            
            # Formatação visual da tabelinha interna
            st.dataframe(
                top_5,
                column_config={
                    "data_compra": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "preco_partida": st.column_config.NumberColumn("Partida", format="R$ %.2f"),
                    "preco_final": st.column_config.NumberColumn("Final", format="R$ %.2f"),
                    "ipi_percent": st.column_config.NumberColumn("IPI %", format="%.1f%%"),
                    "icms_percent": st.column_config.NumberColumn("ICMS %", format="%.1f%%"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            if len(historico) > 5:
                st.info(f"Existem mais {len(historico) - 5} registros antigos não exibidos.")

else:
    st.warning("Nenhum produto cadastrado no CSV.")
