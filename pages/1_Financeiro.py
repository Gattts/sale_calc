import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date

st.set_page_config(page_title="Financeiro", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 3rem !important; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

def carregar_financeiro():
    query = """
        SELECT id, fornecedor, nro_documento, vencimento, valor, situacao 
        FROM contas_pagar 
        ORDER BY vencimento DESC
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()

def style_status(v):
    if str(v).lower() == 'pago': return 'background-color: #d4edda; color: green; font-weight: bold;'
    if str(v).lower() == 'atrasado': return 'background-color: #f8d7da; color: red; font-weight: bold;'
    return 'background-color: #fff3cd; color: #856404;'

# --- LÓGICA ---
st.title("📊 Gestão Financeira")

if st.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

df = carregar_financeiro()

if not df.empty:
    # Tratamento de Datas e Status
    df['vencimento'] = pd.to_datetime(df['vencimento']).dt.date
    hoje = date.today()

    def definir_status(row):
        if str(row['situacao']).strip().lower() == 'pago': return 'Pago'
        if row['vencimento'] < hoje: return 'Atrasado'
        return 'Aberto'

    df['Status Real'] = df.apply(definir_status, axis=1)

    # --- ÁREA DE FILTROS ---
    with st.container(border=True):
        st.caption("Filtros Avançados")
        c1, c2, c3 = st.columns(3)
        
        # Filtro 1: Fornecedor
        lista_fornecedores = sorted(df['fornecedor'].unique().astype(str))
        filtro_forn = c1.multiselect("🏢 Fornecedor", options=lista_fornecedores)
        
        # Filtro 2: Situação
        lista_status = sorted(df['Status Real'].unique().astype(str))
        filtro_sit = c2.multiselect("📌 Situação", options=lista_status)
        
        # Filtro 3: Documento
        busca_doc = c3.text_input("📄 NF/Parcela", placeholder="Digite o número...")

    # APLICAÇÃO DOS FILTROS
    df_filtrado = df.copy()
    
    if filtro_forn:
        df_filtrado = df_filtrado[df_filtrado['fornecedor'].isin(filtro_forn)]
    
    if filtro_sit:
        df_filtrado = df_filtrado[df_filtrado['Status Real'].isin(filtro_sit)]
        
    if busca_doc:
        df_filtrado = df_filtrado[df_filtrado['nro_documento'].astype(str).str.contains(busca_doc, case=False)]

    # --- MÉTRICAS (Baseadas no Filtrado) ---
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    total = df_filtrado['valor'].sum()
    atrasado = df_filtrado[df_filtrado['Status Real'] == 'Atrasado']['valor'].sum()
    aberto = df_filtrado[df_filtrado['Status Real'] == 'Aberto']['valor'].sum()
    pago = df_filtrado[df_filtrado['Status Real'] == 'Pago']['valor'].sum()

    m1.metric("Total Filtrado", f"R$ {total:,.2f}")
    m2.metric("⚠️ Atrasado", f"R$ {atrasado:,.2f}")
    m3.metric("📅 Em Aberto", f"R$ {aberto:,.2f}")
    m4.metric("✅ Pago", f"R$ {pago:,.2f}")

    # --- TABELA ---
    # Renomeando colunas para exibição
    df_show = df_filtrado[['fornecedor', 'nro_documento', 'vencimento', 'valor', 'Status Real']].copy()
    df_show.columns = ['Fornecedor', 'NF/Parcela', 'Vencimento', 'Valor', 'Situação']
    
    st.dataframe(
        df_show.style.map(style_status, subset=['Situação'])
        .format({"Valor": "R$ {:,.2f}", "Vencimento": "{:%d/%m/%Y}"}),
        use_container_width=True,
        height=600,
        hide_index=True
    )
else:
    st.info("Nenhum registro encontrado.")
