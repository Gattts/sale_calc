import os
import requests
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from etl_core_saas import get_valid_token # Reutiliza sua função de token

# --- CONFIGURAÇÃO DB ---
DB_USER = os.getenv('DB_USER', 'sigmacomti')
DB_PASS_RAW = os.getenv('DB_PASS', 'Sigma#com13ti2025')
DB_HOST = os.getenv('DB_HOST', '177.153.209.166')
DB_NAME = os.getenv('DB_NAME', 'sigmacomti')
DB_CONN = f'mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS_RAW)}@{DB_HOST}:3306/{DB_NAME}?connect_timeout=60'

ID_EMPRESA = 1 # Ajuste se necessário

def listar_opcoes():
    print("🚀 Buscando opções no Bling...")
    
    # 1. Pega Token
    engine = create_engine(DB_CONN)
    with engine.connect() as conn:
        emp = conn.execute(text("SELECT client_id, client_secret, refresh_token FROM empresas_bling WHERE id = :id"), {'id': ID_EMPRESA}).mappings().first()
        creds = dict(emp)
        tokens = get_valid_token(creds)
        token = tokens['access_token']

    headers = {'Authorization': f'Bearer {token}'}

    # 2. Busca Contas Contábeis (Portadores)
    print("\n🏦 --- CONTAS / PORTADORES DISPONÍVEIS ---")
    url_contas = 'https://www.bling.com.br/Api/v3/contas-contabeis'
    r = requests.get(url_contas, headers=headers)
    
    if r.status_code == 200:
        contas = r.json().get('data', [])
        for c in contas:
            # Exibe ID e Nome para você copiar
            print(f"ID: {c['id']} | Nome: {c['descricao']}")
    else:
        print(f"Erro ao buscar contas: {r.status_code} - {r.text}")

    # 3. Busca Formas de Pagamento
    print("\n💳 --- FORMAS DE PAGAMENTO DISPONÍVEIS ---")
    url_formas = 'https://www.bling.com.br/Api/v3/formas-pagamentos'
    r = requests.get(url_formas, headers=headers)
    
    if r.status_code == 200:
        formas = r.json().get('data', [])
        for f in formas:
            print(f"ID: {f['id']} | Nome: {f['descricao']}")
    else:
        print(f"Erro ao buscar formas: {r.status_code} - {r.text}")

if __name__ == "__main__":
    listar_opcoes()