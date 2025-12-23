import streamlit as st
import time
from datetime import date
from utils.ui import carregar_css, card_resultado
from utils.calculos import calcular_cenario, calcular_custo_aquisicao, str_to_float
from utils.db import run_query, run_command

st.set_page_config(page_title="Calculadora", layout="wide", page_icon="🧮")
carregar_css()

# Garante estado inicial
if 'custo_final' not in st.session_state: st.session_state.custo_final = 0.0

keys_text = ['sb_icms', 'sb_difal', 'sb_peso', 'sb_armaz', 
             'com_cla', 'marg_cla', 'pr_cla', 'com_pre', 'marg_pre', 'pr_pre', 
             'com_uni', 'marg_uni', 'pr_uni', 
             'upd_pc', 'upd_fr', 'upd_ipi', 'upd_peso', 'upd_icmsp', 'upd_icmsf', 'upd_out', 'upd_st']

for k in keys_text:
    if k not in st.session_state: st.session_state[k] = ""

if 'sb_full' not in st.session_state: st.session_state['sb_full'] = False

# ==============================================================================
# 1. MODAIS (POPUP)
# ==============================================================================

# --- MODAL 1: SIMULAR NOVO CUSTO (O que você pediu) ---
@st.dialog("✨ Simular Novo Custo (Sem Cadastro)")
def dialog_simular_novo():
    st.caption("Insira os dados da NF para descobrir o custo real.")
    
    c1, c2, c3 = st.columns(3)
    pc = c1.text_input("Preço Compra (R$)", key="sim_pc")
    fr = c2.text_input("Frete Compra (R$)", key="sim_fr")
    ipi = c3.text_input("IPI (%)", key="sim_ipi")
    
    c4, c5, c6 = st.columns(3)
    peso = c4.text_input("Peso (Kg)", key="sim_peso")
    icms_p = c5.text_input("ICMS Prod (%)", key="sim_icmsp", value="0.0")
    icms_f = c6.text_input("ICMS Frete (%)", key="sim_icmsf", value="0.0")
    
    c7, c8 = st.columns(2)
    outros = c7.text_input("Outros (R$)", key="sim_out")
    st_val = c8.text_input("ST (R$)", key="sim_st")
    lreal = st.toggle("Lucro Real", value=True, key="sim_lreal")
    
    st.divider()
    
    # Cálculo em tempo real para mostrar no botão
    custo_simulado = 0.0
    if pc:
        res = calcular_custo_aquisicao(pc, fr, ipi, outros, st_val, icms_f, icms_p, lreal)
        custo_simulado = res['custo_final']
        st.info(f"💰 Custo Calculado: **R$ {custo_simulado:.2f}**")

    col_btn1, col_btn2 = st.columns(2)
    
    # Botão A: Só usa na calculadora
    if col_btn1.button("🚀 Usar na Calculadora", type="primary", use_container_width=True):
        st.session_state.custo_final = custo_simulado
        if peso: st.session_state.sb_peso = peso
        if icms_p: st.session_state.sb_icms = icms_p
        st.rerun()

    # Botão B: Salva no banco e usa (Opcional, mas útil)
    if col_btn2.button("💾 Salvar e Usar", use_container_width=True):
        st.session_state.custo_final = custo_simulado
        # Inserção rápida no banco com nome genérico para editar depois
        sql = """INSERT INTO produtos (sku, nome, fornecedor, preco_partida, preco_final, peso, data_compra, quantidade) 
                 VALUES ('NOVO', 'Produto Simulado', 'Simulação', :pp, :pf, :peso, :dt, 0)"""
        params = {
            "pp": str_to_float(pc), "pf": custo_simulado, "peso": str_to_float(peso), "dt": date.today()
        }
        run_command(sql, params)
        st.toast("Salvo como rascunho!", icon="💾")
        st.session_state.custo_final = custo_simulado
        st.rerun()

# --- MODAL 2: EDITAR EXISTENTE ---
@st.dialog("✏️ Atualizar Custos do Produto")
def dialog_atualizar_produto(prod_id, dados_iniciais):
    st.caption(f"Editando: {dados_iniciais['nome']}")
    if not st.session_state.upd_pc:
        st.session_state.upd_pc = f"{dados_iniciais['preco_partida']:.2f}"
        st.session_state.upd_ipi = f"{dados_iniciais['ipi_percent']:.2f}" if dados_iniciais['ipi_percent'] else "0.00"
        st.session_state.upd_icmsp = f"{dados_iniciais['icms_percent']:.2f}" if dados_iniciais['icms_percent'] else "0.00"
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
    lreal = st.toggle("Lucro Real", value=True, key="upd_lreal")
    
    if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
        res_final = calcular_custo_aquisicao(st.session_state.upd_pc, st.session_state.upd_fr, st.session_state.upd_ipi, st.session_state.upd_out, st.session_state.upd_st, st.session_state.upd_icmsf, st.session_state.upd_icmsp, lreal)
        sql = "UPDATE produtos SET preco_partida=:pp, ipi_percent=:ipi, icms_percent=:icms, preco_final=:pf, peso=:peso WHERE id=:id"
        params = {"pp": str_to_float(st.session_state.upd_pc), "ipi": str_to_float(st.session_state.upd_ipi), "icms": str_to_float(st.session_state.upd_icmsp), "pf": res_final['custo_final'], "peso": str_to_float(st.session_state.upd_peso), "id": prod_id}
        if run_command(sql, params):
            st.toast("Produto Atualizado!", icon="✅")
            st.session_state.custo_final = res_final['custo_final'] # Atualiza a calc também
            st.rerun()

