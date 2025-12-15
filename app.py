import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date

# ==============================================================================
# 1. CONFIGURAÇÃO E CONEXÃO AWS (PYMYSQL)
# ==============================================================================
st.set_page_config(page_title="Calculadora Market", layout="wide", page_icon="☁️")

# Credenciais
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    """Cria a conexão com pool de conexões"""
    return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

def run_query(query, params=None):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            if params:
                return pd.read_sql(text(query), conn, params=params)
            return pd.read_sql(text(query), conn)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return pd.DataFrame()

def run_command(query, params):
    """Executa INSERT, UPDATE ou DELETE"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Erro ao Salvar: {e}")
        return False

# ==============================================================================
# 2. FUNÇÕES AUXILIARES
# ==============================================================================
TABELA_FRETE_ML = {
    "79-99": [(0.3, 11.97), (0.5, 12.87), (1.0, 13.47), (2.0, 14.07), (3.0, 14.97), (4.0, 16.17), (5.0, 17.07), (9.0, 26.67), (13.0, 39.57), (17.0, 44.07), (23.0, 51.57), (30.0, 59.37), (40.0, 61.17), (50.0, 63.27), (60.0, 67.47), (70.0, 72.27), (80.0, 75.57), (90.0, 83.97), (100.0, 95.97), (125.0, 107.37), (150.0, 113.97)],
    "100-119": [(0.3, 13.97), (0.5, 15.02), (1.0, 15.72), (2.0, 16.42), (3.0, 17.47), (4.0, 18.87), (5.0, 19.92), (9.0, 31.12), (13.0, 46.17), (17.0, 51.42), (23.0, 60.17), (30.0, 69.27), (40.0, 71.37), (50.0, 73.82), (60.0, 78.72), (70.0, 84.32), (80.0, 88.17), (90.0, 97.97), (100.0, 111.97), (125.0, 125.27)],
    "120-149": [(0.3, 15.96), (0.5, 17.16), (1.0, 17.96), (2.0, 18.76), (3.0, 19.96), (4.0, 21.56), (5.0, 22.76), (9.0, 35.56), (13.0, 52.76), (17.0, 58.76), (23.0, 68.76), (30.0, 79.16), (40.0, 81.56), (50.0, 84.36), (60.0, 89.96), (70.0, 96.36), (80.0, 100.76), (90.0, 111.96), (100.0, 127.96), (125.0, 143.16), (150.0, 151.96)],
    "150-199": [(0.3, 17.96), (0.5, 19.31), (1.0, 20.21), (2.0, 21.11), (3.0, 22.46), (4.0, 24.26), (5.0, 25.61), (9.0, 40.01), (13.0, 59.36), (17.0, 66.11), (23.0, 77.36), (30.0, 89.06), (40.0, 91.76), (50.0, 94.91), (60.0, 101.21), (70.0, 108.41), (80.0, 113.36), (90.0, 125.96), (100.0, 143.96), (125.0, 161.06)],
    "200+": [(0.3, 19.95), (0.5, 21.45), (1.0, 22.45), (2.0, 23.45), (3.0, 24.95), (4.0, 26.95), (5.0, 28.45), (9.0, 44.45), (13.0, 65.95), (17.0, 73.45), (23.0, 85.95), (30.0, 98.95), (40.0, 101.95), (50.0, 105.45), (60.0, 112.45), (70.0, 120.45), (80.0, 125.95), (90.0, 139.95), (100.0, 159.95), (125.0, 178.95), (150.0, 189.95)]
}

def input_float(label, value, key):
    # Vacina contra erro de tipo no cache
    if key in st.session_state:
        st.session_state[key] = str(st.session_state[key])
    
    val_str = st.text_input(label, value=str(value), key=key)
    val_limpo = val_str.replace(',', '.').strip()
    try:
        return float(val_limpo) if val_limpo else 0.0
    except:
        return 0.0

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
    custo_final = preco_medio - total_creditos
    
    return {'custo_final': custo_final, 'preco_medio': preco_medio, 'creditos': total_creditos, 
            'credito_icms': credito_icms, 'credito_pis': credito_pis, 'credito_cofins': credito_cofins}

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
    return {"preco": preco, "lucro": lucro, "margem": margem_real, "repasse": preco - val_mkt}

# ==============================================================================
# 3. GESTÃO DE ESTADO
# ==============================================================================
if 'custo_final' not in st.session_state: st.session_state.custo_final = 0.0
if 'detalhes_custo' not in st.session_state: st.session_state.detalhes_custo = {}
if 'prod_id_selecionado' not in st.session_state: st.session_state.prod_id_selecionado = None

# ==============================================================================
# 4. SIDEBAR (Conectado ao Banco)
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Configuração")
    canal = st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"])
    st.divider()
    
    st.subheader("📦 Catálogo (Nuvem)")
    
    # Busca ID também para poder atualizar
    df_prods = run_query("SELECT id, sku, nome, preco_partida, ipi_percent, icms_percent, data_compra, nro_nf, quantidade FROM produtos ORDER BY id DESC")
    
    opcoes = ["Novo Produto"]
    mapa = {}
    
    if not df_prods.empty:
        df_prods['label'] = df_prods['sku'] + " | " + df_prods['nome']
        # Remove duplicatas visuais mantendo o mais recente para seleção
        for _, row in df_prods.iterrows():
            if row['label'] not in mapa:
                mapa[row['label']] = row
                opcoes.append(row['label'])

    sel = st.selectbox("Produto", options=opcoes, key="last_prod_sel")
    
    if sel != "Novo Produto":
        d = mapa[sel]
        st.session_state.prod_id_selecionado = d['id']
        st.session_state['pc_cad'] = str(d['preco_partida'])
        st.session_state['ipi_cad'] = str(d['ipi_percent'])
        st.session_state['icmsp_cad'] = str(d['icms_percent'])
        # Carrega dados extras para o form
        st.session_state['sku_edit'] = str(d['sku'])
        st.session_state['nome_edit'] = str(d['nome'])
        st.session_state['nf_edit'] = str(d['nro_nf'])
        st.session_state['qtd_edit'] = int(d['quantidade'])
        
        st.success(f"Carregado: {d['data_compra']} (ID: {d['id']})")
    else:
        st.session_state.prod_id_selecionado = None
        st.session_state['sku_edit'] = ""
        st.session_state['nome_edit'] = ""
        st.session_state['nf_edit'] = ""
        st.session_state['qtd_edit'] = 1

    st.info(f"Custo Base: **R$ {st.session_state.custo_final:,.2f}**")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    icms_venda = input_float("ICMS Venda", 18.0, "icms_v")
    difal = input_float("DIFAL", 0.0, "difal")
    c3, c4 = st.columns(2)
    peso = input_float("Peso (Kg)", 0.3, "peso")
    armaz = input_float("Armaz.", 0.0, "armaz")
    is_full = st.checkbox("Full?", False)

# ==============================================================================
# 5. ÁREA PRINCIPAL
# ==============================================================================
tab1, tab2 = st.tabs(["🧮 Calculadora", "📝 Cadastro & Edição"])

with tab1:
    st.markdown(f"### 🏷️ Simulação - {canal}")
    if st.session_state.custo_final <= 0: st.warning("Defina o custo na aba Cadastro.")
    
    tipo = st.radio("Modo", ["Margem (%)", "Preço (R$)"], horizontal=True)
    modo = "margem" if "Margem" in tipo else "preco"
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("#### Simulação Principal")
            c1, c2 = st.columns(2)
            com = input_float("Comissão %", 11.5, "com_1")
            marg = input_float("Margem %", 15.0, "marg_1")
            
            if modo == "preco":
                pr = input_float("Preço Venda", 100.0, "pr_1")
                res = calcular_cenario(0, pr, com, "preco", canal, st.session_state.custo_final, {'icms': icms_venda, 'difal': difal}, peso, is_full, armaz)
            else:
                res = calcular_cenario(marg, 0, com, "margem", canal, st.session_state.custo_final, {'icms': icms_venda, 'difal': difal}, peso, is_full, armaz)
            
            st.metric("Preço Final", f"R$ {res['preco']:.2f}")
            st.markdown(f"**Lucro:** :green[R$ {res['lucro']:.2f}] ({res['margem']:.1f}%)")
            st.caption(f"Repasse Mkt: R$ {res['repasse']:.2f}")

with tab2:
    st.markdown("### ☁️ Cadastro de Custo Real (AWS)")
    c_form, c_info = st.columns([2, 1])
    
    with c_form:
        with st.container(border=True):
            st.subheader("1. Dados do Produto")
            c_prod1, c_prod2 = st.columns(2)
            # Usa key dinâmica ou session_state carregado
            sku_val = st.text_input("SKU", value=st.session_state.get('sku_edit', ''), key="input_sku")
            nome_val = st.text_input("Nome", value=st.session_state.get('nome_edit', ''), key="input_nome")
            
            c_nf1, c_nf2 = st.columns(2)
            nf_val = st.text_input("Nota Fiscal", value=st.session_state.get('nf_edit', ''), key="input_nf")
            qtd_val = st.number_input("Quantidade", min_value=1, value=st.session_state.get('qtd_edit', 1), key="input_qtd")

            st.subheader("2. Composição de Custo")
            l_real = st.toggle("Lucro Real", True)
            c1, c2, c3 = st.columns(3)
            pc = input_float("Preço Compra", 0.0, "pc_cad")
            frete = input_float("Frete Entrada", 0.0, "fr_cad")
            ipi = input_float("IPI %", 0.0, "ipi_cad")
            c4, c5 = st.columns(2)
            outros = input_float("Outros", 0.0, "out_cad")
            st_val = input_float("ST", 0.0, "st_cad")
            
            icms_prod = input_float("ICMS Prod %", 12.0, "icmsp_cad")
            icms_frete = input_float("ICMS Frete %", 0.0, "icmsf_cad")
            
            st.markdown("---")
            b_calc, b_salvar, b_update = st.columns(3)
            
            # --- LÓGICA DE BOTÕES ---
            
            # 1. BOTÃO CALCULAR
            if b_calc.button("🔄 Calcular", use_container_width=True):
                res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                st.session_state.custo_final = res['custo_final']
                st.session_state.detalhes_custo = res
                st.toast("Custo calculado!")
            
            # 2. BOTÃO SALVAR NOVO (INSERT)
            if b_salvar.button("💾 Salvar Nova Compra", use_container_width=True, type="primary"):
                if not sku_val or not nome_val:
                    st.error("Preencha SKU e Nome.")
                else:
                    # Garante cálculo antes de salvar
                    res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                    
                    sql = """
                        INSERT INTO produtos (sku, nome, nro_nf, quantidade, preco_partida, ipi_percent, icms_percent, preco_final, data_compra)
                        VALUES (:sku, :nome, :nf, :qtd, :pp, :ipi, :icms, :pf, :dt)
                    """
                    params = {
                        "sku": sku_val, "nome": nome_val, "nf": nf_val, "qtd": qtd_val, 
                        "pp": pc, "ipi": ipi, "icms": icms_prod, 
                        "pf": res['custo_final'], "dt": date.today()
                    }
                    if run_command(sql, params):
                        st.toast("Novo registro salvo!", icon="☁️")
                        # Limpa seleção para evitar confusão
                        st.session_state.prod_id_selecionado = None
                        st.rerun()

            # 3. BOTÃO ATUALIZAR (UPDATE) - Só aparece se tiver ID selecionado
            if st.session_state.prod_id_selecionado:
                if b_update.button("✏️ Atualizar Este Registro", use_container_width=True):
                    res = calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, 1.65, 7.60, l_real)
                    
                    sql_upd = """
                        UPDATE produtos 
                        SET sku=:sku, nome=:nome, nro_nf=:nf, quantidade=:qtd, 
                            preco_partida=:pp, ipi_percent=:ipi, icms_percent=:icms, preco_final=:pf
                        WHERE id = :id
                    """
                    params_upd = {
                        "sku": sku_val, "nome": nome_val, "nf": nf_val, "qtd": qtd_val, 
                        "pp": pc, "ipi": ipi, "icms": icms_prod, 
                        "pf": res['custo_final'], "id": st.session_state.prod_id_selecionado
                    }
                    if run_command(sql_upd, params_upd):
                        st.toast(f"Registro ID {st.session_state.prod_id_selecionado} atualizado!", icon="✅")
                        st.rerun()

    with c_info:
        if st.session_state.detalhes_custo:
            d = st.session_state.detalhes_custo
            st.info(f"### Custo: R$ {d.get('custo_final', 0):.2f}")
            st.caption(f"Preço Médio: R$ {d.get('preco_medio', 0):.2f}")
            st.write("---")
            st.write("**Créditos Recuperados:**")
            st.write(f"ICMS: R$ {d.get('credito_icms', 0):.2f}")
            st.write(f"PIS: R$ {d.get('credito_pis', 0):.2f}")
            st.write(f"COFINS: R$ {d.get('credito_cofins', 0):.2f}")
