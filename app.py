import streamlit as st
import json
import pandas as pd
from io import BytesIO

# ==============================================================================
# 1. CONFIGURAÇÃO E DADOS ESTÁTICOS
# ==============================================================================
st.set_page_config(page_title="Calculadora E-commerce", layout="wide", page_icon="🏷️")

# Tabela de Fretes Mercado Livre (Atualizada)
TABELA_FRETE_ML = {
    "79-99": [
        (0.3, 11.97), (0.5, 12.87), (1.0, 13.47), (2.0, 14.07), (3.0, 14.97),
        (4.0, 16.17), (5.0, 17.07), (9.0, 26.67), (13.0, 39.57), (17.0, 44.07),
        (23.0, 51.57), (30.0, 59.37), (40.0, 61.17), (50.0, 63.27), (60.0, 67.47),
        (70.0, 72.27), (80.0, 75.57), (90.0, 83.97), (100.0, 95.97), (125.0, 107.37), (150.0, 113.97)
    ],
    "100-119": [
        (0.3, 13.97), (0.5, 15.02), (1.0, 15.72), (2.0, 16.42), (3.0, 17.47),
        (4.0, 18.87), (5.0, 19.92), (9.0, 31.12), (13.0, 46.17), (17.0, 51.42),
        (23.0, 60.17), (30.0, 69.27), (40.0, 71.37), (50.0, 73.82), (60.0, 78.72),
        (70.0, 84.32), (80.0, 88.17), (90.0, 97.97), (100.0, 111.97), (125.0, 125.27)
    ],
    "120-149": [
        (0.3, 15.96), (0.5, 17.16), (1.0, 17.96), (2.0, 18.76), (3.0, 19.96),
        (4.0, 21.56), (5.0, 22.76), (9.0, 35.56), (13.0, 52.76), (17.0, 58.76),
        (23.0, 68.76), (30.0, 79.16), (40.0, 81.56), (50.0, 84.36), (60.0, 89.96),
        (70.0, 96.36), (80.0, 100.76), (90.0, 111.96), (100.0, 127.96), (125.0, 143.16), (150.0, 151.96)
    ],
    "150-199": [
        (0.3, 17.96), (0.5, 19.31), (1.0, 20.21), (2.0, 21.11), (3.0, 22.46),
        (4.0, 24.26), (5.0, 25.61), (9.0, 40.01), (13.0, 59.36), (17.0, 66.11),
        (23.0, 77.36), (30.0, 89.06), (40.0, 91.76), (50.0, 94.91), (60.0, 101.21),
        (70.0, 108.41), (80.0, 113.36), (90.0, 125.96), (100.0, 143.96), (125.0, 161.06)
    ],
    "200+": [
        (0.3, 19.95), (0.5, 21.45), (1.0, 22.45), (2.0, 23.45), (3.0, 24.95),
        (4.0, 26.95), (5.0, 28.45), (9.0, 44.45), (13.0, 65.95), (17.0, 73.45),
        (23.0, 85.95), (30.0, 98.95), (40.0, 101.95), (50.0, 105.45), (60.0, 112.45),
        (70.0, 120.45), (80.0, 125.95), (90.0, 139.95), (100.0, 159.95), (125.0, 178.95), (150.0, 189.95)
    ]
}

# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO E LÓGICA
# ==============================================================================

def calcular_custo_aquisicao(preco_compra, frete, ipi_pct, outros, st_val, icms_frete, icms_prod, pis_pct, cofins_pct, is_lucro_real):
    """Calcula o custo contábil (usado na aba Cadastro)."""
    valor_ipi = preco_compra * (ipi_pct / 100)
    preco_medio = preco_compra + frete + valor_ipi + outros + st_val
    
    credito_icms = 0.0
    credito_pis = 0.0
    credito_cofins = 0.0
    
    if is_lucro_real:
        c_icms_frete = frete * (icms_frete / 100)
        c_icms_prod = preco_compra * (icms_prod / 100)
        credito_icms = c_icms_frete + c_icms_prod
        
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
        'pis_rate': pis_pct,
        'cofins_rate': cofins_pct
    }

