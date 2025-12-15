import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import time

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILO (CSS AJUSTADO)
# ==============================================================================
st.set_page_config(page_title="Market Manager Pro", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    /* 1. Ajuste do Topo */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* 2. Botões */
    .stButton>button { border-radius: 8px; font-weight: bold; }
    
    /* 3. Cards de Resultado */
    .result-card {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .card-title { 
        font-size: 14px; 
        color: #666; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        margin-bottom: 5px; 
    }
    .card-price { 
        font-size: 26px; 
        font-weight: 800; 
        color: #1E88E5; 
        margin: 0; 
        line-height: 1.2; 
    }
    .card-profit { 
        font-size: 20px; 
        font-weight: bold; 
        color: #2E7D32; 
        margin-top: 5px; 
    }
    /* 4. Rodapé do Card (Frete e Repasse - AUMENTADO) */
    .card-footer { 
        margin-top: 12px; 
        padding-top: 12px; 
        border-top: 1px solid #ddd; 
        font-size: 16px; /* Aumentado de 13px para 16px */
        font-weight: 600; /* Mais destaque */
        color: #333; 
        display: flex; 
        justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO COM BANCO (AWS)
# ==============================================================================
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

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

def input_float(label, value, key):
    if key in st.session_state: st.session_state[key] = str(st.session_state[key])
    val_str = st.text_input(label, value=str(value), key=key)
    val_limpo = val_str.replace(',', '.').strip()
    try: return float(val_limpo) if val_limpo else 0.0
    except: return 0.0

def calcular_custo_aquisicao(preco_compra, frete, ipi_pct, outros, st_val, icms_frete, icms_prod, pis_pct, cofins_pct, is_lucro_real):
    valor_ipi = preco_compra * (ipi_pct / 100)
    preco_medio = preco_compra + frete + valor_ipi + outros + st_val
    credito_icms, credito_pis, credito_cofins = 0.0, 0.0, 0.0
    if is_lucro_real:
        c_icms_frete = frete * (icms_frete / 100)
        c_icms_prod = preco_compra * (icms_prod / 100)
        credito_icms = c_icms_frete + c_icms_prod
        base_pis_cofins = max(0, (preco_compra - c_icms_prod) + (frete - c_icms_frete))
        credito_pis = base_pis_cofins * (pis_pct / 100)
        credito_cofins = base_pis_cofins * (cofins_pct / 100)
    
    total_creditos = credito_icms + credito_pis + credito_cofins
    return {'custo_final': preco_medio - total_creditos, 'preco_medio': preco_medio, 'creditos': total_creditos, 'credito_icms': credito_icms, 'credito_pis': credito_pis, 'credito_cofins': credito_cofins}

def obter_frete_ml(preco, peso):
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
    icms, difal = impostos_venda['icms']/100, impostos_venda['difal']/100
    pis, cofins = 0.0165, 0.0760
    taxa_imposto_total = icms + difal + ((1-icms) * (pis + cofins))
    frete, taxa_extra, custo_fixo_extra, taxa_var_extra = 0.0, 0.0, 0.0, 0.0
    
    if is_full: custo_fixo_extra += custo_final * (armaz/100)
    else: taxa_var_extra += armaz

    if "Shopee" in canal: taxa_extra += 4.00
    elif "Mercado Livre" in canal:
        if modo == "preco": frete = obter_frete_ml(preco_manual, peso)
        else: frete = obter_frete_ml(custo_final * 1.5, peso)

    if modo == "margem":
        divisor = 1 - (taxa_imposto_total + (comissao/100) + (taxa_var_extra/100) + (margem_alvo/100))
        numerador = custo_final + frete + taxa_extra + custo_fixo_extra
        preco = numerador / max(divisor, 0.01)
        if "Mercado Livre" in canal:
            frete_real = obter_frete_ml(preco, peso)
            if frete_real != frete:
                preco = (custo_final + frete_real + taxa_extra + custo_fixo_extra) / max(divisor, 0.01)
                frete = frete_real
        margem_real = margem_alvo
    else:
        preco = preco_manual
        custos = (preco * (taxa_imposto_total + comissao/100 + taxa_var_extra/100)) + frete + taxa_extra + custo_final + custo_fixo_extra
        margem_real = ((preco - custos) / preco * 100) if preco > 0 else 0

    val_mkt = (preco * comissao/100) + frete + taxa_extra
    lucro = preco * (1 - taxa_imposto_total) - val_mkt - custo_final - custo_fixo_extra
    return {"preco": preco, "lucro": lucro, "margem": margem_real, "repasse": preco - val_mkt, "frete": frete}

def exibir_card_compacto(titulo, dados):
    """Renderiza o card HTML compacto com fontes ajustadas"""
    html = f"""
    <div class="result-card">
        <div class="card-title">{titulo}</div>
        <div class="card-price">R$ {dados['preco']:.2f}</div>
        <div class="card-profit">Lucro: R$ {dados['lucro']:.2f} ({dados['margem']:.1f}%)</div>
        <div class="card-footer">
            <span>🚚 Frete: R$ {dados.get('frete', 0):.2f}</span>
            <span>🤝 Repasse: R$ {dados.get('repasse', 0):.2f}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==============================================================================
# 4. GESTÃO DE ESTADO
# ==============================================================================
if 'custo_final' not in st.session_state: st.session_state.custo_final = 0.0
if 'detalhes_custo' not in st.session_state: st.session_state.detalhes_custo = {}
if 'prod_id_selecionado' not in st.session_state: st.session_state.prod_id_selecionado = None

# ==============================================================================
# 5. SIDEBAR
# ==============================================================================
with st.sidebar:
    st.title("🚀 Market Manager")
    st.markdown("---")
    
    st.subheader("⚙️ Parâmetros")
    canal = st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"])
    
    c1, c2 = st.columns(2)
    icms_venda = input_float("ICMS (%)", 18.0, "icms_v")
    difal = input_float("DIFAL (%)", 0.0, "difal")
    
    c3, c4 = st.columns(2)
    peso = input_float("Peso (Kg)", 0.3, "peso")
    armaz = input_float("Armaz. (%)", 0.0, "armaz")
    is_full = st.toggle("⚡ Full Fulfillment", False)

    st.markdown("---")
    st.info(f"💰 Custo Base: **R$ {st.session_state.custo_final:,.2f}**")

# ==============================================================================
# 6. ÁREA PRINCIPAL
# ==============================================================================
tab1, tab2 = st.tabs(["🧮 Calculadora", "📝 Cadastro (DB)"])

with tab1:
    st.markdown(f"### 🏷️ Simulação: {canal}")
    if st.session_state.custo_final <= 0:
        st.warning("⚠️ Defina o custo na aba 'Cadastro'.")

    tipo_calculo = st.radio("Objetivo:", ["🎯 Margem (%)", "💵 Preço Fixo (R$)"], horizontal=True)
    modo = "margem" if "Margem" in tipo_calculo else "preco"
    impostos = {'icms': icms_venda, 'difal': difal}

    if "Mercado Livre" in canal:
        col_classico, col_premium = st.columns(2)
        
        with col_classico:
            st.markdown("#### 🔹 Clássico")
            c1, c2 = st.columns(2)
            com_c = input_float("Comissão (%)", 11.5, "com_cla")
            marg_c = input_float("Margem (%)", 15.0, "marg_cla")
            
            if modo == "preco":
                pr_c = input_float("Preço (R$)", 100.0, "pr_cla")
                res_c = calcular_cenario(0, pr_c, com_c, "preco", canal, st.session_state.custo_final, impostos, peso, is_full, armaz)
            else:
                res_c = calcular_cenario(marg_c, 0, com_c, "margem", canal, st.session_state.custo_final, impostos, peso, is_full, armaz)
            
            exibir_card_compacto("Sugestão Clássico", res_c)

        with col_premium:
            st.markdown("#### 🔸 Premium")
            p1, p2 = st.columns(2)
            com_p = input_float("Comissão (%)", 16.5, "com_pre")
            marg_p = input_float("Margem (%)", 15.0, "marg_pre")
            
            if modo == "preco":
                pr_p = input_float("Preço (R$)", 110.0, "pr_pre")
                res_p = calcular_cenario(0, pr_p, com_p, "preco", canal, st.session_state.custo_final, impostos, peso, is_full, armaz)
            else:
                res_p = calcular_cenario(marg_p, 0, com_p, "margem", canal, st.session_state.custo_final, impostos, peso, is_full, armaz)
            
            exibir_card_compacto("Sugestão Premium", res_p)

    else:
        col_unico, _ = st.columns([1, 1])
        with col_unico:
            st.markdown(f"#### 🛍️ {canal}")
            cc1, cc2 = st.columns(2)
            com_u = input_float("Comissão (%)", 14.0, "com_uni")
            marg_u = input_float("Margem (%)", 15.0, "marg_uni")
            
            if modo == "preco":
                pr_u = input_float("Preço (R$)", 100.0, "pr_uni")
                res_u = calcular_cenario(0, pr_u, com_u, "preco", canal, st.session_state.custo_final, impostos, peso, is_full, armaz)
            else:
                res_u = calcular_cenario(marg_u, 0, com_u, "margem", canal, st.session_state.custo_final, impostos, peso, is_full, armaz)
            
            exibir_card_compacto(f"Sugestão {canal}", res_u)

with tab2:
    st.markdown("### ☁️ Gestão de Custos")

    df_prods = run_query("SELECT id, sku, nome, preco_partida, ipi_percent, icms_percent, quantidade, nro_nf FROM produtos ORDER BY nome ASC")
    opcoes_busca = ["✨ Novo Produto"]
    mapa_dados = {}
    
    if not df_prods.empty:
        df_prods['label'] = df_prods['sku'] + " - " + df_prods['nome']
        for _, row in df_prods.iterrows():
            if row['label'] not in mapa_dados:
                mapa_dados[row['label']] = row
                opcoes_busca.append(row['label'])

    produto_selecionado = st.selectbox("🔍 Buscar no Banco:", options=opcoes_busca)

    if produto_selecionado != "✨ Novo Produto":
        if st.session_state.get('ultimo_prod_carregado') != produto_selecionado:
            d = mapa_dados[produto_selecionado]
            st.session_state.prod_id_selecionado = d['id']
            st.session_state['in_sku'] = str(d['sku'])
            st.session_state['in_nome'] = str(d['nome'])
            st.session_state['in_nf'] = str(d['nro_nf']) if d['nro_nf'] else ""
            st.session_state['in_qtd'] = int(d['quantidade'])
            st.session_state['pc_cad'] = str(d['preco_partida'])
            st.session_state['ipi_cad'] = str(d['ipi_percent'])
            st.session_state['icmsp_cad'] = str(d['icms_percent'])
            st.session_state['ultimo_prod_carregado'] = produto_selecionado
            st.toast(f"Carregado: {d['nome']}", icon="📂")
    else:
        if st.session_state.get('ultimo_prod_carregado') != "NOVO":
            st.session_state.prod_id_selecionado = None
            st.session_state['ultimo_prod_carregado'] = "NOVO"

    col_form, col_resumo = st.columns([2, 1])
    
    with col_form:
        with st.container(border=True):
            st.caption("Dados e Custos")
            c1, c2 = st.columns(2)
            sku_val = c1.text_input("SKU", key="in_sku")
            nome_val = c2.text_input("Nome", key="in_nome")
            c3, c4 = st.columns(2)
            nf_val = c3.text_input("NF", key="in_nf")
            qtd_val = c4.number_input("Qtd", min_value=1, key="in_qtd")

            l_real = st.toggle("Lucro Real", True)
            r1, r2, r3 = st.columns(3)
            pc = input_float("Compra (R$)", 0.0, "pc_cad")
            frete = input_float("Frete (R$)", 0.0, "fr_cad")
            ipi = input_float("IPI (%)", 0.0, "ipi_cad")
            
            r4, r5, r6 = st.columns(3)
            icms_prod = input_float("ICMS Prod(%)", 12.0, "icmsp_cad")
            icms_frete = input_float("ICMS Frete(%)", 0.0, "icmsf_cad")
            st_val = input_float("ST (R$)", 0.0, "st_cad")
            outros = input_float("Outros (R$)", 0.0, "out_cad")

            st.write("")
            b1, b2, b3 = st.columns([1, 1.5, 1.5])
            
            if b1.button("🔄 Calc", use_container_width=True):
                res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                st.session_state.custo_final = res['custo_final']
                st.session_state.detalhes_custo = res

            if b2.button("💾 Salvar Novo", type="primary", use_container_width=True):
                if sku_val and nome_val:
                    res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                    sql = """INSERT INTO produtos (sku, nome, nro_nf, quantidade, preco_partida, ipi_percent, icms_percent, preco_final, data_compra) 
                             VALUES (:sku, :nome, :nf, :qtd, :pp, :ipi, :icms, :pf, :dt)"""
                    params = {"sku": sku_val, "nome": nome_val, "nf": nf_val, "qtd": qtd_val, "pp": pc, "ipi": ipi, "icms": icms_prod, "pf": res['custo_final'], "dt": date.today()}
                    if run_command(sql, params):
                        st.toast("Salvo!", icon="☁️")
                        time.sleep(1)
                        st.rerun()

            if st.session_state.prod_id_selecionado:
                if b3.button("✏️ Atualizar", use_container_width=True):
                    res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                    sql = """UPDATE produtos SET sku=:sku, nome=:nome, nro_nf=:nf, quantidade=:qtd, 
                             preco_partida=:pp, ipi_percent=:ipi, icms_percent=:icms, preco_final=:pf WHERE id=:id"""
                    params = {"sku": sku_val, "nome": nome_val, "nf": nf_val, "qtd": qtd_val, "pp": pc, "ipi": ipi, "icms": icms_prod, "pf": res['custo_final'], "id": st.session_state.prod_id_selecionado}
                    if run_command(sql, params):
                        st.toast("Atualizado!", icon="🔄")
                        time.sleep(1)
                        st.rerun()

    with col_resumo:
        if st.session_state.custo_final > 0:
            d = st.session_state.detalhes_custo
            with st.container(border=True):
                st.caption("Custo Final")
                st.markdown(f'<div class="card-price" style="font-size: 22px;">R$ {d.get("custo_final", 0):.2f}</div>', unsafe_allow_html=True)
                st.divider()
                st.markdown("**Créditos:**")
                st.write(f"ICMS: R$ {d.get('credito_icms', 0):.2f}")
                st.write(f"PIS/COF: R$ {d.get('credito_pis', 0) + d.get('credito_cofins', 0):.2f}")
                st.success(f"Total: R$ {d.get('creditos', 0):.2f}")
