import os
import requests
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from etl_core_saas import get_valid_token

# Configurações de Banco (Iguais aos anteriores)
DB_USER = os.getenv('DB_USER', 'sigmacomti')
DB_PASS_RAW = os.getenv('DB_PASS', 'Sigma#com13ti2025')
DB_HOST = os.getenv('DB_HOST', '177.153.209.166')
DB_NAME = os.getenv('DB_NAME', 'sigmacomti')
DB_CONN = f'mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS_RAW)}@{DB_HOST}:3306/{DB_NAME}?connect_timeout=60'
ID_EMPRESA = 1

def listar_categorias():
    print("🚀 Buscando Categorias Financeiras no Bling...")
    
    engine = create_engine(DB_CONN)
    with engine.connect() as conn:
        emp = conn.execute(text("SELECT client_id, client_secret, refresh_token FROM empresas_bling WHERE id = :id"), {'id': ID_EMPRESA}).mappings().first()
        token = get_valid_token(dict(emp))['access_token']

    headers = {'Authorization': f'Bearer {token}'}
    
    # Endpoint de Categorias (Naturezas de Operação Financeira)
    url = 'https://www.bling.com.br/Api/v3/categorias/receitas-despesas'
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200:
        cats = r.json().get('data', [])
        print(f"\n📂 --- CATEGORIAS ENCONTRADAS ({len(cats)}) ---")
        for c in cats:
            print(f"ID: {c['id']} | Nome: {c['descricao']}")
    else:
        print(f"Erro: {r.status_code} - {r.text}")

if __name__ == "__main__":
    listar_categorias()