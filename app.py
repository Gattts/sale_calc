import streamlit as st
import json
import pandas as pd
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Calculadora E-commerce", layout="wide", page_icon="🏷️")

# ==============================================================================
# 🧮 LÓGICA CENTRAL DE CUSTOS (Reutilizável)
# ==============================================================================
def calcular_custo_aquisicao(preco_compra, frete, ipi_pct, outros, st_val, icms_frete, icms_prod, pis_pct, cofins_pct, is_lucro_real):
    """Calcula o custo final contábil do produto."""
    
    valor_ipi = preco_compra * (ipi_pct / 100)
    preco_medio = preco_compra + frete + valor_ipi + outros + st_val
    
    credito_icms = 0.0
    credito_pis = 0.0
    credito_cofins = 0.0
    
    if is_lucro_real:
        # Crédito ICMS (Frete + Produto)
        c_icms_frete = frete * (icms_frete / 100)
        c_icms_prod = preco_compra * (icms_prod / 100)
        credito_icms = c_icms_frete + c_icms_prod
        
        # Crédito PIS/COFINS (Sobre produto)
        credito_pis = preco_compra * (pis_pct / 100)
        credito_cofins = preco_compra * (cofins_pct / 100)
    
    total_creditos = credito_icms + credito_pis + credito_cofins
    custo_final = preco_medio - total_creditos
    
    return {
        'custo_final': custo_final,
        'preco_medio': preco_medio,
        'credito_icms_total': credito_icms,
        'credito_pis': credito_pis,
        'credito_cofins': credito_cofins,
        'fornecedor_base': preco_compra,
        # Guarda as taxas usadas para usar na venda depois
        'pis_rate': pis_pct,
        'cofins_rate': cofins_pct
    }

# ==============================================================================
# 💾 GERENCIAMENTO DE DADOS (JSON)
# ==============================================================================
if 'db_produtos' not in st.session_state:
    st.session_state['db_produtos'] = {}

