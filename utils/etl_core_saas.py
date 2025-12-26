import requests
import pandas as pd
from sqlalchemy import create_engine, text
import base64
import time
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import re

# --- LOGGING ---
def log(msg, empresa_id):
    print(f"\r{' ' * 100}\r", end='') 
    prefix = f"[{datetime.now().strftime('%H:%M:%S')}][Empresa {empresa_id}]"
    print(f"{prefix} {msg}")

# --- CARREGADORES DINÂMICOS ---
def carregar_lojas_do_banco(engine, empresa_id):
    try:
        with engine.connect() as conn:
            sql = text("SELECT id_loja_bling, nome_loja FROM empresas_lojas WHERE empresa_id = :id")
            res = conn.execute(sql, {'id': empresa_id}).fetchall()
            return {str(row[0]): row[1] for row in res}
    except: return {}

def carregar_mapa_situacoes_dict(engine, empresa_id):
    try:
        with engine.connect() as conn:
            sql = text("SELECT id_situacao_bling, nome_situacao FROM empresas_situacoes WHERE empresa_id = :id")
            res = conn.execute(sql, {'id': empresa_id}).fetchall()
            return {row[0]: row[1] for row in res}
    except: return {}

def carregar_situacoes_do_banco(engine, empresa_id):
    lista, pesados = [], []
    try:
        with engine.connect() as conn:
            sql = text("SELECT id_situacao_bling, nome_situacao, e_pesado FROM empresas_situacoes WHERE empresa_id = :id")
            res = conn.execute(sql, {'id': empresa_id}).fetchall()
            for row in res:
                lista.append({'id': row[0], 'nome': row[1]})
                if row[2] == 1: pesados.append(row[0])
        return lista, pesados
    except: return [], []

def carregar_mapa_nfe_db(engine):
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT id_situacao, nome_situacao FROM dominio_situacoes_nfe")).fetchall()
            return {row[0]: row[1] for row in res}
    except: return {}

def get_valid_token(creds):
    b64 = base64.b64encode(f"{creds['client_id']}:{creds['client_secret']}".encode()).decode()
    headers = {'Authorization': f'Basic {b64}', 'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        resp = requests.post('https://www.bling.com.br/Api/v3/oauth/token', headers=headers, data={'grant_type': 'refresh_token', 'refresh_token': creds['refresh_token']}, timeout=10)
        if resp.status_code == 200: return resp.json()
    except: pass
    return None

def listar_lojas_da_conta(token, empresa_id, mapa_banco):
    mapa_api = {}
    try:
        page = 1
        while True:
            resp = requests.get(f'https://www.bling.com.br/Api/v3/lojas?page={page}&limit=100', headers={'Authorization': f'Bearer {token}'}, timeout=10)
            if resp.status_code != 200: break
            dados = resp.json().get('data', [])
            if not dados: break
            for l in dados: mapa_api[str(l['id'])] = l['nome']
            page += 1
    except: pass
    mapa_final = mapa_api.copy()
    if mapa_banco:
        for k, v in mapa_banco.items(): mapa_final[k] = v
    log(f"🏪 Lojas mapeadas: {len(mapa_final)}.", empresa_id)
    return mapa_final

def listar_naturezas_da_conta(token, empresa_id):
    mapa_naturezas = {}
    try:
        url = 'https://www.bling.com.br/Api/v3/naturezas-operacoes?limit=100'
        resp = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=10)
        if resp.status_code == 200:
            dados = resp.json().get('data', [])
            for n in dados:
                mapa_naturezas[str(n['id'])] = n['descricao']
        log(f"📋 Naturezas mapeadas: {len(mapa_naturezas)}.", empresa_id)
    except: 
        log("⚠️ Falha ao mapear naturezas.", empresa_id)
    return mapa_naturezas

# ==============================================================================
# MÓDULO NFE 
# ==============================================================================
def ler_impostos_xml(url_xml):
    try:
        h = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url_xml, headers=h, timeout=15)
        if r.status_code != 200: return None
        xml_text = r.text.replace(' xmlns="http://www.portalfiscal.inf.br/nfe"', '')
        root = ET.fromstring(xml_text)
        total = root.find('.//ICMSTot')
        nat_node = root.find('.//natOp')
        natureza = nat_node.text if nat_node is not None else None
        if total is None: return {'impostos': None, 'natureza': natureza}
        impostos = {
            'icms': float(total.find('vICMS').text or 0),
            'pis': float(total.find('vPIS').text or 0),
            'cofins': float(total.find('vCOFINS').text or 0),
            'ipi': float(total.find('vIPI').text or 0),
            'difal': float(total.find('vICMSUFDest').text or 0)
        }
        return {'impostos': impostos, 'natureza': natureza}
    except: return None

