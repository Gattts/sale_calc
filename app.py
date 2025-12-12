import streamlit as st

# Configuração da página
st.set_page_config(page_title="Calculadora E-commerce", layout="wide", page_icon="🏷️")

# --- BANCO DE DADOS DE FRETES (Mercado Livre) ---
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

# --- INICIALIZAÇÃO DE ESTADO ---
if 'custo_produto_final' not in st.session_state:
    st.session_state['custo_produto_final'] = 99.00
if 'detalhes_custo' not in st.session_state:
    st.session_state['detalhes_custo'] = {
        'preco_medio': 99.00, 'credito_icms_total': 0.0, 
        'credito_pis': 0.0, 'credito_cofins': 0.0, 
        'pis_rate': 1.65, 'cofins_rate': 7.60, 
        'fornecedor_base': 99.00
    }

# --- SIDEBAR - CONFIGURAÇÕES GERAIS ---
with st.sidebar:
    col_sb_title, col_sb_toggle = st.columns([2, 1])
    col_sb_title.header("⚙️ Config.")
    dark_mode = col_sb_toggle.toggle("🌘 Dark", value=False)
    
    canal = st.selectbox("🏪 Canal de Venda", 
                         ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🔵 Magalu", "🟠 KaBuM!", "🌐 Site Próprio"], 
                         index=0)
    st.markdown("---")

