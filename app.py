import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import time

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTILO (CSS Corrigido para mostrar as Abas)
# ==============================================================================
st.set_page_config(page_title="Market Manager Pro", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    /* Ajuste seguro para não esconder as abas */
    .block-container { 
        padding-top: 3.5rem !important; 
        padding-bottom: 1rem !important; 
        max-width: 98%; 
    }
    
    .stButton>button { border-radius: 6px; font-weight: bold; height: 2.8em; }
    
    /* Cards de Resultado */
    .result-card {
        background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px;
        padding: 15px; text-align: center; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .card-price { font-size: 24px; font-weight: 800; color: #1E88E5; margin: 0; }
    .card-footer { 
        margin-top: 8px; padding-top: 8px; border-top: 1px solid #ddd; 
        font-size: 13px; font-weight: 600; display: flex; justify-content: space-between;
    }
    div[data-testid="stTextInput"] input { font-size: 15px; }
    div[data-testid="stTextInput"] label { font-size: 13px; margin-bottom: 2px; }
    div[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO
# ==============================================================================
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")
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

# ==============================================================================
# 3. LÓGICA E CONVERSÃO
# ==============================================================================
def str_to_float(valor_str):
    if not valor_str: return 0.0
    if isinstance(valor_str, (float, int)): return float(valor_str)
    try:
        return float(str(valor_str).replace(',', '.').strip())
    except:
        return 0.0

def obter_taxa_fixa_ml(preco):
    if preco >= 79.00: return 0.00
    elif preco >= 50.00: return 6.75
    elif preco >= 29.00: return 6.50
    elif preco > 12.50: return 6.25
    else: return 0.50

TABELA_FRETE_ML = {
    "79-99": [(0.3, 11.97), (0.5, 12.87), (1.0, 13.47), (2.0, 14.07), (3.0, 14.97), (4.0, 16.17), (5.0, 17.07), (9.0, 26.67), (13.0, 39.57)],
    "100-119": [(0.3, 13.97), (0.5, 15.02), (1.0, 15.72), (2.0, 16.42), (3.0, 17.47), (4.0, 18.87), (5.0, 19.92), (9.0, 31.12), (13.0, 46.17)],
    "120-149": [(0.3, 15.96), (0.5, 17.16), (1.0, 17.96), (2.0, 18.76), (3.0, 19.96), (4.0, 21.56), (5.0, 22.76), (9.0, 35.56), (13.0, 52.76)],
    "150-199": [(0.3, 17.96), (0.5, 19.31), (1.0, 20.21), (2.0, 21.11), (3.0, 22.46), (4.0, 24.26), (5.0, 25.61), (9.0, 40.01), (13.0, 59.36)],
    "200+": [(0.3, 19.95), (0.5, 21.45), (1.0, 22.45), (2.0, 23.45), (3.0, 24.95), (4.0, 26.95), (5.0, 28.45), (9.0, 44.45), (13.0, 65.95)]
}

def obter_frete_ml_tabela(preco, peso):
    if preco < 79.00: return 0.00
    faixa = "200+"
    if 79 <= preco < 100: faixa = "79-99"
    elif 100 <= preco < 120: faixa = "100-119"
    elif 120 <= preco < 150: faixa = "120-149"
    elif 150 <= preco < 200: faixa = "150-199"
    
    lista = TABELA_FRETE_ML.get(faixa, TABELA_FRETE_ML["200+"])
    for limite, valor in lista:
        if peso <= limite: return valor
    return lista[-1][1]

def calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, l_real):
    v_pc, v_frete, v_ipi = str_to_float(pc), str_to_float(frete), str_to_float(ipi)
    v_outros, v_st = str_to_float(outros), str_to_float(st_val)
    v_icms_frete, v_icms_prod = str_to_float(icms_frete), str_to_float(icms_prod)

    valor_ipi = v_pc * (v_ipi / 100)
    preco_medio = v_pc + v_frete + valor_ipi + v_outros + v_st
    
    credito_icms = 0.0
    if l_real:
        c_frete = v_frete * (v_icms_frete / 100)
        c_prod = v_pc * (v_icms_prod / 100)
        credito_icms = c_frete + c_prod
    
    credito_pis_cofins = preco_medio * (0.0925) if l_real else 0.0 
    
    total_creditos = credito_icms + credito_pis_cofins
    custo_final = preco_medio - total_creditos
    
    return {'custo_final': custo_final, 'creditos': total_creditos, 'icms_rec': credito_icms, 'pis_cof_rec': credito_pis_cofins}

def calcular_cenario(margem_alvo, preco_manual, comissao, modo, canal, custo_base, impostos, peso, is_full, armaz):
    v_margem = str_to_float(margem_alvo)
    v_preco_man = str_to_float(preco_manual)
    v_comissao = str_to_float(comissao)
    v_icms = str_to_float(impostos['icms']) / 100
    v_difal = str_to_float(impostos['difal']) / 100
    v_peso = str_to_float(peso)
    v_armaz = str_to_float(armaz)

    imposto_total = v_icms + v_difal + 0.0925
    perc_variaveis = imposto_total + (v_comissao/100) + (v_armaz/100 if not is_full else 0.0)
    
    taxa_fixa = 4.00 if "Shopee" in canal else 0.0
    custo_full = custo_base * (v_armaz/100) if is_full else 0.0
    
    preco = 0.0
    frete = 0.0

    if modo == "preco":
        preco = v_preco_man
        if "Mercado Livre" in canal:
            taxa_fixa += obter_taxa_fixa_ml(preco)
            frete = obter_frete_ml_tabela(preco, v_peso)
    else:
        divisor = 1 - (perc_variaveis + (v_margem/100))
        if divisor <= 0: divisor = 0.01
        custos_fixos = custo_base + custo_full + taxa_fixa
        
        if "Mercado Livre" in canal:
            frete_est = obter_frete_ml_tabela(100.0, v_peso)
            p_teste = (custos_fixos + frete_est) / divisor
            frete = obter_frete_ml_tabela(p_teste, v_peso)
            p_final = (custos_fixos + frete) / divisor
            
            if p_final >= 79.00:
                preco = p_final
            else:
                taxa_ml = obter_taxa_fixa_ml((custos_fixos + 6.00)/divisor)
                preco = (custos_fixos + taxa_ml) / divisor
                taxa_fixa += taxa_ml
                frete = 0.0
        else:
            preco = custos_fixos / divisor

    receita_liq = preco * (1 - perc_variaveis) - frete - taxa_fixa - custo_full
    lucro = receita_liq - custo_base
    margem_real = (lucro / preco * 100) if preco > 0 else 0.0

    return {
        "preco": preco, "lucro": lucro, "margem": margem_real, "frete": frete,
        "detalhes": {"v_icms": preco*v_icms, "v_comissao": preco*(v_comissao/100), "v_taxa": taxa_fixa}
    }

def card_resultado(titulo, dados):
    st.markdown(f"""
    <div class="result-card">
        <div class="card-title">{titulo}</div>
        <div class="card-price">R$ {dados['preco']:.2f}</div>
        <div class="card-profit">Lucro: R$ {dados['lucro']:.2f} ({dados['margem']:.1f}%)</div>
        <div class="card-footer">
            <span>🚚 Frete: {dados['frete']:.2f}</span>
            <span>💰 Taxas: {dados['detalhes']['v_comissao'] + dados['detalhes']['v_taxa']:.2f}</span>
        </div>
    </div>""", unsafe_allow_html=True)

# ==============================================================================
# 4. GESTÃO DE ESTADO
# ==============================================================================
if 'custo_final' not in st.session_state: st.session_state.custo_final = 0.0
if 'prod_selecionado' not in st.session_state: st.session_state.prod_selecionado = None

keys_texto = ['in_sku', 'in_nome', 'in_forn', 'in_nf', 'in_qtd', 
              'pc_cad', 'fr_cad', 'ipi_cad', 'peso_cad', 'icmsp_cad', 'icmsf_cad', 'out_cad', 'st_cad',
              'sb_icms', 'sb_difal', 'sb_peso', 'sb_armaz',
              'com_cla', 'marg_cla', 'pr_cla', 'com_pre', 'marg_pre', 'pr_pre', 'com_uni', 'marg_uni', 'pr_uni',
              'upd_pc', 'upd_fr', 'upd_ipi', 'upd_peso', 'upd_icmsp', 'upd_icmsf', 'upd_out', 'upd_st']

for k in keys_texto:
    if k not in st.session_state: st.session_state[k] = ""

# ==============================================================================
# 5. MODAL DE ATUALIZAÇÃO
# ==============================================================================
@st.dialog("✏️ Atualizar Custos do Produto")
def dialog_atualizar_produto(prod_id, dados_iniciais):
    st.caption(f"Editando: {dados_iniciais['nome']}")
    
    # Preenche se vazio
    if not st.session_state.upd_pc:
        st.session_state.upd_pc = f"{dados_iniciais['preco_partida']:.2f}"
        st.session_state.upd_ipi = f"{dados_iniciais['ipi_percent']:.2f}"
        st.session_state.upd_icmsp = f"{dados_iniciais['icms_percent']:.2f}"
        st.session_state.upd_peso = f"{dados_iniciais['peso']:.3f}" if dados_iniciais['peso'] else "0.000"

    c1, c2, c3 = st.columns(3)
    st.text_input("Preço Compra (R$)", key="upd_pc")
    st.text_input("Frete Compra (R$)", key="upd_fr")
    st.text_input("IPI (%)", key="upd_ipi")
    
    c4, c5, c6 = st.columns(3)
    st.text_input("Peso (Kg)", key="upd_peso")
    st.text_input("ICMS Prod (%)", key="upd_icmsp")
    st.text_input("ICMS Frete (%)", key="upd_icmsf")
    
    c7, c8, c9 = st.columns(3)
    st.text_input("Outros (R$)", key="upd_out")
    st.text_input("ST (R$)", key="upd_st")
    lreal = st.toggle("Lucro Real", value=True)
    
    st.divider()
    
    if st.button("🔄 Simular Novo Custo", use_container_width=True):
        res = calcular_custo_aquisicao(
            st.session_state.upd_pc, st.session_state.upd_fr, st.session_state.upd_ipi, 
            st.session_state.upd_out, st.session_state.upd_st, st.session_state.upd_icmsf, 
            st.session_state.upd_icmsp, lreal
        )
        st.info(f"Novo Custo Final Calculado: **R$ {res['custo_final']:.2f}**")

    if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
        res_final = calcular_custo_aquisicao(
            st.session_state.upd_pc, st.session_state.upd_fr, st.session_state.upd_ipi, 
            st.session_state.upd_out, st.session_state.upd_st, st.session_state.upd_icmsf, 
            st.session_state.upd_icmsp, lreal
        )
        
        sql = """UPDATE produtos SET preco_partida=:pp, ipi_percent=:ipi, icms_percent=:icms, 
                 preco_final=:pf, peso=:peso WHERE id=:id"""
        params = {
            "pp": str_to_float(st.session_state.upd_pc), 
            "ipi": str_to_float(st.session_state.upd_ipi), 
            "icms": str_to_float(st.session_state.upd_icmsp),
            "pf": res_final['custo_final'], 
            "peso": str_to_float(st.session_state.upd_peso), 
            "id": prod_id
        }
        
        if run_command(sql, params):
            st.toast("Produto Atualizado!", icon="✅")
            # Limpa modal
            for k in ['upd_pc', 'upd_fr', 'upd_ipi', 'upd_peso', 'upd_icmsp', 'upd_icmsf', 'upd_out', 'upd_st']:
                st.session_state[k] = ""
            time.sleep(1)
            st.rerun()

# ==============================================================================
# 6. ÁREA PRINCIPAL
# ==============================================================================
st.title("🚀 Market Manager Pro")

tab1, tab2 = st.tabs(["🧮 Calculadora", "📝 Cadastro (DB)"])

with tab1:
    canal = st.session_state.get('sb_canal', 'Mercado Livre')
    st.markdown(f"### 🏷️ {canal}")
    if st.session_state.custo_final <= 0: st.warning("⚠️ Custo zerado. Selecione um produto na aba Cadastro.")

    tipo = st.radio("Meta:", ["Margem (%)", "Preço (R$)"], horizontal=True, label_visibility="collapsed")
    modo = "margem" if "Margem" in tipo else "preco"
    
    # Pega valores da sidebar (que ainda vai renderizar)
    icms_val = st.session_state.sb_icms if st.session_state.get('sb_icms') else "18.0"
    difal_val = st.session_state.sb_difal if st.session_state.get('sb_difal') else "0.0"
    peso_val = st.session_state.sb_peso if st.session_state.get('sb_peso') else "0.3"
    armaz_val = st.session_state.sb_armaz if st.session_state.get('sb_armaz') else "0.0"
    is_full = st.session_state.get('sb_full', False)
    
    impostos = {'icms': icms_val, 'difal': difal_val}
    
    if "Mercado Livre" in canal:
        c1, c2 = st.columns(2)
        with c1:
            st.caption("🔹 Clássico")
            com = st.text_input("Comissão %", key="com_cla") 
            if not com: com = "11.5"
            
            if modo == "preco":
                pr = st.text_input("Preço R$", key="pr_cla")
                if not pr: pr = "100.00"
                res = calcular_cenario(0, pr, com, "preco", canal, st.session_state.custo_final, impostos, peso_val, is_full, armaz_val)
            else:
                mg = st.text_input("Margem %", key="marg_cla")
                if not mg: mg = "15.0"
                res = calcular_cenario(mg, 0, com, "margem", canal, st.session_state.custo_final, impostos, peso_val, is_full, armaz_val)
            card_resultado("Clássico", res)
            
        with c2:
            st.caption("🔸 Premium")
            com = st.text_input("Comissão %", key="com_pre")
            if not com: com = "16.5"
            
            if modo == "preco":
                pr = st.text_input("Preço R$", key="pr_pre")
                if not pr: pr = "110.00"
                res = calcular_cenario(0, pr, com, "preco", canal, st.session_state.custo_final, impostos, peso_val, is_full, armaz_val)
            else:
                mg = st.text_input("Margem %", key="marg_pre")
                if not mg: mg = "15.0"
                res = calcular_cenario(mg, 0, com, "margem", canal, st.session_state.custo_final, impostos, peso_val, is_full, armaz_val)
            card_resultado("Premium", res)
    else:
        st.caption(f"🛍️ {canal}")
        c1, c2 = st.columns(2)
        com = c1.text_input("Comissão %", key="com_uni")
        if not com: com = "14.0"
        
        if modo == "preco":
            pr = c2.text_input("Preço R$", key="pr_uni")
            if not pr: pr = "100.00"
            res = calcular_cenario(0, pr, com, "preco", canal, st.session_state.custo_final, impostos, peso_val, is_full, armaz_val)
        else:
            mg = c2.text_input("Margem %", key="marg_uni")
            if not mg: mg = "15.0"
            res = calcular_cenario(mg, 0, com, "margem", canal, st.session_state.custo_final, impostos, peso_val, is_full, armaz_val)
        card_resultado("Resultado", res)

with tab2:
    st.markdown("### ☁️ Cadastro")
    
    # 1. Carrega Produtos
    df = run_query("SELECT id, sku, nome, fornecedor, preco_partida, ipi_percent, icms_percent, quantidade, nro_nf, peso, preco_final FROM produtos ORDER BY id DESC")
    
    lista_prods = ["✨ Novo Produto"]
    dados_map = {}
    
    if not df.empty:
        df_unicos = df.drop_duplicates(subset=['sku']).sort_values(by='nome')
        for _, row in df_unicos.iterrows():
            lbl = f"{row['sku']} - {row['nome']}"
            lista_prods.append(lbl)
            dados_map[lbl] = row

    sel = st.selectbox("Buscar:", lista_prods)

    # 2. Lógica de Visualização
    if sel == "✨ Novo Produto":
        st.session_state.prod_id = None
        c_form, c_res = st.columns([0.8, 0.2])
        with c_form:
            with st.container(border=True):
                st.caption("Novo Cadastro")
                c1, c2, c3 = st.columns([1, 2, 2])
                st.text_input("SKU", key="in_sku")
                st.text_input("Nome", key="in_nome")
                st.text_input("Fornecedor", key="in_forn")

                c4, c5, c6 = st.columns([2, 1, 1], vertical_alignment="bottom")
                st.text_input("NF", key="in_nf")
                st.text_input("Qtd", key="in_qtd")
                l_real = st.toggle("Lucro Real", True)

                st.caption("Valores (Use vírgula ou ponto)")
                k1, k2, k3 = st.columns(3)
                st.text_input("Preço Compra (R$)", key="pc_cad")
                st.text_input("Frete Compra (R$)", key="fr_cad")
                st.text_input("IPI (%)", key="ipi_cad")
                
                k4, k5, k6 = st.columns(3)
                st.text_input("Peso (Kg)", key="peso_cad")
                st.text_input("ICMS Prod (%)", key="icmsp_cad")
                st.text_input("ICMS Frete (%)", key="icmsf_cad")
                
                k7, k8, k9 = st.columns(3)
                st.text_input("Outros (R$)", key="out_cad")
                st.text_input("ST (R$)", key="st_cad")
                
                st.write("")
                if st.button("💾 Salvar Novo", type="primary"):
                    if st.session_state.in_sku:
                        pp = str_to_float(st.session_state.pc_cad)
                        peso = str_to_float(st.session_state.peso_cad)
                        res = calcular_custo_aquisicao(st.session_state.pc_cad, st.session_state.fr_cad, st.session_state.ipi_cad, st.session_state.out_cad, st.session_state.st_cad, st.session_state.icmsf_cad, st.session_state.icmsp_cad, l_real)
                        
                        sql = """INSERT INTO produtos (sku, nome, fornecedor, nro_nf, quantidade, preco_partida, ipi_percent, icms_percent, preco_final, peso, data_compra) 
                                 VALUES (:sku, :nome, :forn, :nf, :qtd, :pp, :ipi, :icms, :pf, :peso, :dt)"""
                        params = {
                            "sku": st.session_state.in_sku, "nome": st.session_state.in_nome, "forn": st.session_state.in_forn,
                            "nf": st.session_state.in_nf, "qtd": str_to_float(st.session_state.in_qtd),
                            "pp": pp, "ipi": str_to_float(st.session_state.ipi_cad), "icms": str_to_float(st.session_state.icmsp_cad),
                            "pf": res['custo_final'], "peso": peso, "dt": date.today()
                        }
                        if run_command(sql, params):
                            st.toast("Salvo!", icon="💾")
                            time.sleep(1)
                            st.rerun()
    
    else:
        # VISUALIZAÇÃO PRODUTO EXISTENTE
        d = dados_map[sel]
        
        with st.container(border=True):
            cols = st.columns([1, 2.5, 1.5, 1, 1])
            cols[0].markdown(f"**SKU:**\n{d['sku']}")
            cols[1].markdown(f"**Produto:**\n{d['nome']}")
            cols[2].markdown(f"**Fornecedor:**\n{d['fornecedor']}")
            cols[3].metric("💵 Preço NF", f"R$ {d['preco_partida']:,.2f}")
            cols[4].metric("💰 Custo Final", f"R$ {d['preco_final']:,.2f}")
            
            st.divider()
            
            b_col1, b_col2 = st.columns([1, 1])
            
            # Botão para Enviar para a Calculadora
            if b_col1.button("🚀 Usar na Calculadora", use_container_width=True):
                st.session_state.custo_final = float(d['preco_final'])
                # ESPELHAMENTO SIDEBAR
                st.session_state.sb_peso = f"{d['peso']:.3f}" if (d['peso'] and float(d['peso']) > 0) else "0.300"
                st.session_state.sb_icms = f"{d['icms_percent']:.2f}" if (d['icms_percent'] and float(d['icms_percent']) > 0) else "18.00"
                
                st.toast(f"Valores de '{d['sku']}' enviados!", icon="🚀")
                st.rerun()

            if b_col2.button("✏️ Atualizar Custos", type="primary", use_container_width=True):
                dialog_atualizar_produto(d['id'], d)

# ==============================================================================
# 7. SIDEBAR
# ==============================================================================
with st.sidebar:
    st.title("🚀 Market Manager")
    st.markdown("---")
    st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"], key="sb_canal")
    
    with st.expander("🛠️ Parâmetros & Tributos", expanded=True):
        c1, c2 = st.columns(2)
        st.text_input("ICMS (%)", key="sb_icms")
        st.text_input("DIFAL (%)", key="sb_difal")
        
        c3, c4 = st.columns(2)
        st.text_input("Peso (Kg)", key="sb_peso")
        st.text_input("Armaz. (%)", key="sb_armaz")
        st.toggle("⚡ Full Fulfillment", key="sb_full")

    st.markdown("---")
    st.info(f"💰 Custo Base: **R$ {st.session_state.custo_final:,.2f}**")
