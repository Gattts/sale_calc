import streamlit as st
from utils.ui import carregar_css, card_resultado
from utils.calculos import calcular_cenario

st.set_page_config(page_title="Calculadora", layout="wide", page_icon="🧮")
carregar_css()

# Garante estado
if 'custo_final' not in st.session_state: st.session_state.custo_final = 0.0
# Inicializa chaves de texto
for k in ['sb_icms', 'sb_difal', 'sb_peso', 'sb_armaz', 'com_cla', 'marg_cla', 'pr_cla', 'com_pre', 'marg_pre', 'pr_pre', 'com_uni', 'marg_uni', 'pr_uni']:
    if k not in st.session_state: st.session_state[k] = ""

# --- SIDEBAR ESPECÍFICA DA CALCULADORA ---
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
    
    st.info(f"💰 Custo Base: **R$ {st.session_state.custo_final:,.2f}**")

# --- CONTEÚDO DA PÁGINA ---
st.title("🧮 Calculadora de Margem")

if st.session_state.custo_final <= 0: 
    st.warning("⚠️ Custo Base zerado. Vá em 'Cadastro' para selecionar um produto.")

tipo = st.radio("Meta:", ["Margem (%)", "Preço (R$)"], horizontal=True, label_visibility="collapsed")
modo = "margem" if "Margem" in tipo else "preco"

# Prepara dados
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
