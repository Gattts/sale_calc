import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st

# Configurações de Conexão
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")
    # Garante estrutura mínima
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT peso FROM produtos LIMIT 1"))
    except:
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE produtos ADD COLUMN peso DECIMAL(10,3) DEFAULT 0.0"))
                conn.commit()
        except: pass
    return engine

def run_query(query, params=None):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params) if params else pd.read_sql(text(query), conn)
    except: return pd.DataFrame()

def run_command(query, params):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Erro SQL: {e}")
        return False