# --- CSS PERSONALIZADO ---
css_variables = """
    --primary-color: #1e3a8a; --secondary-color: #2c3e50; --card-bg: #ffffff;
    --text-color: #333333; --text-muted: #666666; --border-color: #e0e0e0;
    --success-color: #27ae60; --hover-bg: #f8f9fa; --dotted-color: #ccc;
"""
if dark_mode:
    css_variables = """
    --primary-color: #60a5fa; --secondary-color: #e2e8f0; --card-bg: #1f2937;
    --text-color: #e2e8f0; --text-muted: #9ca3af; --border-color: #374151;
    --success-color: #34d399; --hover-bg: #374151; --dotted-color: #555;
    """

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
    .custom-accordion details {{
        border: 1px solid var(--border-color); border-radius: 6px; margin-bottom: 8px;
        background-color: var(--card-bg); transition: border-color 0.2s; color: var(--text-color);
    }}
    .custom-accordion details:hover {{ border-color: var(--text-muted); }}
    .custom-accordion summary {{
        display: flex; align-items: center; padding: 10px 12px;
        cursor: pointer; font-weight: 500; color: var(--text-color); font-size: 0.95em;
    }}
    .custom-accordion summary::before {{
        content: '›'; font-size: 1.5em; line-height: 0.5em; margin-right: 8px;
        color: var(--text-muted); transition: transform 0.2s ease; margin-top: -2px; 
    }}
    .custom-accordion details[open] summary::before {{ transform: rotate(90deg); color: var(--text-color); }}
    .dotted-fill {{ flex-grow: 1; border-bottom: 2px dotted var(--dotted-color); margin: 0 8px; height: 0.8em; opacity: 0.4; }}
    .summary-value {{ font-weight: 700; color: var(--text-color); }}
    .details-content {{
        padding: 8px 12px 12px 35px; background-color: var(--hover-bg);
        font-size: 0.85em; color: var(--text-color);
        border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; border-top: 1px solid var(--border-color);
    }}
    .sub-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; }}
    .credit-row {{ display: flex; justify-content: space-between; margin-bottom: 2px; color: var(--success-color); font-size: 0.9em; padding-left: 10px; }}
    
    .sidebar-custo-box {{
        background-color: var(--hover-bg); padding: 10px 15px; border-radius: 8px;
        border: 1px solid var(--border-color); margin-bottom: 10px;
    }}
    .sidebar-custo-label {{ font-size: 0.85em; color: var(--text-muted); margin: 0; }}
    .sidebar-custo-value {{ font-size: 1.4em; font-weight: 700; color: var(--primary-color); margin: 0; line-height: 1.2; }}
    
    [data-testid="stVerticalBlock"] > [style*="border"] {{
        border-color: var(--border-color) !important;
        background-color: var(--card-bg);
    }}
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DO POP-UP (DIALOG) ---
@st.dialog("Detalhes Tributários (Entrada)")
def configurar_tributos():
    st.caption("Configure os custos e créditos para chegar no Custo Final do Produto.")
    lucro_real = st.toggle("Empresa é Lucro Real?", value=True)
    st.divider()
    
    c1, c2 = st.columns(2)
    preco_compra = c1.number_input("Preço de Compra ($)", value=100.00, step=1.0)
    frete_rateio = c2.number_input("Frete (Rateio) ($)", value=0.00, step=0.5)
    
    c3, c4 = st.columns(2)
    ipi_pct = c3.number_input("IPI (%)", value=0.00, step=0.5)
    valor_ipi = preco_compra * (ipi_pct / 100)
    c4.info(f"Valor IPI: R$ {valor_ipi:.2f}")
    
    c5, c6 = st.columns(2)
    outros_valores = c5.number_input("Acrésc./Desc. NF ($)", value=0.00, step=1.0)
    icms_st = c6.number_input("ICMS ST ($)", value=0.00, step=1.0)

    preco_compra_medio = preco_compra + frete_rateio + valor_ipi + outros_valores + icms_st
    st.markdown(f"**Preço de Compra Médio: R$ {preco_compra_medio:.2f}**")
    st.divider()
    
    custo_final = preco_compra_medio
    detalhes_to_save = {}

    if lucro_real:
        st.caption("Créditos Tributários")
        col_i1, col_i2 = st.columns(2)
        icms_frete_pct = col_i1.number_input("ICMS Frete (%)", value=12.0, step=0.5)
        disabled_icms_prod = (icms_st > 0)
        val_default_icms = 0.0 if disabled_icms_prod else 12.0
        icms_prod_pct = col_i2.number_input("ICMS Produto (%)", value=val_default_icms, step=0.5, disabled=disabled_icms_prod)
        
        is_importacao = st.toggle("É Importação Própria?", value=False)
        if is_importacao:
            pis_pct, cofins_pct = 2.10, 9.65
        else:
            pis_pct, cofins_pct = 1.65, 7.60
            
        credito_icms_frete = frete_rateio * (icms_frete_pct / 100)
        credito_icms_prod = preco_compra * (icms_prod_pct / 100)
        total_credito_icms = credito_icms_frete + credito_icms_prod
        
        base_pis_cofins = preco_compra 
        credito_pis = base_pis_cofins * (pis_pct / 100)
        credito_cofins = base_pis_cofins * (cofins_pct / 100)
        total_pis_cofins = credito_pis + credito_cofins

        custo_final = preco_compra_medio - total_credito_icms - total_pis_cofins
        
        detalhes_to_save = {
            'preco_medio': preco_compra_medio, 'credito_icms_total': total_credito_icms,
            'credito_pis': credito_pis, 'credito_cofins': credito_cofins, 
            'pis_rate': pis_pct, 'cofins_rate': cofins_pct,
            'fornecedor_base': preco_compra
        }
        st.success(f"Custo Final Calculado: R$ {custo_final:.2f}")
    else:
        st.warning("Simples/Presumido: Custo Final = Preço Médio")
        detalhes_to_save = {
            'preco_medio': preco_compra_medio, 'credito_icms_total': 0.0,
            'credito_pis': 0.0, 'credito_cofins': 0.0, 
            'pis_rate': 0.0, 'cofins_rate': 0.0,
            'fornecedor_base': preco_compra
        }

    if st.button("Salvar e Usar este Custo", type="primary"):
        st.session_state['custo_produto_final'] = custo_final
        st.session_state['detalhes_custo'] = detalhes_to_save
        st.rerun()

# --- SIDEBAR - CONTINUAÇÃO ---
with st.sidebar:
    st.subheader("📦 Produto & Custo")
    custo_display = st.session_state['custo_produto_final']
    st.markdown(f"""<div class="sidebar-custo-box"><p class="sidebar-custo-label">Custo Final Calculado</p><p class="sidebar-custo-value">R$ {custo_display:,.2f}</p></div>""", unsafe_allow_html=True)
    
    if st.button("📝 Editar Fiscal", use_container_width=True):
        configurar_tributos()
        
    st.markdown("---")
    st.subheader("💸 Tributos Venda")
    c_v1, c_v2 = st.columns(2)
    icms_venda_pct = c_v1.number_input("🏛️ ICMS (%)", value=18.00, step=0.5, format="%.2f")
    difal_pct = c_v2.number_input("🌍 DIFAL (%)", value=0.00, step=0.5, format="%.2f") 

    st.markdown("---")
    st.subheader("🚚 Logística")
    is_fulfillment = st.toggle("⚡ Envio Full?", value=False)
    help_text_armaz = "Calculado sobre CUSTO DO PRODUTO (Full Ativo) ou PREÇO VENDA (Full Inativo)"
    
    col_log1, col_log2 = st.columns(2)
    peso_input = col_log1.number_input("⚖️ Peso (Kg)", value=0.30, step=0.10, format="%.2f")
    armazenagem_pct = col_log2.number_input("📦 Armaz. (%)", value=0.0, step=0.1, format="%.2f", help=help_text_armaz)

