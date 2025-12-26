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
    'sb_canal': '🟡 Mercado Livre',
    'sb_icms': '18.00', 'sb_difal': '0.00',
    'sb_pis': '1.65', 'sb_cofins': '7.60',
    'sb_peso': '0.300', 'sb_full': False,
    'com_cla': '11.5', 'marg_cla': 15.0, 
    'pr_cla': 0.0,
    'com_pre': '16.5', 'marg_pre': 20.0, 
    'pr_pre': 0.0,
    'com_std': '14.0', 'marg_std': 15.0, 'pr_std': 0.0,
    'upd_pc': '', 'upd_fr': '', 'upd_ipi': '', 'upd_peso': '', 
    'upd_icmsp': '', 'upd_icmsf': '', 'upd_out': '', 'upd_st': '', 'upd_lreal': True,
    'is_simulation': False,
    'draft_cadastro': {}
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

try:
    if isinstance(st.session_state.marg_cla, str): st.session_state.marg_cla = float(st.session_state.marg_cla)
    if isinstance(st.session_state.marg_pre, str): st.session_state.marg_pre = float(st.session_state.marg_pre)
    if isinstance(st.session_state.marg_std, str): st.session_state.marg_std = float(st.session_state.marg_std)
except: pass

# ==============================================================================
# 2. FUNÇÕES AUXILIARES & CALLBACKS
# ==============================================================================
def safe_float(valor):
    if valor is None or valor == "": return 0.0
    if isinstance(valor, (float, int)): return float(valor)
    try: return float(str(valor).replace(',', '.'))
    except: return 0.0

# --- CALLBACK PARA CARREGAR PRODUTO SEM ERRO DE WIDGET ---
def callback_carregar(dados):
    """Atualiza o session_state ANTES da tela ser redesenhada."""
    st.session_state.custo_final = safe_float(dados['preco_final'])
    st.session_state.sb_peso = f"{safe_float(dados['peso']):.3f}"
    st.session_state.sb_icms = f"{safe_float(dados['icms_percent']):.2f}"
    st.session_state.is_simulation = False 
    
    eh_imp = dados.get('importacao_propria', False)
    if eh_imp:
        st.session_state.sb_pis = "2.10"
        st.session_state.sb_cofins = "9.65"
        st.session_state.sb_origem = "Importação Própria"
    else:
        st.session_state.sb_pis = "1.65"
        st.session_state.sb_cofins = "7.60"
        st.session_state.sb_origem = "Nacional / Revenda"

def criar_dre_detalhada(preco_venda, custo_prod, comissao_pct, impostos_dict, frete_saida):
    fat = safe_float(preco_venda)
    custo_m = safe_float(custo_prod)
    frete = safe_float(frete_saida)
    pc_com = safe_float(comissao_pct)
    
    v_icms = fat * (safe_float(impostos_dict.get('icms')) / 100)
    v_pis = fat * (safe_float(impostos_dict.get('pis')) / 100)
    v_cofins = fat * (safe_float(impostos_dict.get('cofins')) / 100)
    v_difal = fat * (safe_float(impostos_dict.get('difal')) / 100)
    
    v_comissao = fat * (pc_com / 100)
    v_fixa = 0.0
    if "Mercado Livre" in st.session_state.sb_canal and 0 < fat < 79.00: v_fixa = 6.00 
    if "Shopee" in st.session_state.sb_canal: v_fixa = 3.00 
    
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
@st.dialog("Editar Produto")
def dialog_atualizar(prod_id, dados):
    st.caption(f"Editando: {dados['nome']}")
    if not st.session_state.upd_pc:
        st.session_state.upd_pc = f"{safe_float(dados['preco_partida']):.2f}"
        st.session_state.upd_ipi = f"{safe_float(dados['ipi_percent']):.2f}"
        st.session_state.upd_icmsp = f"{safe_float(dados['icms_percent']):.2f}"
        st.session_state.upd_peso = f"{safe_float(dados['peso']):.3f}"

    c1, c2, c3 = st.columns(3)
    st.text_input("Preço Compra", key="upd_pc")
    st.text_input("Frete Compra", key="upd_fr")
    st.text_input("IPI (%)", key="upd_ipi")
    c4, c5 = st.columns(2)
    st.text_input("Peso (Kg)", key="upd_peso")
    st.text_input("ICMS Prod (%)", key="upd_icmsp")
    lreal = st.toggle("Lucro Real", value=True, key="upd_lreal")
    is_imp = st.toggle("Importação Própria", value=(True if dados.get('importacao_propria') else False))

    if st.button("Salvar e Usar", type="primary"):
        res = calcular_custo_aquisicao(st.session_state.upd_pc, st.session_state.upd_fr, st.session_state.upd_ipi, "0", "0", "0", st.session_state.upd_icmsp, lreal)
        
        sql = "UPDATE produtos SET preco_partida=:pp, ipi_percent=:ipi, icms_percent=:icms, preco_final=:pf, peso=:peso, importacao_propria=:imp WHERE id=:id"
        params = {
            "pp": safe_float(st.session_state.upd_pc), "ipi": safe_float(st.session_state.upd_ipi), 
            "icms": safe_float(st.session_state.upd_icmsp), "pf": res['custo_final'], 
            "peso": safe_float(st.session_state.upd_peso), "imp": is_imp, "id": prod_id
        }
        run_command(sql, params)
        
        # Atualiza sessão manualmente para refletir na hora
        st.session_state.custo_final = res['custo_final']
        st.session_state.sb_peso = st.session_state.upd_peso
        st.session_state.is_simulation = False 
        if is_imp:
            st.session_state.sb_pis, st.session_state.sb_cofins = "2.10", "9.65"
            st.session_state.sb_origem = "Importação Própria"
        else:
            st.session_state.sb_pis, st.session_state.sb_cofins = "1.65", "7.60"
            st.session_state.sb_origem = "Nacional / Revenda"
            
        st.toast("Atualizado!", icon="✅")
        st.rerun()

