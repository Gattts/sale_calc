import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date

st.set_page_config(page_title="Financeiro AWS", page_icon="💰", layout="wide")

# --- CONEXÃO ---
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

def carregar_financeiro():
    """Busca contas a pagar do banco AWS"""
    query = """
        SELECT fornecedor, nro_documento, vencimento, valor, situacao 
        FROM contas_pagar 
        ORDER BY vencimento DESC
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

def style_status(v):
    """Estiliza a tabela"""
    if v == 'Pago': return 'background-color: #d4edda; color: green; font-weight: bold;'
    if v == 'Atrasado': return 'background-color: #f8d7da; color: red; font-weight: bold;'
    return 'background-color: #fff3cd; color: #856404;'

# --- LÓGICA ---
st.title("📊 Contas a Pagar (Nuvem)")

if st.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

df = carregar_financeiro()

if not df.empty:
    # 1. Garante que vencimento é Data
    df['vencimento'] = pd.to_datetime(df['vencimento']).dt.date
    hoje = date.today()

    # 2. Recalcula Status (Lógica Inteligente)
    def definir_status(row):
        # Se no banco já diz 'Pago', mantém
        if str(row['situacao']).strip().lower() == 'pago':
            return 'Pago'
        # Se a data venceu e não está pago -> Atrasado
        if row['vencimento'] < hoje:
            return 'Atrasado'
        return 'Aberto'

    df['Status Real'] = df.apply(definir_status, axis=1)

    # 3. Métricas
    c1, c2, c3, c4 = st.columns(4)
    total = df['valor'].sum()
    atrasado = df[df['Status Real'] == 'Atrasado']['valor'].sum()
    aberto = df[df['Status Real'] == 'Aberto']['valor'].sum()
    pago = df[df['Status Real'] == 'Pago']['valor'].sum()

    c1.metric("Total", f"R$ {total:,.2f}")
    c2.metric("⚠️ Atrasado", f"R$ {atrasado:,.2f}", delta="-Vencido")
    c3.metric("📅 A Vencer", f"R$ {aberto:,.2f}")
    c4.metric("✅ Pago", f"R$ {pago:,.2f}")

    # 4. Tabela Colorida
    # Mostramos apenas colunas úteis
    df_show = df[['fornecedor', 'nro_documento', 'vencimento', 'valor', 'Status Real']].copy()
    df_show.columns = ['Fornecedor', 'Doc', 'Vencimento', 'Valor', 'Situação']
    
    st.dataframe(
        df_show.style.map(style_status, subset=['Situação'])
        .format({"Valor": "R$ {:,.2f}"}),
        use_container_width=True,
        height=600,
        hide_index=True
    )
else:
    st.info("Nenhum registro encontrado no banco de dados.")
