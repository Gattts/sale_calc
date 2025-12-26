import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# ==============================================================================
# ⚙️ CONFIGURAÇÃO DA CONEXÃO EXTERNA
# ==============================================================================
DB_USER = os.getenv('DB_USER_EXT', 'sigmacomti')
DB_PASS_RAW = os.getenv('DB_PASS_EXT', 'Sigma#com13ti2025')
DB_HOST = os.getenv('DB_HOST_EXT', '177.153.209.166')
DB_NAME = os.getenv('DB_NAME_EXT', 'sigmacomti')

DB_CONN_STR = f'mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS_RAW)}@{DB_HOST}:3306/{DB_NAME}?connect_timeout=60'
TABLE_NAME = "contas_pagar" 

def get_external_connection():
    return create_engine(DB_CONN_STR)

def buscar_dados_externos():
    """Busca TODO o histórico, sem exceções."""
    try:
        engine = get_external_connection()
        
        # SEM WHERE: Trazemos Aberto, Pago, Cancelado, Liquidado... TUDO.
        query = f"""
        SELECT 
            id AS id_origem,
            nome_fornecedor AS fornecedor,
            numero_documento AS nro_documento,
            data_vencimento AS vencimento,
            valor,
            historico AS descricao,
            nome_categoria AS categoria,
            situacao_nome
        FROM {TABLE_NAME}
        ORDER BY data_vencimento DESC
        """
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            
        df['categoria'] = df['categoria'].fillna('Geral')
        df['descricao'] = df['descricao'].fillna(df['fornecedor'])
            
        return df
        
    except Exception as e:
        return str(e)