def buscar_detalhe_nfe(id_nota, token):
    for _ in range(3):
        try:
            r = requests.get(f'https://www.bling.com.br/Api/v3/nfe/{id_nota}', headers={'Authorization': f'Bearer {token}'}, timeout=15)
            if r.status_code == 200: d = r.json().get('data'); return d[0] if isinstance(d, list) else d
            elif r.status_code == 429: time.sleep(1)
        except: pass
        time.sleep(0.3)
    return None

def extrair_valor_texto(texto, padrao):
    if not texto: return 0.0
    match = re.search(padrao + r"\s?R?\$?\s?([\d\.,]+)", texto, re.IGNORECASE)
    if match:
        try: return float(match.group(1).replace('.', '').replace(',', '.'))
        except: return 0.0
    return 0.0

def salvar_lote_nfe(empresa_id, lote_nfe, engine):
    if not lote_nfe: return
    df = pd.DataFrame(lote_nfe)
    df['empresa_id'] = empresa_id
    for _ in range(3):
        try:
            # ALTERADO PARA CONNECTION EXPLÍCITA COM COMMIT
            with engine.connect() as conn:
                df.to_sql('temp_nfe', conn, if_exists='replace', index=False)
                conn.execute(text("""
                    INSERT INTO notas_fiscais (
                        empresa_id, id, numero, serie, data_emissao, valor_nota, 
                        situacao, tipo, chave_acesso, xml_link, numero_pedido_loja,
                        nome_cliente, uf_destino, natureza_operacao,
                        valor_icms, valor_pis, valor_cofins, valor_ipi, valor_difal
                    )
                    SELECT 
                        empresa_id, id, numero, serie, data_emissao, valor_nota, 
                        situacao, tipo, chave_acesso, xml_link, numero_pedido_loja,
                        nome_cliente, uf_destino, natureza_operacao,
                        valor_icms, valor_pis, valor_cofins, valor_ipi, valor_difal
                    FROM temp_nfe
                    ON DUPLICATE KEY UPDATE
                        situacao=VALUES(situacao), tipo=VALUES(tipo), valor_nota=VALUES(valor_nota), 
                        numero_pedido_loja=VALUES(numero_pedido_loja),
                        natureza_operacao=VALUES(natureza_operacao),
                        valor_icms=VALUES(valor_icms), valor_pis=VALUES(valor_pis),
                        valor_cofins=VALUES(valor_cofins), valor_ipi=VALUES(valor_ipi),
                        valor_difal=VALUES(valor_difal), updated_at=NOW()
                """))
                conn.execute(text("DROP TABLE temp_nfe"))
                conn.commit() # <--- FORÇA O SALVAMENTO IMEDIATO
            break
        except Exception: time.sleep(1)

