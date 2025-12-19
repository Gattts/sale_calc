import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import time

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILO
# ==============================================================================
st.set_page_config(page_title="Market Manager Pro", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important;
    }
    .stButton>button { 
        border-radius: 6px; font-weight: bold; height: 2.5em; padding: 0.2em 1em;
    }
    .result-card {
        background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px;
        padding: 15px; text-align: center; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .card-title { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .card-price { font-size: 24px; font-weight: 800; color: #1E88E5; margin: 0; line-height: 1.1; }
    .card-profit { font-size: 16px; font-weight: bold; color: #2E7D32; margin-top: 5px; }
    .card-footer { 
        margin-top: 8px; padding-top: 8px; border-top: 1px solid #ddd; 
        font-size: 13px; font-weight: 600; color: #333; 
        display: flex; justify-content: space-between;
    }
    /* Deixa os inputs mais compactos */
    div[data-testid="stTextInput"] input { font-size: 14px; }
    div[data-testid="stNumberInput"] input { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO E FUNÇÕES DO BANCO
# ==============================================================================
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")
    # Garante que a coluna PESO existe
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
            if params: return pd.read_sql(text(query), conn, params=params)
            return pd.read_sql(text(query), conn)
    except Exception as e:
        return pd.DataFrame()

def run_command(query, params):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Erro no Banco: {e}")
        return False

# ==============================================================================
# 3. LÓGICA DE NEGÓCIO
# ==============================================================================
TABELA_FRETE_ML = {
    "79-99": [(0.3, 11.97), (0.5, 12.87), (1.0, 13.47), (2.0, 14.07), (3.0, 14.97), (4.0, 16.17), (5.0, 17.07), (9.0, 26.67), (13.0, 39.57), (17.0, 44.07), (23.0, 51.57), (30.0, 59.37), (40.0, 61.17), (50.0, 63.27), (60.0, 67.47), (70.0, 72.27), (80.0, 75.57), (90.0, 83.97), (100.0, 95.97), (125.0, 107.37), (150.0, 113.97)],
    "100-119": [(0.3, 13.97), (0.5, 15.02), (1.0, 15.72), (2.0, 16.42), (3.0, 17.47), (4.0, 18.87), (5.0, 19.92), (9.0, 31.12), (13.0, 46.17), (17.0, 51.42), (23.0, 60.17), (30.0, 69.27), (40.0, 71.37), (50.0, 73.82), (60.0, 78.72), (70.0, 84.32), (80.0, 88.17), (90.0, 97.97), (100.0, 111.97), (125.0, 125.27)],
    "120-149": [(0.3, 15.96), (0.5, 17.16), (1.0, 17.96), (2.0, 18.76), (3.0, 19.96), (4.0, 21.56), (5.0, 22.76), (9.0, 35.56), (13.0, 52.76), (17.0, 58.76), (23.0, 68.76), (30.0, 79.16), (40.0, 81.56), (50.0, 84.36), (60.0, 89.96), (70.0, 96.36), (80.0, 100.76), (90.0, 111.96), (100.0, 127.96), (125.0, 143.16), (150.0, 151.96)],
    "150-199": [(0.3, 17.96), (0.5, 19.31), (1.0, 20.21), (2.0, 21.11), (3.0, 22.46), (4.0, 24.26), (5.0, 25.61), (9.0, 40.01), (13.0, 59.36), (17.0, 66.11), (23.0, 77.36), (30.0, 89.06), (40.0, 91.76), (50.0, 94.91), (60.0, 101.21), (70.0, 108.41), (80.0, 113.36), (90.0, 125.96), (100.0, 143.96), (125.0, 161.06)],
    "200+": [(0.3, 19.95), (0.5, 21.45), (1.0, 22.45), (2.0, 23.45), (3.0, 24.95), (4.0, 26.95), (5.0, 28.45), (9.0, 44.45), (13.0, 65.95), (17.0, 73.45), (23.0, 85.95), (30.0, 98.95), (40.0, 101.95), (50.0, 105.45), (60.0, 112.45), (70.0, 120.45), (80.0, 125.95), (90.0, 139.95), (100.0, 159.95), (125.0, 178.95), (150.0, 189.95)]
}

def calcular_custo_aquisicao(preco_compra, frete, ipi_pct, outros, st_val, icms_frete, icms_prod, pis_pct, cofins_pct, is_lucro_real):
    valor_ipi = preco_compra * (ipi_pct / 100)
    preco_medio = preco_compra + frete + valor_ipi + outros + st_val
    credito_icms = 0.0
    if is_lucro_real:
        c_icms_frete = frete * (icms_frete / 100)
        c_icms_prod = preco_compra * (icms_prod / 100)
        credito_icms = c_icms_frete + c_icms_prod
    
    # Créditos PIS/COFINS (simplificado)
    base_pis_cofins = preco_medio 
    if is_lucro_real:
        credito_pis = base_pis_cofins * (1.65 / 100)
        credito_cofins = base_pis_cofins * (7.60 / 100)
    else:
        credito_pis = 0
        credito_cofins = 0

    total_creditos = credito_icms + credito_pis + credito_cofins
    return {'custo_final': preco_medio - total_creditos, 'preco_medio': preco_medio, 'creditos': total_creditos, 'credito_icms': credito_icms, 'credito_pis': credito_pis, 'credito_cofins': credito_cofins}

def obter_taxa_fixa_ml(preco):
    if preco >= 79.00: return 0.00
    elif preco >= 50.00: return 6.75
    elif preco >= 29.00: return 6.50
    elif preco > 12.50: return 6.25
    else: return 0.50

def obter_frete_ml_tabela(preco, peso):
    if preco < 79.00: return 0.00
    faixa = "200+"
    if 79 <= preco < 100: faixa = "79-99"
    elif 100 <= preco < 120: faixa = "100-119"
    elif 120 <= preco < 150: faixa = "120-149"
    elif 150 <= preco < 200: faixa = "150-199"
    for limite, valor in TABELA_FRETE_ML[faixa]:
        if peso <= limite: return valor
    return TABELA_FRETE_ML[faixa][-1][1]

def calcular_cenario(margem_alvo, preco_manual, comissao, modo, canal, custo_final, impostos_venda, peso, is_full, armaz):
    icms = impostos_venda['icms']/100
    difal = impostos_venda['difal']/100
    pis, cofins = 0.0165, 0.0760
    
    taxa_imposto_total = icms + difal + ((1-icms) * (pis + cofins))
    perc_variaveis = taxa_imposto_total + (comissao/100) + (armaz/100 if not is_full else 0.0)
    
    frete, taxa_extra, custo_fixo_extra = 0.0, 0.0, 0.0
    if is_full: custo_fixo_extra += custo_final * (armaz/100)
    if "Shopee" in canal: taxa_extra += 4.00 
    
    preco = 0.0
    if modo == "preco":
        preco = preco_manual
        if "Mercado Livre" in canal:
            taxa_extra += obter_taxa_fixa_ml(preco)
            frete = obter_frete_ml_tabela(preco, peso)
    else:
        margem_decimal = margem_alvo / 100
        divisor = 1 - (perc_variaveis + margem_decimal)
        if divisor <= 0: divisor = 0.01 
        custos_base = custo_final + custo_fixo_extra + taxa_extra 

        if "Mercado Livre" in canal:
            frete_estimado = obter_frete_ml_tabela(100.0, peso) 
            preco_t1 = (custos_base + frete_estimado) / divisor
            frete_real = obter_frete_ml_tabela(preco_t1, peso)
            preco_final_t1 = (custos_base + frete_real) / divisor
            if preco_final_t1 >= 79.00:
                preco, frete = preco_final_t1, frete_real
            else:
                taxa_real = obter_taxa_fixa_ml((custos_base + 6.75) / divisor)
                preco = (custos_base + taxa_real) / divisor
                taxa_extra += taxa_real
                frete = 0.0
        else:
            preco = custos_base / divisor

    v_icms = preco * icms
    v_difal = preco * difal
    v_pis_cofins = preco * (1-icms) * (pis + cofins)
    v_comissao = preco * (comissao/100)
    v_armaz_var = preco * (armaz/100) if not is_full else 0.0
    
    repasse = preco - v_comissao - frete - taxa_extra
    lucro = repasse - (v_icms + v_difal + v_pis_cofins) - custo_final - v_armaz_var - custo_fixo_extra
    margem_real = (lucro / preco * 100) if preco > 0 else 0

    return {
        "preco": preco, "lucro": lucro, "margem": margem_real, "repasse": repasse, "frete": frete,
        "detalhes": {
            "venda_bruta": preco, "v_icms": v_icms, "icms_pct": impostos_venda['icms'],
            "v_difal": v_difal, "difal_pct": impostos_venda['difal'], "v_pis_cofins": v_pis_cofins,
            "v_comissao": v_comissao, "comissao_pct": comissao, "v_frete": frete,
            "v_taxa_fixa": taxa_extra, "v_armaz": v_armaz_var + custo_fixo_extra, "custo_produto": custo_final
        }
    }

def exibir_card_compacto(titulo, dados):
    st.markdown(f"""
    <div class="result-card">
        <div class="card-title">{titulo}</div>
        <div class="card-price">R$ {dados['preco']:.2f}</div>
        <div class="card-profit">Lucro: R$ {dados['lucro']:.2f} ({dados['margem']:.1f}%)</div>
        <div class="card-footer">
            <span>🚚 Frete: R$ {dados.get('frete', 0):.2f}</span>
            <span>🤝 Repasse: R$ {dados.get('repasse', 0):.2f}</span>
        </div>
    </div>""", unsafe_allow_html=True)
    d = dados['detalhes']
    with st.expander("🔎 Ver Extrato Detalhado"):
        tabela = [
            {"D": "➕ Venda", "V": f"R$ {d['venda_bruta']:,.2f}"},
            {"D": f"➖ ICMS ({d['icms_pct']:.1f}%)", "V": f"- R$ {d['v_icms']:,.2f}"},
            {"D": f"➖ DIFAL ({d['difal_pct']:.1f}%)", "V": f"- R$ {d['v_difal']:,.2f}"},
            {"D": "➖ PIS/COF", "V": f"- R$ {d['v_pis_cofins']:,.2f}"},
            {"D": f"➖ Mkt ({d['comissao_pct']:.1f}%)", "V": f"- R$ {d['v_comissao']:,.2f}"},
            {"D": "➖ Taxa Fixa", "V": f"- R$ {d['v_taxa_fixa']:,.2f}"},
            {"D": "➖ Frete", "V": f"- R$ {d['v_frete']:,.2f}"},
            {"D": "➖ Armaz/Full", "V": f"- R$ {d['v_armaz']:,.2f}"},
            {"D": "➖ Custo Prod", "V": f"- R$ {d['custo_produto']:,.2f}"},
            {"D": "✅ LUCRO", "V": f"R$ {dados['lucro']:,.2f}"}
        ]
        st.table(pd.DataFrame(tabela))

# ==============================================================================
# 4. COMPONENTES PERSONALIZADOS (RESOLUÇÃO DO INPUT)
# ==============================================================================
def input_dinheiro(label, key_state):
    """Cria um campo de texto que funciona como dinheiro (permite apagar)."""
    # 1. Recupera valor atual do estado (Float)
    valor_float = st.session_state.get(key_state, 0.0)
    
    # 2. Converte para string para exibir (vazio se for 0.0 e usuário estiver limpando)
    val_str = f"{valor_float:.2f}" if valor_float is not None else "0.00"
    
    # 3. Cria o widget de Texto (permite apagar tudo!)
    # Usamos uma chave interna única para o widget
    input_val = st.text_input(label, value=val_str, key=f"wid_{key_state}")
    
    # 4. Converte de volta para float e salva no estado
    try:
        # Troca virgula por ponto
        clean_val = input_val.replace(',', '.')
        if not clean_val: clean_val = "0.0"
        novo_float = float(clean_val)
    except:
        novo_float = 0.0
    
    st.session_state[key_state] = novo_float
    return novo_float

# ==============================================================================
# 5. GESTÃO DE ESTADO INICIAL
# ==============================================================================
# Garante que as variáveis existem antes de tudo
defaults = {
    'custo_final': 0.0, 'detalhes_custo': {}, 'prod_id_selecionado': None,
    'sb_canal': "Mercado Livre", 'sb_peso': 0.3, 'sb_icms': 18.0, 
    'sb_difal': 0.0, 'sb_armaz': 0.0, 'sb_full': False,
    # Inputs de cadastro
    'pc_cad': 0.0, 'fr_cad': 0.0, 'ipi_cad': 0.0, 'peso_cad': 0.0,
    'icmsp_cad': 12.0, 'icmsf_cad': 0.0, 'out_cad': 0.0, 'st_cad': 0.0
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ==============================================================================
# 6. ÁREA PRINCIPAL (TABS)
# ==============================================================================
tab1, tab2 = st.tabs(["🧮 Calculadora", "📝 Cadastro (DB)"])

with tab1:
    # Acesso direto às variáveis da Sidebar (que será renderizada depois)
    canal = st.session_state.sb_canal
    peso = st.session_state.sb_peso
    icms_val = st.session_state.sb_icms
    difal_val = st.session_state.sb_difal
    
    st.markdown(f"### 🏷️ Simulação: {canal}")
    if st.session_state.custo_final <= 0: st.warning("⚠️ Custo Base zerado. Vá em 'Cadastro' para definir.")

    tipo_calculo = st.radio("Objetivo:", ["🎯 Margem (%)", "💵 Preço Fixo (R$)"], horizontal=True)
    modo = "margem" if "Margem" in tipo_calculo else "preco"
    impostos = {'icms': icms_val, 'difal': difal_val}

    if "Mercado Livre" in canal:
        col_c, col_p = st.columns(2)
        with col_c:
            st.markdown("#### 🔹 Clássico")
            com_c = st.number_input("Comissão (%)", value=11.5, step=0.5, key="com_cla")
            marg_c = st.number_input("Margem (%)", value=15.0, step=0.5, key="marg_cla")
            if modo == "preco":
                pr_c = st.number_input("Preço (R$)", value=100.0, step=1.0, key="pr_cla")
                res_c = calcular_cenario(0, pr_c, com_c, "preco", canal, st.session_state.custo_final, impostos, peso, st.session_state.sb_full, st.session_state.sb_armaz)
            else:
                res_c = calcular_cenario(marg_c, 0, com_c, "margem", canal, st.session_state.custo_final, impostos, peso, st.session_state.sb_full, st.session_state.sb_armaz)
            exibir_card_compacto("Sugestão Clássico", res_c)

        with col_p:
            st.markdown("#### 🔸 Premium")
            com_p = st.number_input("Comissão (%)", value=16.5, step=0.5, key="com_pre")
            marg_p = st.number_input("Margem (%)", value=15.0, step=0.5, key="marg_pre")
            if modo == "preco":
                pr_p = st.number_input("Preço (R$)", value=110.0, step=1.0, key="pr_pre")
                res_p = calcular_cenario(0, pr_p, com_p, "preco", canal, st.session_state.custo_final, impostos, peso, st.session_state.sb_full, st.session_state.sb_armaz)
            else:
                res_p = calcular_cenario(marg_p, 0, com_p, "margem", canal, st.session_state.custo_final, impostos, peso, st.session_state.sb_full, st.session_state.sb_armaz)
            exibir_card_compacto("Sugestão Premium", res_p)
    else:
        col_u, _ = st.columns([1, 1])
        with col_u:
            st.markdown(f"#### 🛍️ {canal}")
            com_u = st.number_input("Comissão (%)", value=14.0, step=0.5, key="com_uni")
            marg_u = st.number_input("Margem (%)", value=15.0, step=0.5, key="marg_uni")
            if modo == "preco":
                pr_u = st.number_input("Preço (R$)", value=100.0, step=1.0, key="pr_uni")
                res_u = calcular_cenario(0, pr_u, com_u, "preco", canal, st.session_state.custo_final, impostos, peso, st.session_state.sb_full, st.session_state.sb_armaz)
            else:
                res_u = calcular_cenario(marg_u, 0, com_u, "margem", canal, st.session_state.custo_final, impostos, peso, st.session_state.sb_full, st.session_state.sb_armaz)
            exibir_card_compacto(f"Sugestão {canal}", res_u)

with tab2:
    st.markdown("### ☁️ Cadastro de Produtos")
    
    # Carrega lista do banco
    query_load = "SELECT id, sku, nome, fornecedor, preco_partida, ipi_percent, icms_percent, quantidade, nro_nf, peso FROM produtos ORDER BY nome ASC"
    df_prods = run_query(query_load)
    
    opcoes = ["✨ Novo Produto"]
    mapa = {}
    if not df_prods.empty:
        df_prods['label'] = df_prods['sku'] + " - " + df_prods['nome']
        for _, row in df_prods.iterrows():
            if row['label'] not in mapa:
                mapa[row['label']] = row
                opcoes.append(row['label'])

    sel = st.selectbox("🔍 Buscar no Banco:", options=opcoes)

    # Lógica de Carga dos Dados (Atualiza Session State)
    if sel != "✨ Novo Produto":
        if st.session_state.get('ultimo_prod_carregado') != sel:
            d = mapa[sel]
            st.session_state.prod_id_selecionado = d['id']
            st.session_state.update({
                'in_sku': str(d['sku']), 'in_nome': str(d['nome']),
                'in_forn': str(d['fornecedor']) if d['fornecedor'] else "",
                'in_nf': str(d['nro_nf']) if d['nro_nf'] else "",
                'in_qtd': int(d['quantidade']),
                # Atualiza Floats
                'pc_cad': float(d['preco_partida']), 
                'ipi_cad': float(d['ipi_percent']), 
                'icmsp_cad': float(d['icms_percent']),
                'peso_cad': float(d['peso']) if d['peso'] else 0.0,
                'sb_peso': float(d['peso']) if d['peso'] else 0.0, # Espelho
                'sb_icms': float(d['icms_percent']),               # Espelho
                'ultimo_prod_carregado': sel
            })
            st.toast(f"Carregado: {d['nome']}", icon="📂")
            time.sleep(0.1) # Breve pausa para garantir propagação
            st.rerun()
    else:
        if st.session_state.get('ultimo_prod_carregado') != "NOVO":
            st.session_state.prod_id_selecionado = None
            st.session_state['ultimo_prod_carregado'] = "NOVO"
            st.session_state.update({'pc_cad':0.0, 'peso_cad':0.0, 'in_sku':"", 'in_nome':""})
            st.rerun()

    # Formulário
    col_form, col_resumo = st.columns([0.80, 0.20])
    with col_form:
        with st.container(border=True):
            st.caption("1. Dados Principais")
            c1, c2, c3 = st.columns([1, 2, 2])
            sku_val = c1.text_input("SKU", key="in_sku")
            nome_val = c2.text_input("Nome", key="in_nome")
            forn_val = c3.text_input("Fornecedor", key="in_forn")

            st.caption("2. Entrada")
            c4, c5, c6 = st.columns([2, 1, 1], vertical_alignment="bottom")
            nf_val = c4.text_input("Nº NF", key="in_nf")
            qtd_val = c5.number_input("Qtd", min_value=1, key="in_qtd")
            l_real = c6.toggle("Lucro Real", True)

            st.caption("3. Custos Unitários & Logística")
            k1, k2, k3 = st.columns(3)
            # USANDO O NOVO INPUT HÍBRIDO (Text Input que salva como Float)
            # Isso resolve o problema de apagar o texto com backspace
            pc = input_dinheiro("Preço Compra (R$)", "pc_cad")
            frete = input_dinheiro("Frete Compra (R$)", "fr_cad")
            ipi = input_dinheiro("IPI (%)", "ipi_cad")
            
            k4, k5, k6 = st.columns(3)
            peso_prod = input_dinheiro("Peso (Kg)", "peso_cad")
            icms_prod = input_dinheiro("ICMS Prod(%)", "icmsp_cad")
            icms_frete = input_dinheiro("ICMS Frete(%)", "icmsf_cad")
            
            k7, k8, k9 = st.columns(3)
            outros = input_dinheiro("Outros (R$)", "out_cad")
            st_val = input_dinheiro("ST (R$)", "st_cad")
            
            st.write("")
            b1, b2, b3 = st.columns([1, 2, 2], vertical_alignment="bottom")
            
            if b1.button("🔄 Calcular", use_container_width=True):
                res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                st.session_state.custo_final = res['custo_final']
                st.session_state.detalhes_custo = res
                st.rerun()

            if b2.button("💾 Salvar Novo", type="primary", use_container_width=True):
                if sku_val and nome_val:
                    res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                    sql = """INSERT INTO produtos (sku, nome, fornecedor, nro_nf, quantidade, preco_partida, ipi_percent, icms_percent, preco_final, peso, data_compra) 
                             VALUES (:sku, :nome, :forn, :nf, :qtd, :pp, :ipi, :icms, :pf, :peso, :dt)"""
                    params = {"sku": sku_val, "nome": nome_val, "forn": forn_val, "nf": nf_val, "qtd": qtd_val, "pp": pc, "ipi": ipi, "icms": icms_prod, "pf": res['custo_final'], "peso": peso_prod, "dt": date.today()}
                    if run_command(sql, params):
                        st.toast("Salvo!", icon="☁️")
                        time.sleep(1)
                        st.rerun()

            if st.session_state.prod_id_selecionado:
                if b3.button("✏️ Atualizar", use_container_width=True):
                    res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                    sql = """UPDATE produtos SET sku=:sku, nome=:nome, fornecedor=:forn, nro_nf=:nf, quantidade=:qtd, 
                             preco_partida=:pp, ipi_percent=:ipi, icms_percent=:icms, preco_final=:pf, peso=:peso WHERE id=:id"""
                    params = {"sku": sku_val, "nome": nome_val, "forn": forn_val, "nf": nf_val, "qtd": qtd_val, "pp": pc, "ipi": ipi, "icms": icms_prod, "pf": res['custo_final'], "peso": peso_prod, "id": st.session_state.prod_id_selecionado}
                    if run_command(sql, params):
                        st.toast("Atualizado!", icon="🔄")
                        time.sleep(1)
                        st.rerun()

    with col_resumo:
        if st.session_state.custo_final > 0:
            d = st.session_state.detalhes_custo
            with st.container(border=True):
                st.caption("Resumo")
                st.markdown(f'<div class="card-price" style="font-size: 20px;">R$ {d.get("custo_final", 0):.2f}</div>', unsafe_allow_html=True)
                st.caption("Custo Final Unitário")
                st.divider()
                st.write(f"**ICMS Rec:** R$ {d.get('credito_icms', 0):.2f}")
                st.write(f"**PIS/COF:** R$ {d.get('credito_pis', 0) + d.get('credito_cofins', 0):.2f}")
                st.success(f"**Total Créditos:** R$ {d.get('creditos', 0):.2f}")

# ==============================================================================
# 7. SIDEBAR (RENDERIZADA NO FINAL)
# ==============================================================================
with st.sidebar:
    st.title("🚀 Market Manager")
    st.markdown("---")
    st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"], key="sb_canal")
    
    with st.expander("🛠️ Parâmetros & Tributos", expanded=True):
        c1, c2 = st.columns(2)
        # Inputs que leem do session state (espelhamento) e salvam nele
        st.number_input("ICMS (%)", min_value=0.0, max_value=100.0, step=0.5, key="sb_icms")
        st.number_input("DIFAL (%)", min_value=0.0, max_value=100.0, step=0.5, key="sb_difal")
        
        c3, c4 = st.columns(2)
        st.number_input("Peso (Kg)", min_value=0.0, step=0.1, key="sb_peso")
        st.number_input("Armaz. (%)", min_value=0.0, step=0.5, key="sb_armaz")
        st.toggle("⚡ Full Fulfillment", key="sb_full")

    st.markdown("---")
    st.info(f"💰 Custo Base: **R$ {st.session_state.custo_final:,.2f}**")
