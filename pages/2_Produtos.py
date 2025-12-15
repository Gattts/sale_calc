import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Histórico de Compras", page_icon="🛍️", layout="wide")

# ==============================================================================
# 1. CONEXÃO AWS
# ==============================================================================
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

def carregar_historico():
    """Busca TODO o histórico ordenado da compra mais recente para a mais antiga"""
    query = """
        SELECT id, sku, nome, nro_nf, data_compra, quantidade, 
               preco_partida, ipi_percent, icms_percent, preco_final
        FROM produtos 
        ORDER BY data_compra DESC, id DESC
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# ==============================================================================
# 2. INTERFACE
# ==============================================================================
st.title("🛍️ Histórico de Compras")
st.caption("Consulte as últimas entradas, custos e impostos pagos por produto.")

# Botão de atualização
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

df = carregar_historico()

if not df.empty:
    # --- BARRA DE BUSCA ---
    busca = st.text_input("🔍 Buscar Produto (Nome ou SKU)", placeholder="Digite para filtrar...")
    
    if busca:
        # Filtra ignorando maiúsculas/minúsculas
        mask = df['nome'].str.contains(busca, case=False, na=False) | df['sku'].str.contains(busca, case=False, na=False)
        df_filtrado = df[mask]
    else:
        df_filtrado = df

    # --- LÓGICA DE AGRUPAMENTO ---
    # Pegamos a lista única de SKUs presentes no filtro (mantendo a ordem cronológica do DF original)
    skus_unicos = df_filtrado['sku'].unique()

    st.markdown(f"**Encontrados:** {len(skus_unicos)} produtos distintos nas compras filtradas.")
    st.divider()

    # Para cada SKU único, cria um bloco visual
    for sku in skus_unicos:
        # Pega todo o histórico desse SKU
        historico_produto = df_filtrado[df_filtrado['sku'] == sku]
        
        # A primeira linha é a mais recente (pois o SQL já ordenou DESC)
        ultima_compra = historico_produto.iloc[0]
        
        nome_prod = ultima_compra['nome']
        data_recente = pd.to_datetime(ultima_compra['data_compra']).strftime('%d/%m/%Y')
        preco_recente = ultima_compra['preco_final']
        
        # Título do Dropdown (Resumo)
        label_expander = f"📦 {sku} | {nome_prod} — Última: R$ {preco_recente:,.2f} em {data_recente}"
        
        with st.expander(label_expander):
            # --- DETALHES DA ÚLTIMA COMPRA (DESTAQUE) ---
            st.markdown("#### 🔖 Detalhes da Compra Mais Recente")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Preço Compra (NF)", f"R$ {ultima_compra['preco_partida']:,.2f}")
            c2.metric("Custo Final", f"R$ {ultima_compra['preco_final']:,.2f}", help="Custo com impostos recuperáveis descontados")
            c3.metric("Impostos %", f"IPI: {ultima_compra['ipi_percent']}% | ICMS: {ultima_compra['icms_percent']}%")
            c4.metric("Nota Fiscal", f"{ultima_compra['nro_nf']}")

            # --- TABELA COM AS 5 ÚLTIMAS COMPRAS ---
            st.markdown("#### ⏳ Histórico Recente (Últimas 5 Entradas)")
            
            # Pega as 5 primeiras linhas e seleciona colunas úteis
            top_5 = historico_produto.head(5).copy()
            
            # Renomeia para ficar bonito na tabela
            cols_show = {
                'data_compra': 'Data',
                'nro_nf': 'Nota Fiscal',
                'quantidade': 'Qtd',
                'preco_partida': 'Valor NF (Un)',
                'ipi_percent': 'IPI %',
                'icms_percent': 'ICMS %',
                'preco_final': 'Custo Real (Un)'
            }
            
            # Formata datas
            top_5['data_compra'] = pd.to_datetime(top_5['data_compra']).dt.strftime('%d/%m/%Y')
            
            # Exibe tabela estilizada
            st.dataframe(
                top_5[cols_show.keys()].rename(columns=cols_show).style.format({
                    'Valor NF (Un)': 'R$ {:,.2f}',
                    'Custo Real (Un)': 'R$ {:,.2f}',
                    'IPI %': '{:.1f}%',
                    'ICMS %': '{:.1f}%'
                }),
                use_container_width=True,
                hide_index=True
            )
            
else:
    st.info("Nenhum histórico de compras encontrado no banco de dados.")