def processar_lista_nfe(dados_api, token, engine, empresa_id, ids_vistos, mapa_nfe_db, mapa_naturezas={}):
    lote_nfe = []
    for r in dados_api:
        if r['id'] in ids_vistos: continue
        if str(r.get('tipo', '1')) in ['0', 'E', 'e']: continue 
        
        n = buscar_detalhe_nfe(r['id'], token)
        if not n: continue
        
        raw_tipo = str(n.get('tipo', '1'))
        if raw_tipo in ['0', 'E', 'e']: continue
        else: tipo_final = 'S'
        
        ids_vistos.add(n['id'])
        
        raw_sit = n.get('situacao')
        if isinstance(raw_sit, int): situacao_str = mapa_nfe_db.get(raw_sit, str(raw_sit))
        elif isinstance(raw_sit, dict): situacao_str = str(raw_sit.get('valor', raw_sit.get('id', '')))
        else: situacao_str = str(raw_sit)

        impostos = {'icms': 0.0, 'pis': 0.0, 'cofins': 0.0, 'ipi': 0.0, 'difal': 0.0}
        
        id_nat = str(n.get('naturezaOperacao', {}).get('id', ''))
        natureza_op = mapa_naturezas.get(id_nat, id_nat)
        
        xml_link = n.get('xml')
        xml_data = ler_impostos_xml(xml_link) if xml_link else None
        
        if xml_data:
            if xml_data.get('impostos'): impostos = xml_data['impostos']
            if xml_data.get('natureza'): natureza_op = xml_data['natureza']
        else:
            obs = n.get('informacoesComplementares', '') + " " + n.get('observacoes', '')
            impostos['difal'] = extrair_valor_texto(obs, r"DIFAL da UF destino")
            for item in n.get('itens', []):
                imp = item.get('impostos', {})
                if 'icms' in imp: impostos['icms'] += float(imp['icms'].get('valor', 0))
                if 'pis' in imp: impostos['pis'] += float(imp['pis'].get('valor', 0))
                if 'cofins' in imp: impostos['cofins'] += float(imp['cofins'].get('valor', 0))
                if 'ipi' in imp: impostos['ipi'] += float(imp['ipi'].get('valor', 0))

        lote_nfe.append({
            'id': n['id'], 'numero': str(n.get('numero')), 'serie': str(n.get('serie')),
            'data_emissao': n.get('dataEmissao'), 'valor_nota': float(n.get('valorNota', 0)),
            'situacao': situacao_str, 'tipo': tipo_final,
            'chave_acesso': n.get('chaveAcesso'), 'xml_link': n.get('xml'),
            'numero_pedido_loja': str(n.get('numeroPedidoLoja', '')),
            'nome_cliente': n.get('contato', {}).get('nome'), 'uf_destino': n.get('contato', {}).get('endereco', {}).get('uf'),
            'natureza_operacao': natureza_op,
            'valor_icms': impostos['icms'], 'valor_pis': impostos['pis'], 'valor_cofins': impostos['cofins'],
            'valor_ipi': impostos['ipi'], 'valor_difal': impostos['difal']
        })
    if lote_nfe: salvar_lote_nfe(empresa_id, lote_nfe, engine)
    return len(lote_nfe)