def obter_frete_ml(preco, peso):
    """Busca o frete na tabela ML baseado em Preço e Peso."""
    if preco < 79.00: return 0.00
    
    faixa_key = ""
    if 79.00 <= preco < 100.00: faixa_key = "79-99"
    elif 100.00 <= preco < 120.00: faixa_key = "100-119"
    elif 120.00 <= preco < 150.00: faixa_key = "120-149"
    elif 150.00 <= preco < 200.00: faixa_key = "150-199"
    else: faixa_key = "200+"

    lista_precos = TABELA_FRETE_ML[faixa_key]
    frete_encontrado = 0.0
    found = False
    for peso_limite, valor in lista_precos:
        if peso <= peso_limite:
            frete_encontrado = valor; found = True; break
    if not found: frete_encontrado = lista_precos[-1][1]
    return frete_encontrado

def calcular_cenario(margem_alvo, preco_venda_manual, comissao_pct, modo_calculo, canal_atual, 
                     custo_final_produto, detalhes_entrada, icms_venda_pct, difal_pct, 
                     peso_input, is_fulfillment, armazenagem_pct):
    """Motor principal de cálculo de precificação."""
    
    # Taxas de Saída
    icms_rate = icms_venda_pct / 100
    difal_rate = difal_pct / 100
    # Herda taxas de entrada ou usa padrão
    pis_rate = detalhes_entrada.get('pis_rate', 1.65) / 100
    cofins_rate = detalhes_entrada.get('cofins_rate', 7.60) / 100
    
    # Carga Tributária Efetiva (Base Reduzida: Preço - ICMS)
    pis_efetivo = (1 - icms_rate) * pis_rate
    cofins_efetivo = (1 - icms_rate) * cofins_rate
    total_impostos_pct = icms_venda_pct + difal_pct + (pis_efetivo * 100) + (cofins_efetivo * 100)
    
    # Configuração Logística
    frete_aplicado = 0.0
    taxa_fixa_extra = 0.0
    custo_armaz_fixo = 0.0
    taxa_armaz_variavel = 0.0
    
    if is_fulfillment:
        custo_armaz_fixo = custo_final_produto * (armazenagem_pct / 100)
    else:
        taxa_armaz_variavel = armazenagem_pct

    # Lógica de Frete (Iterativa para ML)
    if "Shopee" in canal_atual:
        frete_aplicado = 0.00; taxa_fixa_extra = 4.00
    elif "Mercado Livre" in canal_atual:
        if modo_calculo == "preco":
            frete_aplicado = obter_frete_ml(preco_venda_manual, peso_input)
        else:
            frete_temp = 0.0
            for _ in range(3): # Loop de convergência
                divisor = 1 - ((total_impostos_pct + comissao_pct + taxa_armaz_variavel + margem_alvo) / 100)
                if divisor <= 0: divisor = 0.01
                numerador = custo_final_produto + frete_temp + taxa_fixa_extra + custo_armaz_fixo
                preco_simulado = numerador / divisor
                frete_temp = obter_frete_ml(preco_simulado, peso_input)
            frete_aplicado = frete_temp
    else:
        frete_aplicado = 0.00

    # Cálculo Final
    if modo_calculo == "margem":
        divisor = 1 - ((total_impostos_pct + comissao_pct + taxa_armaz_variavel + margem_alvo) / 100)
        if divisor <= 0: divisor = 0.01
        numerador = custo_final_produto + frete_aplicado + taxa_fixa_extra + custo_armaz_fixo
        preco_final = numerador / divisor
        margem_real = margem_alvo
    else: 
        preco_final = preco_venda_manual
        val_armaz_variavel = preco_final * (taxa_armaz_variavel / 100)
        custos_variaveis_val = preco_final * ((total_impostos_pct + comissao_pct) / 100)
        custos_fixos_totais = frete_aplicado + taxa_fixa_extra + custo_final_produto + custo_armaz_fixo + val_armaz_variavel
        lucro_bruto = preco_final - custos_variaveis_val - custos_fixos_totais
        margem_real = (lucro_bruto / preco_final) * 100 if preco_final > 0 else 0

    # Detalhamento Monetário
    val_icms = preco_final * icms_rate
    val_difal = preco_final * difal_rate
    base_pis_cofins = preco_final - val_icms
    val_pis = base_pis_cofins * pis_rate
    val_cofins = base_pis_cofins * cofins_rate
    val_impostos_total = val_icms + val_difal + val_pis + val_cofins
    
    val_comissao = preco_final * (comissao_pct / 100)
    val_armazenagem_final = custo_armaz_fixo if is_fulfillment else (preco_final * (taxa_armaz_variavel / 100))
    val_marketplace_total = val_comissao + frete_aplicado + taxa_fixa_extra + val_armazenagem_final
    val_lucro = preco_final - val_impostos_total - val_marketplace_total - custo_final_produto
    
    return {
        "preco": preco_final, "lucro": val_lucro, "margem": margem_real,
        "detalhes": {
            "impostos_venda_total": val_impostos_total, 
            "val_icms": val_icms, "val_difal": val_difal,
            "val_pis": val_pis, "val_cofins": val_cofins, 
            "pis_rate_used": pis_rate*100, "cofins_rate_used": cofins_rate*100,
            "mkt_total": val_marketplace_total, "mkt_comissao": val_comissao, "mkt_frete": frete_aplicado, 
            "mkt_taxa_extra": taxa_fixa_extra, "mkt_armazenagem": val_armazenagem_final,
            "custo_prod_total": custo_final_produto, "preco_medio": detalhes_entrada.get('preco_medio', 0),
            "credito_icms": detalhes_entrada.get('credito_icms_total', 0),
            "credito_pis": detalhes_entrada.get('credito_pis', 0), "credito_cofins": detalhes_entrada.get('credito_cofins', 0),
        }
    }