def carregar_banco_dados(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state['db_produtos'] = data
            st.toast("Banco de dados atualizado com sucesso!", icon="✅")
        except:
            st.error("Erro ao ler arquivo JSON.")

def converter_db_para_json():
    return json.dumps(st.session_state['db_produtos'], indent=4).encode('utf-8')

# --- INICIALIZAÇÃO DE ESTADO DA CALCULADORA ---
if 'custo_produto_final' not in st.session_state:
    st.session_state['custo_produto_final'] = 99.00
if 'detalhes_custo' not in st.session_state:
    st.session_state['detalhes_custo'] = {
        'preco_medio': 99.00, 'credito_icms_total': 0.0, 'credito_pis': 0.0, 'credito_cofins': 0.0, 
        'pis_rate': 1.65, 'cofins_rate': 7.60, 'fornecedor_base': 99.00
    }

# ==============================================================================
# 🎨 UI E ESTILOS
# ==============================================================================
# Tabela de Fretes ML (Mantida)
TABELA_FRETE_ML = {
    "79-99": [(0.3, 11.97), (0.5, 12.87), (1.0, 13.47), (2.0, 14.07), (3.0, 14.97), (4.0, 16.17), (5.0, 17.07), (9.0, 26.67), (150.0, 113.97)],
    "100-119": [(0.3, 13.97), (0.5, 15.02), (1.0, 15.72), (2.0, 16.42), (3.0, 17.47), (4.0, 18.87), (5.0, 19.92), (9.0, 31.12), (150.0, 125.27)],
    "120-149": [(0.3, 15.96), (0.5, 17.16), (1.0, 17.96), (2.0, 18.76), (3.0, 19.96), (4.0, 21.56), (5.0, 22.76), (9.0, 35.56), (150.0, 151.96)],
    "150-199": [(0.3, 17.96), (0.5, 19.31), (1.0, 20.21), (2.0, 21.11), (3.0, 22.46), (4.0, 24.26), (5.0, 25.61), (9.0, 40.01), (150.0, 161.06)],
    "200+": [(0.3, 19.95), (0.5, 21.45), (1.0, 22.45), (2.0, 23.45), (3.0, 24.95), (4.0, 26.95), (5.0, 28.45), (9.0, 44.45), (150.0, 189.95)]
} # (Simplifiquei a visualização aqui, mas mantenha a tabela completa no seu código)

with st.sidebar:
    c_head, c_tog = st.columns([2,1])
    c_head.header("⚙️ Config.")
    dark_mode = c_tog.toggle("🌘", value=False)
    
    canal = st.selectbox("🏪 Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🔵 Magalu", "🟠 KaBuM!", "🌐 Site Próprio"])
    st.markdown("---")
    
    # SELEÇÃO DE PRODUTO DO BANCO DE DADOS
    st.subheader("📦 Selecionar Produto")
    
    # Opções do selectbox
    opcoes_produtos = ["Novo / Manual"] + list(st.session_state['db_produtos'].keys())
    produto_selecionado = st.selectbox("Buscar no Cadastro", opcoes_produtos)
    
    # Lógica de Carregamento
    if produto_selecionado != "Novo / Manual":
        dados_prod = st.session_state['db_produtos'][produto_selecionado]
        # Atualiza a calculadora com os dados salvos
        st.session_state['custo_produto_final'] = dados_prod['custo_final']
        st.session_state['detalhes_custo'] = dados_prod['detalhes']
        # Peso também pode vir do cadastro se quiser implementar
        
    custo_display = st.session_state['custo_produto_final']
    st.markdown(f"""<div style="background:#f0f2f6;padding:10px;border-radius:8px;border:1px solid #ddd;margin-bottom:10px;color:#333;">
    <small>Custo Atual</small><br><b style="font-size:1.4em;color:#1e3a8a">R$ {custo_display:,.2f}</b></div>""", unsafe_allow_html=True)

    # ... (Resto da Sidebar: Tributos, Logística, etc) ...
    st.subheader("💸 Tributos Venda")
    col_t1, col_t2 = st.columns(2)
    icms_venda_pct = col_t1.number_input("ICMS (%)", 18.0, step=0.5)
    difal_pct = col_t2.number_input("DIFAL (%)", 0.0, step=0.5)
    
    st.subheader("🚚 Logística")
    is_fulfillment = st.toggle("⚡ Envio Full?", value=False)
    col_l1, col_l2 = st.columns(2)
    peso_input = col_l1.number_input("Peso (Kg)", 0.3, step=0.1)
    armazenagem_pct = col_l2.number_input("Armaz. (%)", 0.0, step=0.1)
    
    st.markdown("---")
    # UPLOAD/DOWNLOAD DO BANCO
    with st.expander("💾 Backup / Dados"):
        st.download_button("Baixar Cadastro (JSON)", data=converter_db_para_json(), file_name="db_produtos.json", mime="application/json")
        uploaded_db = st.file_uploader("Carregar Backup", type=["json"])
        if uploaded_db:
            carregar_banco_dados(uploaded_db)

# CSS (Mantendo o seu CSS de Dark Mode e Accordion)
css_variables = "--primary-color: #1e3a8a; --card-bg: #ffffff; --text-color: #333;" 
if dark_mode: css_variables = "--primary-color: #60a5fa; --card-bg: #1f2937; --text-color: #e2e8f0;"
st.markdown(f"<style>:root{{{css_variables}}} /*...SEU CSS COMPLETO AQUI...*/ </style>", unsafe_allow_html=True)


# ==============================================================================
# 🖥️ ÁREA PRINCIPAL (ABAS)
# ==============================================================================
tab_calc, tab_cadastro = st.tabs(["🧮 Calculadora", "📝 Cadastro de Custos"])