def worker_nfe_recursivo(token, engine, empresa_id, ts_ini, ts_fim, data_alvo, ids_vistos, mapa_nfe_db, mapa_naturezas, tipo_filtro='S'):
    url = f'https://www.bling.com.br/Api/v3/nfe?page=1&limit=100&dataEmissaoInicial={ts_ini}&dataEmissaoFinal={ts_fim}&tipo={tipo_filtro}'
    dados = []
    for _ in range(3):
        try:
            r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=20)
            if r.status_code == 200: dados = r.json().get('data', []); break
            elif r.status_code == 429: time.sleep(2)
        except: time.sleep(1)
    qtd = len(dados)
    dt_ini = datetime.strptime(ts_ini, "%Y-%m-%d %H:%M:%S")
    dt_fim = datetime.strptime(ts_fim, "%Y-%m-%d %H:%M:%S")
    diff_min = (dt_fim - dt_ini).total_seconds() / 60
    
    if qtd < 100 or diff_min < 10:
        validos = [x for x in dados if x['dataEmissao'].startswith(data_alvo)]
        if validos:
            print(f"      📄 NFe ({tipo_filtro}) {ts_ini.split(' ')[1][:5]}: Baixando {len(validos)}...", end='\r')
            return processar_lista_nfe(validos, token, engine, empresa_id, ids_vistos, mapa_nfe_db, mapa_naturezas)
        return 0
    
    meio = dt_ini + (dt_fim - dt_ini) / 2
    return worker_nfe_recursivo(token, engine, empresa_id, ts_ini, meio.strftime("%Y-%m-%d %H:%M:%S"), data_alvo, ids_vistos, mapa_nfe_db, mapa_naturezas, tipo_filtro) + \
           worker_nfe_recursivo(token, engine, empresa_id, (meio+timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"), ts_fim, data_alvo, ids_vistos, mapa_nfe_db, mapa_naturezas, tipo_filtro)

# --- PEDIDOS E DEMAIS FUNÇÕES ---
def buscar_detalhe_pedido(id_pedido, token):
    for _ in range(3):
        try:
            r = requests.get(f'https://www.bling.com.br/Api/v3/pedidos/vendas/{id_pedido}', headers={'Authorization': f'Bearer {token}'}, timeout=15)
            if r.status_code == 200: d = r.json().get('data'); return d[0] if isinstance(d, list) else d
            elif r.status_code == 429: time.sleep(1)
        except: pass
    return None

def salvar_lote_pedidos(empresa_id, lote_p, lote_i, engine, ids_lote):
    if not lote_p: return
    
    # Prepara DataFrames
    df_p = pd.DataFrame(lote_p)
    df_i = pd.DataFrame(lote_i)
    df_p['empresa_id'] = empresa_id
    
    # Se tiver itens, garante que tem empresa_id e remove coluna 'id' se vier suja da API
    if not df_i.empty:
        df_i['empresa_id'] = empresa_id
        if 'id' in df_i.columns:
            df_i = df_i.drop(columns=['id']) # Deixa o banco gerar o ID do item
    
    for _ in range(3):
        try:
            with engine.connect() as conn:
                # 1. Salva/Atualiza Pedido Pai
                df_p.to_sql('temp_etl_pedidos', conn, if_exists='replace', index=False)
                
                conn.execute(text("""
                    INSERT INTO pedidos_vendas 
                    (empresa_id, id, numero, numero_pedido_loja, data, id_loja, nome_loja, total, valor_frete, taxa_marketplace, valor_liquido, situacao, id_situacao)
                    SELECT 
                    empresa_id, id, numero, numero_pedido_loja, data, id_loja, nome_loja, total, valor_frete, taxa_marketplace, valor_liquido, situacao, id_situacao 
                    FROM temp_etl_pedidos
                    ON DUPLICATE KEY UPDATE 
                        total=VALUES(total), 
                        situacao=VALUES(situacao), 
                        id_situacao=VALUES(id_situacao), 
                        updated_at=NOW()
                """))
                conn.execute(text("DROP TABLE temp_etl_pedidos"))
                
                # Commit do pai para garantir integridade
                conn.commit()

                # 2. Substitui os Itens
                if not df_i.empty:
                    # Deleta itens antigos desse lote de pedidos
                    ids_str = ','.join(map(str, ids_lote))
                    conn.execute(text(f"DELETE FROM pedidos_itens WHERE empresa_id = {empresa_id} AND pedido_id IN ({ids_str})"))
                    
                    # Insere os novos
                    df_i.to_sql('pedidos_itens', conn, if_exists='append', index=False)
                    
                    conn.commit()
            
            # Se chegou aqui, deu tudo certo
            break
            
        except Exception as e:
            print(f"\n❌ Erro ao salvar lote (Tentativa {_ + 1}): {e}")
            time.sleep(1)

def processar_lista_pedidos(dados_api, token, engine, empresa_id, situacao_obj, mapa_lojas, ids_vistos_global, mapa_nfe_db=None, mapa_naturezas={}, mapa_situacoes_db={}):
    lote_p, lote_i, ids_proc = [], [], []
    batch_notas_para_baixar = []

    for r in dados_api:
        if r['id'] in ids_vistos_global: continue
        p = buscar_detalhe_pedido(r['id'], token)
        if not p: continue
        ids_proc.append(p['id']); ids_vistos_global.add(p['id'])
        
        # --- 1. RESOLUÇÃO INTELIGENTE DE VALORES ---
        tot = float(p.get('total', 0))
        tax = p.get('taxas', {})
        val_com = float(tax.get('taxaComissao', 0))
        val_frete = float(tax.get('custoFrete', 0))
        if val_frete == 0:
            val_frete = float(p.get('transporte', {}).get('frete', 0))
        liq = tot - val_com - val_frete

        # --- 2. RESOLUÇÃO INTELIGENTE DE STATUS ---
        id_sit_api = p.get('situacao', {}).get('id')
        nome_sit_api = p.get('situacao', {}).get('valor')
        
        if id_sit_api in mapa_situacoes_db:
            sit_nome = mapa_situacoes_db[id_sit_api]
            sit_id = id_sit_api
        else:
            sit_nome = nome_sit_api if nome_sit_api else situacao_obj.get('nome', 'Indefinido')
            sit_id = id_sit_api if id_sit_api else situacao_obj.get('id', 0)

        id_loja = p.get('loja', {}).get('id')
        nome_loja = mapa_lojas.get(str(id_loja), f"Loja {id_loja}")
        num_ext = str(p.get('numeroLoja', ''))
        
        lote_p.append({
            'id': p['id'], 'numero': str(p.get('numero')), 'numero_pedido_loja': num_ext, 
            'data': p['data'], 'id_loja': id_loja, 'nome_loja': nome_loja, 
            'total': tot, 'valor_frete': val_frete, 'taxa_marketplace': val_com, 
            'valor_liquido': liq, 
            'situacao': sit_nome, 
            'id_situacao': sit_id
        })
        
        for i in p.get('itens', []):
            lote_i.append({
                'pedido_id': p['id'],
                'codigo_produto': str(i.get('codigo')),
                'descricao': i.get('descricao'),
                'quantidade': float(i.get('quantidade', 0)),
                'valor_unitario': float(i.get('valor', 0)),
                'total_item': float(i.get('quantidade', 0)) * float(i.get('valor', 0)),
                'numero_pedido': str(p.get('numero')),
                'data_pedido': p['data'],
                'situacao': sit_nome,
                'id_contato': p.get('contato', {}).get('id'),
                'id_loja': id_loja,
                'nome_loja': nome_loja,
                'total_pedido': tot,
                'valor_frete': val_frete,
                'taxa_marketplace': val_com,
                'valor_liquido': liq,
                'id_situacao': sit_id,
                'numero_pedido_loja': num_ext
            })

        if mapa_nfe_db is not None and 'notas' in p:
            for nota in p['notas']:
                if 'id' in nota:
                    batch_notas_para_baixar.append({'id': nota['id']})

    if lote_p: salvar_lote_pedidos(empresa_id, lote_p, lote_i, engine, ids_proc)
    
    if batch_notas_para_baixar and mapa_nfe_db is not None:
        processar_lista_nfe(batch_notas_para_baixar, token, engine, empresa_id, set(), mapa_nfe_db, mapa_naturezas)
    
    return len(lote_p)

# ... (Funções Recursivas e Executor ficam iguais, só lembre de passar o mapa novo se usar o Executor) ...

def processar_tempo_recursivo_global(token, engine, empresa_id, situacao_obj, ts_ini, ts_fim, mapa_lojas, data_alvo, ids_vistos_global):
    url = f'https://www.bling.com.br/Api/v3/pedidos/vendas?page=1&limit=100&dataAlteracaoInicial={ts_ini}&dataAlteracaoFinal={ts_fim}&idsSituacoes[]={situacao_obj["id"]}'
    dados = []
    for _ in range(3):
        try:
            resp = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=20)
            if resp.status_code == 200: dados = resp.json().get('data', []); break
            elif resp.status_code == 429: time.sleep(2)
        except: time.sleep(1)
    qtd = len(dados)
    dt_ini = datetime.strptime(ts_ini, "%Y-%m-%d %H:%M:%S")
    dt_fim = datetime.strptime(ts_fim, "%Y-%m-%d %H:%M:%S")
    diff_min = (dt_fim - dt_ini).total_seconds() / 60
    if qtd < 100 or diff_min < 5:
        if qtd > 0:
            validos = [p for p in dados if p['data'] == data_alvo]
            if validos:
                hora_show = ts_ini.split(' ')[1][:5]
                print(f"      ⚡ Pedidos {hora_show}: Baixando {len(validos)}...", end='\r')
                return processar_lista_pedidos(validos, token, engine, empresa_id, situacao_obj, mapa_lojas, ids_vistos_global)
        return 0
    meio = dt_ini + (dt_fim - dt_ini) / 2
    return processar_tempo_recursivo_global(token, engine, empresa_id, situacao_obj, ts_ini, meio.strftime("%Y-%m-%d %H:%M:%S"), mapa_lojas, data_alvo, ids_vistos_global) + \
           processar_tempo_recursivo_global(token, engine, empresa_id, situacao_obj, (meio+timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"), ts_fim, mapa_lojas, data_alvo, ids_vistos_global)

def processar_status_pedidos(token, engine, empresa_id, situacao, data_alvo, mapa_lojas, ids_pesados):
    id_sit = situacao['id']; nome_sit = situacao['nome']
    usar_recursivo = id_sit in ids_pesados
    ids_vistos = set()
    if not usar_recursivo:
        log(f"🔎 Varrendo '{nome_sit}'...", empresa_id)
        page = 1; ultimo_id = None
        while True:
            url = f'https://www.bling.com.br/Api/v3/pedidos/vendas?page={page}&limit=100&dataInclusaoInicial={data_alvo}&idsSituacoes[]={id_sit}'
            try:
                r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=15)
                if r.status_code == 429: time.sleep(2); continue
                dados = r.json().get('data', [])
                if not dados: break 
                if dados[0]['id'] == ultimo_id: log(f"⚠️ Loop. Ativando Recursivo.", empresa_id); usar_recursivo = True; break
                ultimo_id = dados[0]['id']
                if dados[-1]['data'] < data_alvo:
                    processar_lista_pedidos([p for p in dados if p['data'] == data_alvo], token, engine, empresa_id, situacao, mapa_lojas, ids_vistos); break 
                processar_lista_pedidos([p for p in dados if p['data'] == data_alvo], token, engine, empresa_id, situacao, mapa_lojas, ids_vistos)
                page += 1
            except: break
    if usar_recursivo:
        log(f"⚔️ Recursivo Global (48h) em '{nome_sit}'...", empresa_id)
        dias = [data_alvo, (datetime.strptime(data_alvo, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')]
        for dia in dias:
            processar_tempo_recursivo_global(token, engine, empresa_id, situacao, f"{dia} 00:00:00", f"{dia} 23:59:59", mapa_lojas, data_alvo, ids_vistos)
    return len(ids_vistos)

def tapar_buracos_sequenciais(engine, empresa_id, token, data_alvo, mapa_lojas):
    try:
        with engine.connect() as conn:
            sql = f"SELECT CAST(numero AS UNSIGNED) as num FROM pedidos_vendas WHERE data = '{data_alvo}' AND empresa_id = {empresa_id} AND numero REGEXP '^[0-9]+$'"
            res = conn.execute(text(sql)).fetchall()
            if not res: return
            numeros_db = sorted([row[0] for row in res])
            min_id, max_id = min(numeros_db), max(numeros_db)
            ja_temos = set(numeros_db)
            todos_teoricos = set(range(min_id, max_id + 1))
            faltantes = list(todos_teoricos - ja_temos)
            if not faltantes: return
            log(f"🔧 Auto-Healing: Buscando {len(faltantes)} pedidos perdidos...", empresa_id)
            cnt_recup = 0
            for num in faltantes:
                try:
                    r = requests.get(f'https://www.bling.com.br/Api/v3/pedidos/vendas?numero={num}', headers={'Authorization': f'Bearer {token}'}, timeout=5)
                    if r.status_code == 200:
                        d = r.json().get('data', [])
                        if d and d[0]['data'] == data_alvo:
                            sit_fake = {'id': d[0]['situacao']['id'], 'nome': 'Resgatado Auto'}
                            processar_lista_pedidos(d, token, engine, empresa_id, sit_fake, mapa_lojas, set())
                            cnt_recup += 1
                except: pass
            if cnt_recup > 0: print(f"      ✅ Recuperados: {cnt_recup}")
    except: pass

salvar_lote = salvar_lote_pedidos
buscar_detalhe_financeiro = buscar_detalhe_pedido
corrigir_vinculos_sql = lambda *args: None

def executar_etl_empresa(empresa_id, creds_dict, engine, data_alvo=None):
    if not data_alvo: data_alvo = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    log(f"Iniciando ETL Completo. Alvo: {data_alvo}", empresa_id)
    tokens = get_valid_token(creds_dict)
    if not tokens: return False, None
    token = tokens['access_token']
    
    mapa_lojas = listar_lojas_da_conta(token, empresa_id, carregar_lojas_do_banco(engine, empresa_id))
    sits, pesados = carregar_situacoes_do_banco(engine, empresa_id)
    mapa_nfe_db = carregar_mapa_nfe_db(engine)
    
    # NOVO: Carrega o mapa de naturezas
    mapa_naturezas = listar_naturezas_da_conta(token, empresa_id)

    tot_ped = 0
    for s in sits: 
        tot_ped += processar_status_pedidos(token, engine, empresa_id, s, data_alvo, mapa_lojas, pesados)
    
    tapar_buracos_sequenciais(engine, empresa_id, token, data_alvo, mapa_lojas)
    print("")

    log("--- PROCESSANDO NOTAS SAÍDA ---", empresa_id)
    # Agora passamos mapa_naturezas para o worker
    tot_nfe = worker_nfe_recursivo(token, engine, empresa_id, f"{data_alvo} 00:00:00", f"{data_alvo} 23:59:59", data_alvo, set(), mapa_nfe_db, mapa_naturezas, tipo_filtro='S')
    print("")
    
    log(f"SUCESSO. Pedidos: {tot_ped} | Notas Saída: {tot_nfe}", empresa_id)
    return True, tokens['refresh_token']
