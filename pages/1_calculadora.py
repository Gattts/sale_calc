import streamlit as st
from utils.ui import carregar_css, card_resultado
from utils.calculos import calcular_cenario
from utils.db import run_query # <--- Adicionado para buscar produtos

st.set_page_config(page_title="Calculadora", layout="wide", page_icon="🧮")
carregar_css()

# Garante estado inicial das variáveis
if 'custo_final' not in st.session_state: st.session_state.custo_final = 0.0

keys_sidebar = ['sb_icms', 'sb_difal', 'sb_peso', 'sb_armaz', 'sb_full']
keys_inputs = ['com_cla', 'marg_cla', 'pr_cla', 'com_pre', 'marg_pre', 'pr_pre', 'com_uni', 'marg_uni', 'pr_uni']

for k in keys_sidebar + keys_inputs:
    if k not in st.session_state: st.session_state[k] = ""

# ==============================================================================
# 1. BUSCA RÁPIDA DE PRODUTOS (Recurso Restaurado)
# ==============================================================================
st.title("🧮 Calculadora de Margem")

with st.expander("📦 Importar Produto do Estoque (Preenchimento Automático)"):
    # Busca produtos no banco
    try:
        df_prods = run_query("SELECT id, sku, nome, preco_final, peso, icms_percent FROM produtos ORDER BY nome")
        
        if not df_prods.empty:
            # Cria um dicionário para o Selectbox: "SKU - Nome" -> Linha de Dados
            mapa_produtos = {f"{row['sku']} - {row['nome']}": row for _, row in df_prods.iterrows()}
            
            prod_selecionado = st.selectbox("Selecione um produto:", ["Selecione..."] + list(mapa_produtos.keys()))
            
            if prod_selecionado != "Selecione..." and st.button("⬇️ Carregar Dados deste Produto"):
                dados = mapa_produtos[prod_selecionado]
                
                # --- O ESPELHAMENTO ACONTECE AQUI ---
                st.session_state.custo_final = float(dados['preco_final'])
                
                # Atualiza Peso na Sidebar
                if dados['peso'] and float(dados['peso']) > 0:
                    st.session_state.sb_peso = f"{float(dados['peso']):.3f}"
                else:
                    st.session_state.sb_peso = "0.300"
                
                # Atualiza ICMS na Sidebar
                if dados['icms_percent'] and float(dados['icms_percent']) > 0:
                    st.session_state.sb_icms = f"{float(dados['icms_percent']):.2f}"
                else:
                    st.session_state.sb_icms = "18.00"
                
                st.toast(f"Dados de '{dados['sku']}' carregados!", icon="✅")
                st.rerun() # Recarrega a página para aplicar os valores nos inputs
        else:
            st.warning("Nenhum produto cadastrado no banco.")
            
    except Exception as e:
        st.error(f"Erro ao buscar produtos: {e}")

st.markdown("---")

# ==============================================================================
# 2. SIDEBAR E PARÂMETROS
# ==============================================================================
with st.sidebar:
    st.title("⚙️ Configurações")
    canal = st.selectbox("Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🌐 Site Próprio"], key="sb_canal")
    
    with st.expander("🛠️ Parâmetros & Tributos", expanded=True):
        c1, c2 = st.columns(2)
        # O valor (value) vem do session_state, permitindo o preenchimento automático
        st.text_input("ICMS (%)", key="sb_icms")
        st.text_input("DIFAL (%)", key="sb_difal")
        
        c3, c4 = st.columns(2)
        st.text_input("Peso (Kg)", key="sb_peso")
        st.text_input("Armaz. (%)", key="sb_armaz")
        st.toggle("⚡ Full Fulfillment", key="sb_full")
    
    # Mostra o Custo Base atual
    if st.session_state.custo_final > 0:
        st.success(f"💰 Custo Base: **R$ {st.session_state.custo_final:,.2f}**")
    else:
        st.info("💰 Custo Base: R$ 0,00")

# ==============================================================================
# 3. LÓGICA DE CÁLCULO
# ==============================================================================

if st.session_state.custo_final <= 0: 
    st.warning("⚠️ Custo Base zerado. Importe um produto acima ou digite os custos manualmente.")

tipo = st.radio("Meta:", ["Margem (%)", "Preço (R$)"], horizontal=True, label_visibility="collapsed")
modo = "margem" if "Margem" in tipo else "preco"

# Prepara dados (com valores padrão caso vazio)
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
