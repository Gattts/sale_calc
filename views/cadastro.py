import streamlit as st
from datetime import date
from utils.db import run_command, run_query
from utils.calculos import calcular_custo_aquisicao, str_to_float

st.header("📦 Cadastro de Produtos")

# --- VERIFICAÇÃO DE RASCUNHO (Vindo do Teste) ---
draft = st.session_state.get('draft_cadastro', {})
# Valores padrão: Se tiver no draft usa, senão zero
def_pnf = float(draft.get('preco_nf', 0.0))
def_frete = float(draft.get('frete', 0.0))
def_ipi = float(draft.get('ipi', 0.0))
def_icms = float(draft.get('icms_prod', 0.0))
def_peso = float(draft.get('peso', 0.0))
def_lreal = draft.get('lreal', True)
def_imp = draft.get('imp_propria', False)

if draft:
    st.info("ℹ️ Dados importados da Simulação de Compra. Complete o cadastro.")
    # Limpa o draft para não persistir se der F5
    del st.session_state['draft_cadastro']

# --- Formulário de Cadastro ---
with st.container(border=True):
    st.subheader("Novo Produto")
    
    # Linha 1: Identificação
    c1, c2, c3 = st.columns([1, 2, 1])
    sku = c1.text_input("SKU / Código")
    nome = c2.text_input("Nome do Produto")
    forn = c3.text_input("Fornecedor")

    # Linha 2: Valores Fiscais da Compra (COM PREENCHIMENTO AUTOMÁTICO)
    c4, c5, c6, c7 = st.columns(4)
    preco_nf = c4.number_input("Preço na NF (R$)", min_value=0.0, value=def_pnf)
    ipi = c5.number_input("IPI (%)", min_value=0.0, value=def_ipi)
    icms_prod = c6.number_input("ICMS Prod. (%)", min_value=0.0, value=def_icms, help="Crédito de ICMS do produto")
    icms_frete = c7.number_input("ICMS Frete (%)", min_value=0.0)

    # Linha 3: Custos Extras e Logística
    c8, c9, c10, c11 = st.columns(4)
    frete = c8.number_input("Frete Compra (R$)", min_value=0.0, value=def_frete)
    outros = c9.number_input("Outros Custos (R$)", min_value=0.0)
    st_val = c10.number_input("ST (R$)", min_value=0.0)
    peso = c11.number_input("Peso (Kg)", min_value=0.0, value=def_peso, format="%.3f")

    st.divider()

    # Linha 4: Configurações Fiscais Específicas
    col_check1, col_check2 = st.columns(2)
    lreal = col_check1.toggle("Lucro Real (Credita Impostos?)", value=def_lreal)
    imp_propria = col_check2.toggle("🌍 Importação Própria?", value=def_imp)

    # Botão Salvar
    if st.button("💾 Salvar Produto no Estoque", type="primary", use_container_width=True):
        if not sku or not nome:
            st.error("Preencha pelo menos SKU e Nome.")
        else:
            res = calcular_custo_aquisicao(preco_nf, frete, ipi, outros, st_val, icms_frete, icms_prod, lreal)
            custo_final = res['custo_final']

            sql = """
                INSERT INTO produtos 
                (sku, nome, fornecedor, preco_partida, ipi_percent, icms_percent, 
                 preco_final, peso, data_compra, quantidade, importacao_propria)
                VALUES 
                (:sku, :nome, :forn, :pnf, :ipi, :icms, :pf, :peso, :hj, 0, :imp)
            """
            params = {"sku": sku, "nome": nome, "forn": forn, "pnf": preco_nf, "ipi": ipi, "icms": icms_prod, "pf": custo_final, "peso": peso, "hj": date.today(), "imp": imp_propria}
            
            if run_command(sql, params):
                st.success(f"Produto {sku} cadastrado! Custo Final: R$ {custo_final:.2f}")

# --- Tabela ---
st.divider()
st.subheader("Últimos Cadastrados")
df = run_query("SELECT sku, nome, preco_final, peso, importacao_propria FROM produtos ORDER BY id DESC LIMIT 10")
st.dataframe(df, use_container_width=True, hide_index=True)