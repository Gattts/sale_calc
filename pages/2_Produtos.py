import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Histórico de Compras", page_icon="🛍️", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem !important; }
    .label-info { font-size: 14px; color: #555; font-weight: bold; }
    .value-info { font-size: 18px; color: #000; }
</style>
""", unsafe_allow_html=True)

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
    """Busca histórico fazendo JOIN com fornecedor"""
    query = """
        SELECT p.id, p.sku, p.nome, p.nro_nf, p.data_compra, p.quantidade, 
               p.preco_partida, p.ipi_percent, p.icms_percent, p.preco_final,
               COALESCE(c.fornecedor, 'Não Identificado') as fornecedor
        FROM produtos p
        LEFT JOIN contas_pagar c ON p.nro_nf = c.nro_documento
        ORDER BY p.data_compra DESC, p.id DESC
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

# Botão de refresh e Filtros
col_refresh, col_filter = st.columns([1, 4])
if col_refresh.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

df = carregar_historico()

if not df.empty:
    # --- FILTROS ---
    col_f1, col_f2 = st.columns(2)
    
    # 1. Busca por Texto
    busca = col_f1.text_input("🔍 Buscar Produto (Nome ou SKU)", placeholder="Digite para filtrar...")
    
    # 2. Filtro de Fornecedor
    lista_fornecedores = sorted(df['fornecedor'].unique())
    filtro_fornecedor = col_f2.multiselect("🏢 Filtrar por Fornecedor", options=lista_fornecedores)

    # Aplica Filtros
    df_filtrado = df.copy()
    
    if busca:
        mask_texto = df_filtrado['nome'].str.contains(busca, case=False, na=False) | df_filtrado['sku'].str.contains(busca, case=False, na=False)
        df_filtrado = df_filtrado[mask_texto]
        
    if filtro_fornecedor:
        df_filtrado = df_filtrado[df_filtrado['fornecedor'].isin(filtro_fornecedor)]

    # --- RESULTADO ---
    skus_unicos = df_filtrado['sku'].unique()
    st.caption(f"Mostrando {len(skus_unicos)} produtos de {len(df_filtrado)} registros encontrados.")
    st.divider()

    for sku in skus_unicos:
        historico_produto = df_filtrado[df_filtrado['sku'] == sku]
        ultima_compra = historico_produto.iloc[0]
        
        nome_prod = ultima_compra['nome']
        data_recente = pd.to_datetime(ultima_compra['data_compra']).strftime('%d/%m/%Y')
        preco_recente = ultima_compra['preco_final']
        fornecedor_top = ultima_compra['fornecedor']
        
        # Título do Dropdown
        label_expander = f"📦 {sku} | {nome_prod} — R$ {preco_recente:,.2f} ({data_recente})"
        
        with st.expander(label_expander):
            st.markdown("#### 🔖 Compra Mais Recente")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='label-info'>Fornecedor</div><div class='value-info'>{fornecedor_top}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='label-info'>Preço NF</div><div class='value-info'>R$ {ultima_compra['preco_partida']:,.2f}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='label-info'>Custo Final</div><div class='value-info'>R$ {ultima_compra['preco_final']:,.2f}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='label-info'>NF</div><div class='value-info'>{ultima_compra['nro_nf']}</div>", unsafe_allow_html=True)

            st.write("")
            st.markdown("#### ⏳ Histórico Recente")
            
            top_5 = historico_produto.head(5).copy()
            cols_show = {
                'data_compra': 'Data',
                'fornecedor': 'Fornecedor',
                'nro_nf': 'Nota Fiscal',
                'quantidade': 'Qtd',
                'preco_partida': 'Valor NF (Un)',
                'preco_final': 'Custo Real (Un)'
            }
            
            top_5['data_compra'] = pd.to_datetime(top_5['data_compra']).dt.strftime('%d/%m/%Y')
            
            st.dataframe(
                top_5[cols_show.keys()].rename(columns=cols_show).style.format({
                    'Valor NF (Un)': 'R$ {:,.2f}',
                    'Custo Real (Un)': 'R$ {:,.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
else:
    st.info("Nenhum histórico encontrado.")