# ==============================================================================
# 2. ÁREA DE IMPORTAÇÃO E SIMULAÇÃO
# ==============================================================================
st.title("🧮 Calculadora de Margem")

with st.expander("📦 Importar do Estoque ou Simular Novo", expanded=True):
    c_busca, c_novo = st.columns([3, 1], vertical_alignment="bottom")
    
    # Lado Esquerdo: Busca no Banco
    with c_busca:
        try:
            df_prods = run_query("SELECT * FROM produtos ORDER BY nome")
            mapa_produtos = {f"{row['sku']} - {row['nome']}": row for _, row in df_prods.iterrows()} if not df_prods.empty else {}
            prod_selecionado = st.selectbox("Selecione um produto:", ["Selecione..."] + list(mapa_produtos.keys()))
        except: map_produtos = {}

    # Lado Direito: Botão de Simulação (NOVO)
    with c_novo:
        if st.button("➕ Simular Novo Custo", use_container_width=True):
            dialog_simular_novo()

    # Ações se selecionou algo da lista
    if prod_selecionado != "Selecione...":
        dados = mapa_produtos[prod_selecionado]
        b1, b2 = st.columns([1, 1])
        
        if b1.button("⬇️ Carregar Dados", use_container_width=True):
            st.session_state.custo_final = float(dados['preco_final'])
            st.session_state.sb_peso = f"{float(dados['peso']):.3f}" if (dados['peso'] and float(dados['peso']) > 0) else "0.300"
            st.session_state.sb_icms = f"{float(dados['icms_percent']):.2f}" if (dados['icms_percent'] and float(dados['icms_percent']) > 0) else "18.00"
            st.toast(f"Dados carregados! Custo: R$ {st.session_state.custo_final:.2f}", icon="🚀")
            time.sleep(0.5)
            st.rerun()

        if b2.button("✏️ Editar Produto", type="secondary", use_container_width=True):
             # Limpa keys antigas
            for k in ['upd_pc', 'upd_fr', 'upd_ipi', 'upd_peso', 'upd_icmsp', 'upd_icmsf', 'upd_out', 'upd_st']: st.session_state[k] = ""
            dialog_atualizar_produto(dados['id'], dados)

st.markdown("---")

# ==============================================================================
# 3. SIDEBAR E CÁLCULO (Padrão)
# ==============================================================================
with st.sidebar:
    st.title("⚙️ Configurações")
    canal = st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"], key="sb_canal")
    with st.expander("🛠️ Parâmetros & Tributos", expanded=True):
        c1, c2 = st.columns(2)
        st.text_input("ICMS (%)", key="sb_icms")
        st.text_input("DIFAL (%)", key="sb_difal")
        c3, c4 = st.columns(2)
        st.text_input("Peso (Kg)", key="sb_peso")
        st.text_input("Armaz. (%)", key="sb_armaz")
        st.toggle("⚡ Full Fulfillment", key="sb_full")
    if st.session_state.custo_final > 0:
        st.success(f"💰 Custo Base: **R$ {st.session_state.custo_final:,.2f}**")
    else: st.info("💰 Custo Base: R$ 0,00")

if st.session_state.custo_final <= 0: 
    st.warning("⚠️ Custo Base zerado. Importe um produto acima ou simule um novo custo.")

tipo = st.radio("Meta:", ["Margem (%)", "Preço (R$)"], horizontal=True, label_visibility="collapsed")
modo = "margem" if "Margem" in tipo else "preco"

icms_val = st.session_state.sb_icms if st.session_state.sb_icms else "18.0"
difal_val = st.session_state.sb_difal if st.session_state.sb_difal else "0.0"
peso_val = st.session_state.sb_peso if st.session_state.sb_peso else "0.3"
armaz_val = st.session_state.sb_armaz if st.session_state.sb_armaz else "0.0"
impostos = {'icms': icms_val, 'difal': difal_val}
is_full = st.session_state.get('sb_full', False)

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