# --- ABA 1: CALCULADORA (Sua lógica existente) ---
with tab_calc:
    # AQUI VAI TODO O CÓDIGO DA CALCULADORA (FUNÇÕES DE CÁLCULO E LAYOUT)
    # Função obter_frete_ml, calcular_cenario, render_card_html...
    # (Para economizar espaço, imagine que o código da resposta anterior está aqui)
    
    # ... (Copie o bloco "FUNÇÃO HELPER: CONSULTAR TABELA ML" até o final do código anterior) ...
    # Placeholder só pra exemplificar onde entra:
    # nome_canal_titulo = canal...
    # calcular_cenario(...)
    pass 


# --- ABA 2: CADASTRO DE PRODUTOS (NOVA) ---
with tab_cadastro:
    st.markdown("## 📝 Editor de Custos de Produtos")
    st.caption("Cadastre ou edite produtos aqui. Os dados salvos aparecerão na busca da calculadora.")
    
    col_form, col_resumo = st.columns([2, 1], gap="large")
    
    with col_form:
        with st.container(border=True):
            nome_prod = st.text_input("Nome do Produto (ID)", value=produto_selecionado if produto_selecionado != "Novo / Manual" else "")
            
            st.divider()
            
            l_real = st.toggle("Lucro Real?", value=True, key="regime_cad")
            
            c1, c2, c3 = st.columns(3)
            p_compra = c1.number_input("Preço Compra ($)", 0.0, step=1.0, key="pc_cad")
            p_frete = c2.number_input("Frete Entrada ($)", 0.0, step=0.5, key="fr_cad")
            p_ipi = c3.number_input("IPI (%)", 0.0, step=0.5, key="ipi_cad")
            
            c4, c5 = st.columns(2)
            p_outros = c4.number_input("Outros Custos ($)", 0.0, step=1.0, key="out_cad")
            p_st = c5.number_input("ICMS ST ($)", 0.0, step=1.0, key="st_cad")
            
            st.markdown("#### Créditos")
            cc1, cc2 = st.columns(2)
            icms_fr_pct = cc1.number_input("ICMS Frete (%)", 12.0, step=0.5, key="icmsf_cad")
            # Trava ICMS
            travado = (p_st > 0)
            icms_pr_pct = cc2.number_input("ICMS Produto (%)", 0.0 if travado else 12.0, step=0.5, disabled=travado, key="icmsp_cad")
            
            is_imp = st.toggle("Importação?", False, key="imp_cad")
            pis_c = 2.10 if is_imp else 1.65
            cofins_c = 9.65 if is_imp else 7.60
            st.caption(f"PIS: {pis_c}% | COFINS: {cofins_c}%")

            # Botão Calcular (Preview)
            if st.button("Simular Custo", use_container_width=True):
                res = calcular_custo_aquisicao(p_compra, p_frete, p_ipi, p_outros, p_st, icms_fr_pct, icms_pr_pct, pis_c, cofins_c, l_real)
                st.session_state['preview_cadastro'] = res
            
    with col_resumo:
        if 'preview_cadastro' in st.session_state:
            res = st.session_state['preview_cadastro']
            st.info(f"### Custo Final: R$ {res['custo_final']:.2f}")
            st.write(f"Preço Médio: R$ {res['preco_medio']:.2f}")
            st.success(f"Créditos Recuperados: R$ {res['credito_icms_total'] + res['credito_pis'] + res['credito_cofins']:.2f}")
            
            st.divider()
            
            if st.button("💾 SALVAR NO BANCO", type="primary", use_container_width=True):
                if nome_prod:
                    # Estrutura do Objeto Salvo
                    novo_item = {
                        'custo_final': res['custo_final'],
                        'detalhes': res # Salva todos os detalhes fiscais
                    }
                    # Salva no Dicionário da Sessão
                    st.session_state['db_produtos'][nome_prod] = novo_item
                    st.toast(f"Produto '{nome_prod}' salvo!", icon="💾")
                    st.rerun() # Atualiza a tela para aparecer na lista
                else:
                    st.error("Digite um nome para o produto.")
            
            if produto_selecionado in st.session_state['db_produtos']:
                if st.button("🗑️ Excluir deste cadastro", type="secondary"):
                    del st.session_state['db_produtos'][produto_selecionado]
                    st.rerun()
