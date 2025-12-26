import streamlit as st
import pandas as pd
import time
from utils.ui import carregar_css, card_resultado
from utils.calculos import calcular_cenario, calcular_custo_aquisicao
from utils.db import run_query, run_command

# ==============================================================================
# 1. INICIALIZAÇÃO DE ESTADO
# ==============================================================================
defaults = {
    'custo_final': 0.0,
    'sb_regime': 'Lucro Real',
    'sb_origem': 'Nacional / Revenda',
    'sb_icms': '18.00', 'sb_difal': '0.00',
    'sb_pis': '1.65', 'sb_cofins': '7.60',
    'sb_peso': '0.300', 'sb_full': False,
    'com_cla': '11.5', 'marg_cla': '15.0', 'pr_cla': 0.0,
    'com_pre': '16.5', 'marg_pre': '20.0', 'pr_pre': 0.0,
    'upd_pc': '', 'upd_fr': '', 'upd_ipi': '', 'upd_peso': '', 
    'upd_icmsp': '', 'upd_icmsf': '', 'upd_out': '', 'upd_st': '', 'upd_lreal': True,
    'is_simulation': False, # Novo controle de simulação
    'draft_cadastro': {}    # Memória do rascunho
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==============================================================================
# 2. FUNÇÕES AUXILIARES
# ==============================================================================
def safe_float(valor):
    if not valor: return 0.0
    if isinstance(valor, (float, int)): return float(valor)
    try: return float(str(valor).replace(',', '.'))
    except: return 0.0

def criar_dre_detalhada(preco_venda, custo_prod, comissao_pct, impostos_dict, frete_saida):
    fat = safe_float(preco_venda)
    custo_m = safe_float(custo_prod)
    frete = safe_float(frete_saida)
    pc_com = safe_float(comissao_pct)
    
    # Impostos
    v_icms = fat * (safe_float(impostos_dict.get('icms')) / 100)
    v_pis = fat * (safe_float(impostos_dict.get('pis')) / 100)
    v_cofins = fat * (safe_float(impostos_dict.get('cofins')) / 100)
    v_difal = fat * (safe_float(impostos_dict.get('difal')) / 100)
    
    # Taxas
    v_comissao = fat * (pc_com / 100)
    v_fixa = 6.00 if ("Mercado Livre" in st.session_state.sb_canal and 0 < fat < 79.00) else 0.00
    
    lucro = fat - (v_icms + v_pis + v_cofins + v_difal) - (v_comissao + v_fixa) - custo_m - frete
    
    dados = [
        {"Descrição": "1. PREÇO DE VENDA", "Valor": fat},
        {"Descrição": "(-) ICMS", "Valor": -v_icms},
        {"Descrição": "(-) PIS", "Valor": -v_pis},
        {"Descrição": "(-) COFINS", "Valor": -v_cofins},
        {"Descrição": "(-) DIFAL", "Valor": -v_difal},
        {"Descrição": "(-) Comissão", "Valor": -v_comissao},
        {"Descrição": "(-) Taxa Fixa", "Valor": -v_fixa},
        {"Descrição": "(-) Custo Produto (CMV)", "Valor": -custo_m},
        {"Descrição": "(-) Frete Saída", "Valor": -frete},
        {"Descrição": "(=) LUCRO LÍQUIDO", "Valor": lucro}
    ]
    return pd.DataFrame(dados)

# ==============================================================================
# 3. MODAIS
# ==============================================================================

# --- MODAL DE EDIÇÃO (Banco de Dados) ---
@st.dialog("✏️ Editar Produto")
def dialog_atualizar(prod_id, dados):
    st.caption(f"Editando: {dados['nome']}")
    if not st.session_state.upd_pc:
        st.session_state.upd_pc = f"{dados['preco_partida']:.2f}"
        st.session_state.upd_ipi = f"{dados['ipi_percent']:.2f}" if dados['ipi_percent'] else "0.00"
        st.session_state.upd_icmsp = f"{dados['icms_percent']:.2f}" if dados['icms_percent'] else "0.00"
        st.session_state.upd_peso = f"{dados['peso']:.3f}" if dados['peso'] else "0.000"

    c1, c2, c3 = st.columns(3)
    st.text_input("Preço Compra", key="upd_pc")
    st.text_input("Frete Compra", key="upd_fr")
    st.text_input("IPI (%)", key="upd_ipi")
    c4, c5 = st.columns(2)
    st.text_input("Peso (Kg)", key="upd_peso")
    st.text_input("ICMS Prod (%)", key="upd_icmsp")
    lreal = st.toggle("Lucro Real", value=True, key="upd_lreal")
    is_imp = st.toggle("Importação Própria", value=(True if dados['importacao_propria'] else False))

    if st.button("Salvar e Usar", type="primary"):
        res = calcular_custo_aquisicao(st.session_state.upd_pc, st.session_state.upd_fr, st.session_state.upd_ipi, "0", "0", "0", st.session_state.upd_icmsp, lreal)
        
        sql = "UPDATE produtos SET preco_partida=:pp, ipi_percent=:ipi, icms_percent=:icms, preco_final=:pf, peso=:peso, importacao_propria=:imp WHERE id=:id"
        params = {"pp": safe_float(st.session_state.upd_pc), "ipi": safe_float(st.session_state.upd_ipi), "icms": safe_float(st.session_state.upd_icmsp), "pf": res['custo_final'], "peso": safe_float(st.session_state.upd_peso), "imp": is_imp, "id": prod_id}
        run_command(sql, params)
        
        st.session_state.custo_final = res['custo_final']
        st.session_state.sb_peso = st.session_state.upd_peso
        st.session_state.is_simulation = False # Sai do modo simulação pois carregou do banco
        
        if is_imp:
            st.session_state.sb_pis, st.session_state.sb_cofins = "2.10", "9.65"
            st.session_state.sb_origem = "Importação Própria"
        else:
            st.session_state.sb_pis, st.session_state.sb_cofins = "1.65", "7.60"
            st.session_state.sb_origem = "Nacional / Revenda"
            
        st.toast("Atualizado e Carregado!", icon="✅")
        st.rerun()

# --- MODAL DE SIMULAÇÃO (TESTE SEM SALVAR) ---
@st.dialog("🧪 Simular Compra (Teste)")
def dialog_simular():
    st.caption("Insira os dados da compra para descobrir o custo final.")
    
    c1, c2, c3 = st.columns(3)
    pc = c1.number_input("Preço Compra (R$)", min_value=0.0, step=1.0)
    fr = c2.number_input("Frete Compra (R$)", min_value=0.0, step=1.0)
    ipi = c3.number_input("IPI (%)", min_value=0.0, step=0.1)
    
    c4, c5 = st.columns(2)
    icms_p = c4.number_input("ICMS Prod (%)", min_value=0.0, step=0.1)
    peso_s = c5.number_input("Peso Estimado (Kg)", min_value=0.0, format="%.3f")
    
    c6, c7 = st.columns(2)
    lreal_s = c6.toggle("Lucro Real (Entrada)", value=True)
    imp_s = c7.toggle("Importação Própria", value=False)
    
    st.divider()
    
    # Cálculo em Tempo Real
    res = calcular_custo_aquisicao(pc, fr, ipi, 0, 0, 0, icms_p, lreal_s)
    custo_simulado = res['custo_final']
    st.metric("Custo Final Estimado", f"R$ {custo_simulado:,.2f}")
    
    st.caption("O que você deseja fazer?")
    col_a, col_b = st.columns(2)
    
    # OPÇÃO A: TESTAR NA CALCULADORA (SEM SALVAR NO BANCO)
    if col_a.button("🧪 Testar Venda (Sem Salvar)", use_container_width=True):
        # 1. Atualiza a calculadora principal
        st.session_state.custo_final = custo_simulado
        st.session_state.sb_peso = f"{peso_s:.3f}"
        
        # 2. Configura taxas baseado na origem simulada
        if imp_s:
            st.session_state.sb_pis, st.session_state.sb_cofins = "2.10", "9.65"
            st.session_state.sb_origem = "Importação Própria"
        else:
            st.session_state.sb_pis, st.session_state.sb_cofins = "1.65", "7.60"
            st.session_state.sb_origem = "Nacional / Revenda"
            
        # 3. Ativa MODO SIMULAÇÃO e guarda RASCUNHO na memória
        st.session_state.is_simulation = True
        st.session_state.draft_cadastro = {
            'preco_nf': pc, 'frete': fr, 'ipi': ipi,
            'icms_prod': icms_p, 'peso': peso_s, 
            'lreal': lreal_s, 'imp_propria': imp_s
        }
        
        st.toast("Dados simulados carregados! Verifique o lucro.", icon="🧪")
        st.rerun()
        
    # OPÇÃO B: JÁ LEVAR PARA CADASTRO
    if col_b.button("➡️ Salvar e Cadastrar", use_container_width=True):
        st.session_state.draft_cadastro = {
            'preco_nf': pc, 'frete': fr, 'ipi': ipi,
            'icms_prod': icms_p, 'peso': peso_s, 
            'lreal': lreal_s, 'imp_propria': imp_s
        }
        st.switch_page("views/2_cadastro.py")

# ==============================================================================
# 4. SIDEBAR
# ==============================================================================
with st.sidebar:
    st.header("🛒 Produto & Config")
    
    # ABA INTELIGENTE: Se estiver em simulação, avisa.
    if st.session_state.get('is_simulation'):
        with st.container(border=True):
            st.info("🧪 **MODO SIMULAÇÃO**")
            st.caption("Você está testando um custo provisório.")
            if st.button("💾 Transformar em Cadastro Real", type="primary", use_container_width=True):
                st.switch_page("views/2_cadastro.py")
            if st.button("❌ Limpar Simulação"):
                st.session_state.is_simulation = False
                st.session_state.custo_final = 0.0
                st.rerun()
    
    tab_est, tab_test = st.tabs(["📦 Estoque", "🧪 Novo Teste"])
    
    with tab_est:
        try:
            df_prods = run_query("SELECT * FROM produtos ORDER BY nome")
            mapa = {f"{r['sku']} - {r['nome']}": r for _, r in df_prods.iterrows()} if not df_prods.empty else {}
            sel = st.selectbox("Buscar:", ["Selecione..."] + list(mapa.keys()))
            
            if sel != "Selecione...":
                dados = mapa[sel]
                b1, b2 = st.columns([1,1])
                if b1.button("⬇️ Carregar", use_container_width=True):
                    st.session_state.custo_final = float(dados['preco_final'])
                    if dados['peso']: st.session_state.sb_peso = f"{float(dados['peso']):.3f}"
                    if dados['icms_percent']: st.session_state.sb_icms = f"{float(dados['icms_percent']):.2f}"
                    
                    st.session_state.is_simulation = False # Reseta simulação pois carregou real
                    
                    eh_imp = dados.get('importacao_propria', False)
                    if eh_imp:
                        st.session_state.sb_pis, st.session_state.sb_cofins = "2.10", "9.65"
                        st.session_state.sb_origem = "Importação Própria"
                    else:
                        st.session_state.sb_pis, st.session_state.sb_cofins = "1.65", "7.60"
                        st.session_state.sb_origem = "Nacional / Revenda"
                    st.rerun()

                if b2.button("✏️ Editar", use_container_width=True):
                    dialog_atualizar(dados['id'], dados)
        except: st.error("Erro BD")
        
    with tab_test:
        if st.button("🚀 Iniciar Simulação", use_container_width=True):
            dialog_simular()

    st.divider()
    
    st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"], key="sb_canal")
    st.selectbox("Origem", ["Nacional / Revenda", "Importação Própria"], key="sb_origem", disabled=True) 
    
    c1, c2 = st.columns(2)
    st.text_input("ICMS (%)", key="sb_icms")
    st.text_input("DIFAL (%)", key="sb_difal")
    c3, c4 = st.columns(2)
    st.text_input("PIS (%)", key="sb_pis")
    st.text_input("COFINS (%)", key="sb_cofins")
    
    st.text_input("Peso (Kg)", key="sb_peso")
    st.toggle("⚡ Full", key="sb_full")
    
    if st.session_state.custo_final > 0:
        val = st.session_state.custo_final
        if st.session_state.get('is_simulation'):
            st.info(f"Custo Simulado: **R$ {val:,.2f}**")
        else:
            st.success(f"Custo Base: **R$ {val:,.2f}**")
    else:
        st.warning("Carregue ou Simule.")

# ==============================================================================
# 5. CORPO PRINCIPAL
# ==============================================================================
st.header("🧮 Calculadora de Margem de Precisão")

custo = st.session_state.custo_final
impostos = {'icms': st.session_state.sb_icms, 'pis': st.session_state.sb_pis, 'cofins': st.session_state.sb_cofins, 'difal': st.session_state.sb_difal}
peso = st.session_state.sb_peso
is_full = st.session_state.sb_full

col_mode, _ = st.columns([2, 3])
modo = "margem" if "Margem" in col_mode.radio("Meta:", ["Margem (%)", "Preço (R$)"], horizontal=True) else "preco"

st.divider()

if "Mercado Livre" in st.session_state.sb_canal:
    c_clas, c_prem = st.columns(2, gap="medium")
    
    # --- CLÁSSICO ---
    with c_clas:
        st.markdown("### 🔹 Clássico")
        com = st.text_input("Comissão %", key="com_cla")
        safe_com = com if com else "0.0"
        
        if modo == "preco":
            val = st.number_input("Preço Venda", 0.0, key="pr_cla")
            res = calcular_cenario(0, str(val), safe_com, "preco", "Mercado Livre", custo, impostos, peso, is_full, 0)
        else:
            marg = st.number_input("Margem %", 0.0, key="marg_cla")
            res = calcular_cenario(str(marg), 0, safe_com, "margem", "Mercado Livre", custo, impostos, peso, is_full, 0)
            
        card_resultado("Clássico", res)
        with st.expander("🧾 DRE Detalhado"):
            st.dataframe(criar_dre_detalhada(res['preco'], custo, safe_com, impostos, res['frete']).style.format({"Valor": "R$ {:,.2f}"}).applymap(lambda v: 'color: #ff4b4b' if v < 0 else 'color: #2e7d32; font-weight: bold', subset=['Valor']), hide_index=True)

    # --- PREMIUM ---
    with c_prem:
        st.markdown("### 🔸 Premium")
        com_p = st.text_input("Comissão %", key="com_pre")
        safe_com_p = com_p if com_p else "0.0"
        
        if modo == "preco":
            val_p = st.number_input("Preço Venda", 0.0, key="pr_pre")
            res_p = calcular_cenario(0, str(val_p), safe_com_p, "preco", "Mercado Livre", custo, impostos, peso, is_full, 0)
        else:
            marg_p = st.number_input("Margem %", 0.0, key="marg_pre")
            res_p = calcular_cenario(str(marg_p), 0, safe_com_p, "margem", "Mercado Livre", custo, impostos, peso, is_full, 0)

        card_resultado("Premium", res_p)
        with st.expander("🧾 DRE Detalhado"):
            st.dataframe(criar_dre_detalhada(res_p['preco'], custo, safe_com_p, impostos, res_p['frete']).style.format({"Valor": "R$ {:,.2f}"}).applymap(lambda v: 'color: #ff4b4b' if v < 0 else 'color: #2e7d32; font-weight: bold', subset=['Valor']), hide_index=True)
else:
    st.info("Selecione Mercado Livre para ver os cards.")