# --- FUNÇÃO HELPER: CONSULTAR TABELA ML ---
def obter_frete_ml(preco, peso):
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
        if peso_input <= peso_limite:
            frete_encontrado = valor; found = True; break
    if not found: frete_encontrado = lista_precos[-1][1]
    return frete_encontrado


# --- FUNÇÃO DE CÁLCULO GERAL ---
def calcular_cenario(margem_alvo, preco_venda_manual, comissao_pct, modo_calculo, canal_atual):
    custo_final_produto = st.session_state['custo_produto_final']
    detalhes_entrada = st.session_state['detalhes_custo']
    
    icms_rate = icms_venda_pct / 100
    difal_rate = difal_pct / 100
    pis_rate = details_pis_rate = detalhes_entrada.get('pis_rate', 1.65) / 100
    cofins_rate = details_cofins_rate = detalhes_entrada.get('cofins_rate', 7.60) / 100
    
    # 2. Calcular Carga Tributária Efetiva
    pis_efetivo = (1 - icms_rate) * pis_rate
    cofins_efetivo = (1 - icms_rate) * cofins_rate
    total_impostos_pct = icms_venda_pct + difal_pct + (pis_efetivo * 100) + (cofins_efetivo * 100)
    
    frete_aplicado = 0.0
    taxa_fixa_extra = 0.0
    custo_armaz_fixo = 0.0
    taxa_armaz_variavel = 0.0
    
    if is_fulfillment:
        custo_armaz_fixo = custo_final_produto * (armazenagem_pct / 100)
    else:
        taxa_armaz_variavel = armazenagem_pct

    # 3. Definição de Frete e Loop
    if "Shopee" in canal_atual:
        frete_aplicado = 0.00; taxa_fixa_extra = 4.00
    elif "Mercado Livre" in canal_atual:
        if modo_calculo == "preco":
            frete_aplicado = obter_frete_ml(preco_venda_manual, peso_input)
        else:
            frete_temp = 0.0
            for _ in range(3):
                divisor = 1 - ((total_impostos_pct + comissao_pct + taxa_armaz_variavel + margem_alvo) / 100)
                if divisor <= 0: divisor = 0.01
                numerador = custo_final_produto + frete_temp + taxa_fixa_extra + custo_armaz_fixo
                preco_simulado = numerador / divisor
                frete_temp = obter_frete_ml(preco_simulado, peso_input)
            frete_aplicado = frete_temp

    # 4. Cálculo Final
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

    # 5. Detalhamento Absoluto
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
            "pis_rate_used": details_pis_rate*100, "cofins_rate_used": details_cofins_rate*100,
            "mkt_total": val_marketplace_total, "mkt_comissao": val_comissao, "mkt_frete": frete_aplicado, 
            "mkt_taxa_extra": taxa_fixa_extra, "mkt_armazenagem": val_armazenagem_final,
            "custo_prod_total": custo_final_produto, "preco_medio": detalhes_entrada.get('preco_medio', 0),
            "credito_icms": detalhes_entrada.get('credito_icms_total', 0),
            "credito_pis": detalhes_entrada.get('credito_pis', 0), "credito_cofins": detalhes_entrada.get('credito_cofins', 0),
        }
    }