def render_card_html(d, comissao, nome_icms, icms_venda_pct, difal_pct, is_fulfillment):
    """Gera o HTML do Card (Sem indentação para evitar bugs)."""
    difal_row = f'<div class="sub-row"><span>DIFAL ({difal_pct}%)</span> <span>R$ {d["val_difal"]:.2f}</span></div>' if d['val_difal'] > 0 else ""
    pis_row = f'<div class="sub-row"><span>PIS ({d["pis_rate_used"]:.2f}%)</span> <span>R$ {d["val_pis"]:.2f}</span></div>' if d['val_pis'] > 0 else ""
    cofins_row = f'<div class="sub-row"><span>COFINS ({d["cofins_rate_used"]:.2f}%)</span> <span>R$ {d["val_cofins"]:.2f}</span></div>' if d['val_cofins'] > 0 else ""
    taxa_extra_row = f'<div class="sub-row"><span>Taxa Fixa</span> <span>R$ {d["mkt_taxa_extra"]:.2f}</span></div>' if d.get('mkt_taxa_extra', 0) > 0 else ""
    
    armazenagem_row = ""
    if d.get('mkt_armazenagem', 0) > 0:
        base_calc = "Custo" if is_fulfillment else "Venda"
        armazenagem_row = f'<div class="sub-row"><span>Armaz. (% s/ {base_calc})</span> <span>R$ {d["mkt_armazenagem"]:.2f}</span></div>'

    creditos_html = ""
    if d['credito_icms'] > 0: creditos_html += f'<div class="credit-row"><span>• Crédito ICMS</span> <span>- R$ {d["credito_icms"]:.2f}</span></div>'
    if d['credito_pis'] > 0: creditos_html += f'<div class="credit-row"><span>• Crédito PIS</span> <span>- R$ {d["credito_pis"]:.2f}</span></div>'
    if d['credito_cofins'] > 0: creditos_html += f'<div class="credit-row"><span>• Crédito COFINS</span> <span>- R$ {d["credito_cofins"]:.2f}</span></div>'
    
    return f"""<div class="custom-accordion"><details><summary><span>(-) Impostos Venda</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['impostos_venda_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>{nome_icms} ({icms_venda_pct}%)</span> <span>R$ {d['val_icms']:.2f}</span></div>{difal_row}{pis_row}{cofins_row}</div></details><details><summary><span>(-) Custos Marketplace</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['mkt_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>Comissão ({comissao}%)</span> <span>R$ {d['mkt_comissao']:.2f}</span></div><div class="sub-row"><span>Frete</span> <span>R$ {d['mkt_frete']:.2f}</span></div>{taxa_extra_row}{armazenagem_row}</div></details><details><summary><span>(-) Custo Produto Final</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['custo_prod_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>Preço Compra Médio</span> <span>R$ {d['preco_medio']:.2f}</span></div><div style="margin-top: 5px; border-top: 1px dashed var(--border-color); padding-top:4px;"><span style="font-size:0.9em; color: var(--text-muted);">Abatimentos Fiscais:</span>{creditos_html}</div></div></details></div>"""

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

