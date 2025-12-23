import streamlit as st
from datetime import date
import time
from utils.ui import carregar_css
from utils.db import run_query, run_command
from utils.calculos import calcular_custo_aquisicao, str_to_float

st.set_page_config(page_title="Cadastro de Produtos", layout="wide", page_icon="📦")
carregar_css()

# Init Session State
keys = ['in_sku', 'in_nome', 'in_forn', 'in_nf', 'in_qtd', 'pc_cad', 'fr_cad', 'ipi_cad', 
        'peso_cad', 'icmsp_cad', 'icmsf_cad', 'out_cad', 'st_cad', 'upd_pc', 'upd_fr', 
        'upd_ipi', 'upd_peso', 'upd_icmsp', 'upd_icmsf', 'upd_out', 'upd_st']
for k in keys:
    if k not in st.session_state: st.session_state[k] = ""

# --- MODAL ATUALIZAÇÃO ---
@st.dialog("✏️ Atualizar Custos do Produto")
def dialog_atualizar_produto(prod_id, dados_iniciais):
    st.caption(f"Editando: {dados_iniciais['nome']}")
    
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
            for k in ['upd_pc', 'upd_fr', 'upd_ipi', 'upd_peso', 'upd_icmsp', 'upd_icmsf', 'upd_out', 'upd_st']:
                st.session_state[k] = ""
            time.sleep(1)
            st.rerun()

# --- CONTEÚDO PRINCIPAL ---
st.title("📦 Cadastro de Produtos")

# Carrega Produtos
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
    # MODO PRODUTO EXISTENTE (CARD APENAS)
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
        
        if b_col1.button("🚀 Usar na Calculadora", use_container_width=True):
            st.session_state.custo_final = float(d['preco_final'])
            st.session_state.sb_peso = f"{d['peso']:.3f}" if (d['peso'] and float(d['peso']) > 0) else "0.300"
            st.session_state.sb_icms = f"{d['icms_percent']:.2f}" if (d['icms_percent'] and float(d['icms_percent']) > 0) else "18.00"
            st.toast(f"Valores de '{d['sku']}' enviados!", icon="🚀")
            st.switch_page("pages/1_🧮_Calculadora.py") # Redireciona automatico!

        if b_col2.button("✏️ Atualizar Custos", type="primary", use_container_width=True):
            dialog_atualizar_produto(d['id'], d)