# --- HELPER HTML (FIXED) ---
def render_card_html(d, comissao, nome_icms):
    difal_row = f'<div class="sub-row"><span>DIFAL ({difal_pct}%)</span> <span>R$ {d["val_difal"]:.2f}</span></div>' if d['val_difal'] > 0 else ""
    
    pis_row = ""
    if d['val_pis'] > 0:
        pis_row = f'<div class="sub-row"><span>PIS ({d["pis_rate_used"]:.2f}%)</span> <span>R$ {d["val_pis"]:.2f}</span></div>'
    
    cofins_row = ""
    if d['val_cofins'] > 0:
        cofins_row = f'<div class="sub-row"><span>COFINS ({d["cofins_rate_used"]:.2f}%)</span> <span>R$ {d["val_cofins"]:.2f}</span></div>'

    taxa_extra_row = f'<div class="sub-row"><span>Taxa Fixa</span> <span>R$ {d["mkt_taxa_extra"]:.2f}</span></div>' if d.get('mkt_taxa_extra', 0) > 0 else ""
    
    armazenagem_row = ""
    if d.get('mkt_armazenagem', 0) > 0:
        base_calc = "Custo" if is_fulfillment else "Venda"
        armazenagem_row = f'<div class="sub-row"><span>Armaz. (% s/ {base_calc})</span> <span>R$ {d["mkt_armazenagem"]:.2f}</span></div>'

    creditos_html = ""
    if d['credito_icms'] > 0: creditos_html += f'<div class="credit-row"><span>• Crédito ICMS</span> <span>- R$ {d["credito_icms"]:.2f}</span></div>'
    if d['credito_pis'] > 0: creditos_html += f'<div class="credit-row"><span>• Crédito PIS</span> <span>- R$ {d["credito_pis"]:.2f}</span></div>'
    if d['credito_cofins'] > 0: creditos_html += f'<div class="credit-row"><span>• Crédito COFINS</span> <span>- R$ {d["credito_cofins"]:.2f}</span></div>'
    
    # IMPORTANTE: String HTML sem indentação para evitar bug do Markdown
    return f"""<div class="custom-accordion"><details><summary><span>(-) Impostos Venda</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['impostos_venda_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>{nome_icms} ({icms_venda_pct}%)</span> <span>R$ {d['val_icms']:.2f}</span></div>{difal_row}{pis_row}{cofins_row}</div></details><details><summary><span>(-) Custos Marketplace</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['mkt_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>Comissão ({comissao}%)</span> <span>R$ {d['mkt_comissao']:.2f}</span></div><div class="sub-row"><span>Frete</span> <span>R$ {d['mkt_frete']:.2f}</span></div>{taxa_extra_row}{armazenagem_row}</div></details><details><summary><span>(-) Custo Produto Final</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['custo_prod_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>Preço Compra Médio</span> <span>R$ {d['preco_medio']:.2f}</span></div><div style="margin-top: 5px; border-top: 1px dashed var(--border-color); padding-top:4px;"><span style="font-size:0.9em; color: var(--text-muted);">Abatimentos Fiscais:</span>{creditos_html}</div></div></details></div>"""

# --- LAYOUT PRINCIPAL ---
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
                res_c = calcular_cenario(0, preco_c_manual, comissao_c, "preco", canal)
            else:
                res_c = calcular_cenario(margem_c_input, 0, comissao_c, "margem", canal)
                st.markdown(f'<div class="big-price">R$ {res_c["preco"]:.2f}</div>', unsafe_allow_html=True)
            st.markdown(render_card_html(res_c["detalhes"], comissao_c, "ICMS"), unsafe_allow_html=True)
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
                res_p = calcular_cenario(0, preco_p_manual, comissao_p, "preco", canal)
            else:
                res_p = calcular_cenario(margem_p_input, 0, comissao_p, "margem", canal)
                st.markdown(f'<div class="big-price">R$ {res_p["preco"]:.2f}</div>', unsafe_allow_html=True)
            st.markdown(render_card_html(res_p["detalhes"], comissao_p, "ICMS"), unsafe_allow_html=True)
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
                res_u = calcular_cenario(0, preco_u_manual, comissao_u, "preco", canal)
            else:
                res_u = calcular_cenario(margem_u_input, 0, comissao_u, "margem", canal)
                st.markdown(f'<div class="big-price">R$ {res_u["preco"]:.2f}</div>', unsafe_allow_html=True)
            st.markdown(render_card_html(res_u["detalhes"], comissao_u, "ICMS"), unsafe_allow_html=True)
            st.markdown(f"""<div class="result-box"><div class="lucro-label">Lucro Líquido (Margem Real: {res_u['margem']:.1f}%)</div><div class="lucro-valor">⬆ R$ {res_u['lucro']:.2f}</div></div>""", unsafe_allow_html=True)