# ==============================================================================
# 3. GESTÃO DE ESTADO
# ==============================================================================
if 'db_produtos' not in st.session_state: st.session_state['db_produtos'] = {}
if 'custo_produto_final' not in st.session_state: st.session_state['custo_produto_final'] = 99.00
if 'detalhes_custo' not in st.session_state:
    st.session_state['detalhes_custo'] = {
        'preco_medio': 99.00, 'credito_icms_total': 0.0, 'credito_pis': 0.0, 'credito_cofins': 0.0, 
        'pis_rate': 1.65, 'cofins_rate': 7.60, 'fornecedor_base': 99.00
    }

# ==============================================================================
# 4. SIDEBAR (CONFIGURAÇÕES GERAIS)
# ==============================================================================
with st.sidebar:
    c_head, c_tog = st.columns([2,1])
    c_head.header("⚙️ Config.")
    dark_mode = c_tog.toggle("🌘", value=False)
    
    canal = st.selectbox("🏪 Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🔵 Magalu", "🟠 KaBuM!", "🌐 Site Próprio"])
    st.markdown("---")
    
    # SELEÇÃO DE PRODUTO DO BANCO DE DADOS
    st.subheader("📦 Selecionar Produto")
    opcoes_produtos = ["Novo / Manual"] + list(st.session_state['db_produtos'].keys())
    produto_selecionado = st.selectbox("Buscar no Cadastro", opcoes_produtos)
    
    # Lógica de Carregamento
    if produto_selecionado != "Novo / Manual":
        dados_prod = st.session_state['db_produtos'][produto_selecionado]
        st.session_state['custo_produto_final'] = dados_prod['custo_final']
        st.session_state['detalhes_custo'] = dados_prod['detalhes']
        
    custo_display = st.session_state['custo_produto_final']
    st.markdown(f"""<div style="background:var(--hover-bg);padding:10px;border-radius:8px;border:1px solid var(--border-color);margin-bottom:10px;color:var(--text-color);"><small style="color:var(--text-muted)">Custo Atual</small><br><b style="font-size:1.4em;color:var(--primary-color)">R$ {custo_display:,.2f}</b></div>""", unsafe_allow_html=True)

    st.subheader("💸 Tributos Venda")
    col_t1, col_t2 = st.columns(2)
    icms_venda_pct = col_t1.number_input("ICMS (%)", 18.0, step=0.5, format="%.2f")
    difal_pct = col_t2.number_input("DIFAL (%)", 0.0, step=0.5, format="%.2f")
    
    st.subheader("🚚 Logística")
    is_fulfillment = st.toggle("⚡ Envio Full?", value=False)
    col_l1, col_l2 = st.columns(2)
    peso_input = col_l1.number_input("Peso (Kg)", 0.3, step=0.1, format="%.2f")
    armazenagem_pct = col_l2.number_input("Armaz. (%)", 0.0, step=0.1, format="%.2f", help="Sobre Custo (Full) ou Venda (Flex)")
    
    st.markdown("---")
    with st.expander("💾 Backup / Dados"):
        st.download_button("Baixar Cadastro (JSON)", data=converter_db_para_json(), file_name="db_produtos.json", mime="application/json")
        uploaded_db = st.file_uploader("Carregar Backup", type=["json"])
        if uploaded_db: carregar_banco_dados(uploaded_db)

# CSS DINÂMICO
css_variables = "--primary-color: #1e3a8a; --secondary-color: #2c3e50; --card-bg: #ffffff; --text-color: #333; --text-muted: #666; --border-color: #e0e0e0; --success-color: #27ae60; --hover-bg: #f8f9fa; --dotted-color: #ccc;"
if dark_mode: css_variables = "--primary-color: #60a5fa; --secondary-color: #e2e8f0; --card-bg: #1f2937; --text-color: #e2e8f0; --text-muted: #9ca3af; --border-color: #374151; --success-color: #34d399; --hover-bg: #374151; --dotted-color: #555;"