@st.dialog("Simular Compra (Teste)")
def dialog_simular():
    st.caption("Simule custo e impostos.")
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
    res = calcular_custo_aquisicao(pc, fr, ipi, 0, 0, 0, icms_p, lreal_s)
    custo_simulado = res['custo_final']
    st.metric("Custo Final Estimado", f"R$ {custo_simulado:,.2f}")
    
    col_a, col_b = st.columns(2)
    if col_a.button("Testar Venda", use_container_width=True):
        st.session_state.custo_final = custo_simulado
        st.session_state.sb_peso = f"{peso_s:.3f}"
        if imp_s:
            st.session_state.sb_pis, st.session_state.sb_cofins = "2.10", "9.65"
            st.session_state.sb_origem = "Importação Própria"
        else:
            st.session_state.sb_pis, st.session_state.sb_cofins = "1.65", "7.60"
            st.session_state.sb_origem = "Nacional / Revenda"
        st.session_state.is_simulation = True
        st.session_state.draft_cadastro = {'preco_nf': pc, 'frete': fr, 'ipi': ipi, 'icms_prod': icms_p, 'peso': peso_s, 'lreal': lreal_s, 'imp_propria': imp_s}
        st.rerun()
        
    if col_b.button("Salvar e Cadastrar", use_container_width=True):
        st.session_state.draft_cadastro = {'preco_nf': pc, 'frete': fr, 'ipi': ipi, 'icms_prod': icms_p, 'peso': peso_s, 'lreal': lreal_s, 'imp_propria': imp_s}
        st.switch_page("views/2_cadastro.py")

# ==============================================================================
# 4. SIDEBAR (ORGANIZADA)
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Configurações de Venda")
    
    # --- BLOCO 1: INPUTS (Desenhados primeiro) ---
    st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"], key="sb_canal")
    st.selectbox("Origem", ["Nacional / Revenda", "Importação Própria"], key="sb_origem", disabled=True) 
    
    c1, c2 = st.columns(2)
    st.text_input("ICMS (%)", key="sb_icms")
    st.text_input("DIFAL (%)", key="sb_difal")
    c3, c4 = st.columns(2)
    st.text_input("PIS (%)", key="sb_pis")
    st.text_input("COFINS (%)", key="sb_cofins")
    
    st.divider()

    # --- BLOCO 2: CARREGAMENTO ---
    st.header("📦 Produto")
    
    if st.session_state.get('is_simulation'):
        with st.container(border=True):
            st.info("🧪 **MODO SIMULAÇÃO**")
            if st.button("Cadastrar Item", type="primary", use_container_width=True):
                st.switch_page("views/2_cadastro.py")
            if st.button("Limpar"):
                st.session_state.is_simulation = False
                st.session_state.custo_final = 0.0
                st.rerun()
    
    tab_est, tab_test = st.tabs(["📦 Estoque", "🧪 Novo Teste"])
    
    with tab_est:
        try:
            df_prods = run_query("SELECT * FROM produtos ORDER BY nome")
            if not df_prods.empty:
                mapa = {f"{r['sku']} - {r['nome']}": r for _, r in df_prods.iterrows()}
                sel = st.selectbox("Buscar:", ["Selecione..."] + list(mapa.keys()))
                
                if sel != "Selecione...":
                    dados = mapa[sel]
                    b1, b2 = st.columns([1,1])
                    
                    # --- BOTÃO COM CALLBACK (CORREÇÃO DO ERRO) ---
                    # Em vez de 'if button:', usamos 'on_click=funcao'
                    b1.button("Carregar", use_container_width=True, on_click=callback_carregar, args=(dados,))
                        
                    if b2.button("Editar", use_container_width=True):
                        dialog_atualizar(dados['id'], dados)
            else:
                st.warning("Nenhum produto cadastrado.")
        except Exception as e: 
            st.error(f"Erro BD: {e}") 
            
    with tab_test:
        if st.button("Iniciar Simulação", use_container_width=True):
            dialog_simular()

    # --- BLOCO 3: LOGÍSTICA ---
    st.divider()
    st.text_input("Peso (Kg)", key="sb_peso")
    st.toggle("⚡ Full", key="sb_full")
    
    # Feedback
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
    st.markdown(f"### 🛍️ Venda em: {st.session_state.sb_canal}")
    c_std, _ = st.columns([1, 1]) 
    
    with c_std:
        com_s = st.text_input("Comissão do Canal (%)", key="com_std")
        safe_com_s = com_s if com_s else "0.0"
        
        if modo == "preco":
            val_s = st.number_input("Preço Venda", 0.0, key="pr_std")
            res_s = calcular_cenario(0, str(val_s), safe_com_s, "preco", st.session_state.sb_canal, custo, impostos, peso, is_full, 0)
        else:
            marg_s = st.number_input("Margem Meta %", 0.0, key="marg_std")
            res_s = calcular_cenario(str(marg_s), 0, safe_com_s, "margem", st.session_state.sb_canal, custo, impostos, peso, is_full, 0)

        card_resultado("Resultado", res_s)
        with st.expander("🧾 DRE Detalhado"):
             st.dataframe(criar_dre_detalhada(res_s['preco'], custo, safe_com_s, impostos, res_s['frete']).style.format({"Valor": "R$ {:,.2f}"}).applymap(lambda v: 'color: #ff4b4b' if v < 0 else 'color: #2e7d32; font-weight: bold', subset=['Valor']), hide_index=True)