st.markdown(f"""
<style>
    :root {{ {css_variables} }}
    .main-header {{ font-size: 2.2em; font-weight: bold; margin-bottom: 10px; color: var(--secondary-color); }}
    .card-title {{ font-size: 1.6em; font-weight: bold; color: var(--text-color); margin-top: 5px; }}
    .price-label {{ font-size: 0.85em; color: var(--text-muted); margin-bottom: -5px; margin-top: 10px; }}
    .big-price {{ font-size: 2.5em; font-weight: 800; color: var(--primary-color); margin-bottom: 15px; }}
    div[data-testid="stNumberInput"] input {{ font-weight: bold; color: var(--primary-color); background-color: transparent; }}
    div[data-testid="stNumberInput"] label {{ color: var(--text-muted); }}
    div[data-testid="stNumberInput"] button {{ color: var(--text-color); }}
    .result-box {{ margin-top: 15px; padding-top: 10px; border-top: 1px solid var(--border-color); }}
    .lucro-label {{ font-size: 0.8em; font-weight: bold; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }}
    .lucro-valor {{ font-size: 1.8em; font-weight: bold; color: var(--success-color); display: flex; align-items: center; gap: 5px; }}
    
    .custom-accordion details > summary {{ list-style: none; }}
    .custom-accordion details > summary::-webkit-details-marker {{ display: none; }}
    .custom-accordion details {{ border: 1px solid var(--border-color); border-radius: 6px; margin-bottom: 8px; background-color: var(--card-bg); transition: border-color 0.2s; color: var(--text-color); }}
    .custom-accordion details:hover {{ border-color: var(--text-muted); }}
    .custom-accordion summary {{ display: flex; align-items: center; padding: 10px 12px; cursor: pointer; font-weight: 500; color: var(--text-color); font-size: 0.95em; }}
    .custom-accordion summary::before {{ content: '›'; font-size: 1.5em; line-height: 0.5em; margin-right: 8px; color: var(--text-muted); transition: transform 0.2s ease; margin-top: -2px; }}
    .custom-accordion details[open] summary::before {{ transform: rotate(90deg); color: var(--text-color); }}
    .dotted-fill {{ flex-grow: 1; border-bottom: 2px dotted var(--dotted-color); margin: 0 8px; height: 0.8em; opacity: 0.4; }}
    .summary-value {{ font-weight: 700; color: var(--text-color); }}
    .details-content {{ padding: 8px 12px 12px 35px; background-color: var(--hover-bg); font-size: 0.85em; color: var(--text-color); border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; border-top: 1px solid var(--border-color); }}
    .sub-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; }}
    .credit-row {{ display: flex; justify-content: space-between; margin-bottom: 2px; color: var(--success-color); font-size: 0.9em; padding-left: 10px; }}
    
    [data-testid="stVerticalBlock"] > [style*="border"] {{ border-color: var(--border-color) !important; background-color: var(--card-bg); }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. ÁREA PRINCIPAL (ABAS)
# ==============================================================================
tab_calc, tab_cadastro = st.tabs(["🧮 Calculadora", "📝 Cadastro de Custos"])

# --- ABA 1: CALCULADORA ---
with tab_calc:
    nome_canal_titulo = canal.split(' ', 1)[1] if ' ' in canal else canal
    st.markdown(f'<div class="main-header">🏷️ Calculadora - {nome_canal_titulo}</div>', unsafe_allow_html=True)
    tipo_calculo = st.radio("🎯 O que você deseja definir?", ["Definir Margem (%)", "Definir Preço de Venda (R$)"], horizontal=True)
    modo = "margem" if "Margem" in tipo_calculo else "preco"
    st.write("") 

    if "Mercado Livre" in canal:
        col_classico, col_premium = st.columns(2, gap="medium")
        with col_classico:
            with st.container(border=True):
                h1, h2 = st.columns([1, 1.5])
                h1.markdown('<div class="card-title">Clássico</div>', unsafe_allow_html=True)
                with h2:
                    cc1, cc2 = st.columns(2)
                    comissao_c = cc1.number_input("🏷️ Comis. (%)", value=11.5, step=0.5, format="%.1f", key="c_com")
                    margem_c_input = cc2.number_input("📈 Margem (%)", value=15.0, step=0.5, format="%.1f", key="c_mar", disabled=(modo=="preco"))
                st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)
                preco_c_manual = 0.0
                if modo == "preco":
                    preco_c_manual = st.number_input("", value=75.00, step=0.5, format="%.2f", key="c_price_man", label_visibility="collapsed")
                    res_c = calcular_cenario(0, preco_c_manual, comissao_c, "preco", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                else:
                    res_c = calcular_cenario(margem_c_input, 0, comissao_c, "margem", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                st.markdown(f'<div class="big-price">R$ {res_c["preco"]:.2f}</div>', unsafe_allow_html=True)
                st.markdown(render_card_html(res_c["detalhes"], comissao_c, "ICMS", icms_venda_pct, difal_pct, is_fulfillment), unsafe_allow_html=True)
                st.markdown(f"""<div class="result-box"><div class="lucro-label">Lucro Líquido (Margem Real: {res_c['margem']:.1f}%)</div><div class="lucro-valor">⬆ R$ {res_c['lucro']:.2f}</div></div>""", unsafe_allow_html=True)

        with col_premium:
            with st.container(border=True):
                h1p, h2p = st.columns([1, 1.5])
                h1p.markdown('<div class="card-title">Premium</div>', unsafe_allow_html=True)
                with h2p:
                    cp1, cp2 = st.columns(2)
                    comissao_p = cp1.number_input("🏷️ Comis. (%)", value=16.5, step=0.5, format="%.1f", key="p_com")
                    margem_p_input = cp2.number_input("📈 Margem (%)", value=15.0, step=0.5, format="%.1f", key="p_mar", disabled=(modo=="preco"))
                st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)
                preco_p_manual = 0.0
                if modo == "preco":
                    preco_p_manual = st.number_input("", value=85.00, step=0.5, format="%.2f", key="p_price_man", label_visibility="collapsed")
                    res_p = calcular_cenario(0, preco_p_manual, comissao_p, "preco", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                else:
                    res_p = calcular_cenario(margem_p_input, 0, comissao_p, "margem", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                st.markdown(f'<div class="big-price">R$ {res_p["preco"]:.2f}</div>', unsafe_allow_html=True)
                st.markdown(render_card_html(res_p["detalhes"], comissao_p, "ICMS", icms_venda_pct, difal_pct, is_fulfillment), unsafe_allow_html=True)
                st.markdown(f"""<div class="result-box"><div class="lucro-label">Lucro Líquido (Margem Real: {res_p['margem']:.1f}%)</div><div class="lucro-valor">⬆ R$ {res_p['lucro']:.2f}</div></div>""", unsafe_allow_html=True)
    else:
        c_left, c_center, c_right = st.columns([1, 2, 1])
        with c_center:
            with st.container(border=True):
                h1u, h2u = st.columns([1, 1.5])
                h1u.markdown(f'<div class="card-title">{nome_canal_titulo}</div>', unsafe_allow_html=True)
                with h2u:
                    cu1, cu2 = st.columns(2)
                    comissao_u = cu1.number_input("🏷️ Comis. (%)", value=18.0, step=0.5, format="%.1f", key="u_com")
                    margem_u_input = cu2.number_input("📈 Margem (%)", value=15.0, step=0.5, format="%.1f", key="u_mar", disabled=(modo=="preco"))
                st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)
                preco_u_manual = 0.0
                if modo == "preco":
                    preco_u_manual = st.number_input("", value=100.00, step=0.5, format="%.2f", key="u_price_man", label_visibility="collapsed")
                    res_u = calcular_cenario(0, preco_u_manual, comissao_u, "preco", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                else:
                    res_u = calcular_cenario(margem_u_input, 0, comissao_u, "margem", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                st.markdown(f'<div class="big-price">R$ {res_u["preco"]:.2f}</div>', unsafe_allow_html=True)
                st.markdown(render_card_html(res_u["detalhes"], comissao_u, "ICMS", icms_venda_pct, difal_pct, is_fulfillment), unsafe_allow_html=True)
                st.markdown(f"""<div class="result-box"><div class="lucro-label">Lucro Líquido (Margem Real: {res_u['margem']:.1f}%)</div><div class="lucro-valor">⬆ R$ {res_u['lucro']:.2f}</div></div>""", unsafe_allow_html=True)

# --- ABA 2: CADASTRO ---
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
            travado = (p_st > 0)
            icms_pr_pct = cc2.number_input("ICMS Produto (%)", 0.0 if travado else 12.0, step=0.5, disabled=travado, key="icmsp_cad")
            
            is_imp = st.toggle("Importação?", False, key="imp_cad")
            pis_c = 2.10 if is_imp else 1.65
            cofins_c = 9.65 if is_imp else 7.60
            st.caption(f"PIS: {pis_c}% | COFINS: {cofins_c}%")

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
                    novo_item = {'custo_final': res['custo_final'], 'detalhes': res}
                    st.session_state['db_produtos'][nome_prod] = novo_item
                    st.toast(f"Produto '{nome_prod}' salvo!", icon="💾")
                    st.rerun()
                else:
                    st.error("Digite um nome para o produto.")
            
            if produto_selecionado in st.session_state['db_produtos']:
                if st.button("🗑️ Excluir deste cadastro", type="secondary"):
                    del st.session_state['db_produtos'][produto_selecionado]
                    st.rerun()
