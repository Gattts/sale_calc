import streamlit as st

# Configuração da página
st.set_page_config(page_title="Calculadora E-commerce", layout="wide", page_icon="🏷️")

# --- INICIALIZAÇÃO DE ESTADO ---
if 'custo_produto_final' not in st.session_state:
    st.session_state['custo_produto_final'] = 99.00
if 'detalhes_custo' not in st.session_state:
    st.session_state['detalhes_custo'] = {
        'preco_medio': 99.00, 
        'credito_icms_total': 0.0,
        'credito_pis': 0.0,
        'credito_cofins': 0.0,
        'fornecedor_base': 99.00
    }

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* Estilos Gerais */
    .main-header { font-size: 2.2em; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
    .card-title { font-size: 1.6em; font-weight: bold; color: #333; margin-top: 5px;}
    .price-label { font-size: 0.85em; color: #666; margin-bottom: -5px; margin-top: 10px; }
    
    /* Input e Textos */
    .big-price { font-size: 2.5em; font-weight: 800; color: #1e3a8a; margin-bottom: 15px; }
    div[data-testid="stNumberInput"] input { font-weight: bold; color: #1e3a8a; }

    /* Resultado */
    .result-box { margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee; }
    .lucro-label { font-size: 0.8em; font-weight: bold; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .lucro-valor { font-size: 1.8em; font-weight: bold; color: #27ae60; display: flex; align-items: center; gap: 5px; }

    /* Acordeão Customizado */
    .custom-accordion details > summary { list-style: none; }
    .custom-accordion details > summary::-webkit-details-marker { display: none; }
    
    .custom-accordion details {
        border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 8px;
        background-color: white; transition: border-color 0.2s;
    }
    .custom-accordion details:hover { border-color: #bbb; }
    
    .custom-accordion summary {
        display: flex; align-items: center; padding: 10px 12px;
        cursor: pointer; font-weight: 500; color: #444; font-size: 0.95em;
    }
    .custom-accordion summary::before {
        content: '›'; font-size: 1.5em; line-height: 0.5em; margin-right: 8px;
        color: #999; transition: transform 0.2s ease; margin-top: -2px; 
    }
    .custom-accordion details[open] summary::before { transform: rotate(90deg); color: #333; }
    
    .dotted-fill { flex-grow: 1; border-bottom: 2px dotted #ccc; margin: 0 8px; height: 0.8em; opacity: 0.4; }
    .summary-value { font-weight: 700; color: #333; }
    
    .details-content {
        padding: 8px 12px 12px 35px; background-color: #f8f9fa;
        font-size: 0.85em; color: #666;
        border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; border-top: 1px solid #eee;
    }
    .sub-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
    
    /* Estilo para sub-itens de crédito (verde e indentado) */
    .credit-row { 
        display: flex; justify-content: space-between; margin-bottom: 2px; 
        color: #27ae60; font-size: 0.9em; padding-left: 10px;
    }
    
    /* Box Customizado da Sidebar (Custo) */
    .sidebar-custo-box {
        background-color: #f0f2f6;
        padding: 10px 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    .sidebar-custo-label { font-size: 0.85em; color: #555; margin: 0; }
    .sidebar-custo-value { font-size: 1.4em; font-weight: 700; color: #1e3a8a; margin: 0; line-height: 1.2;}
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
    ipi_pct = c3.number_input("IPI (%)", value=0.00, step=1.0)
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
        icms_frete_pct = col_i1.number_input("ICMS Frete (%)", value=12.0)
        
        disabled_icms_prod = (icms_st > 0)
        val_default_icms = 0.0 if disabled_icms_prod else 12.0
        icms_prod_pct = col_i2.number_input("ICMS Produto (%)", value=val_default_icms, disabled=disabled_icms_prod)
        
        is_importacao = st.toggle("É Importação Própria?", value=False)
        if is_importacao:
            pis_pct, cofins_pct = 2.10, 9.65
        else:
            pis_pct, cofins_pct = 1.65, 7.60
            
        st.caption(f"Aliquotas PIS/COFINS: {pis_pct}% / {cofins_pct}%")

        credito_icms_frete = frete_rateio * (icms_frete_pct / 100)
        credito_icms_prod = preco_compra * (icms_prod_pct / 100)
        total_credito_icms = credito_icms_frete + credito_icms_prod
        
        base_pis_cofins = preco_compra 
        credito_pis = base_pis_cofins * (pis_pct / 100)
        credito_cofins = base_pis_cofins * (cofins_pct / 100)
        total_pis_cofins = credito_pis + credito_cofins

        custo_final = preco_compra_medio - total_credito_icms - total_pis_cofins
        
        detalhes_to_save = {
            'preco_medio': preco_compra_medio,
            'credito_icms_total': total_credito_icms,
            'credito_pis': credito_pis,
            'credito_cofins': credito_cofins,
            'fornecedor_base': preco_compra
        }
        st.success(f"Custo Final Calculado: R$ {custo_final:.2f}")
    else:
        st.warning("Simples/Presumido: Custo Final = Preço Médio")
        detalhes_to_save = {
            'preco_medio': preco_compra_medio,
            'credito_icms_total': 0.0,
            'credito_pis': 0.0,
            'credito_cofins': 0.0,
            'fornecedor_base': preco_compra
        }

    if st.button("Salvar e Usar este Custo", type="primary"):
        st.session_state['custo_produto_final'] = custo_final
        st.session_state['detalhes_custo'] = detalhes_to_save
        st.rerun()

# --- SIDEBAR PRINCIPAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # LISTA ATUALIZADA DE MARKETPLACES
    canal = st.selectbox("🏪 Canal de Venda", 
                         ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🔵 Magalu", "🟠 KaBuM!", "🌐 Site Próprio"], 
                         index=0)
    
    st.markdown("---")
    st.subheader("📦 Produto & Custo")
    
    custo_display = st.session_state['custo_produto_final']
    st.markdown(f"""
    <div class="sidebar-custo-box">
        <p class="sidebar-custo-label">Custo Final Calculado</p>
        <p class="sidebar-custo-value">R$ {custo_display:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📝 Editar Fiscal", use_container_width=True):
        configurar_tributos()
        
    st.markdown("---")
    st.subheader("💸 Tributos Venda")
    c_v1, c_v2 = st.columns(2)
    icms_venda_pct = c_v1.number_input("🏛️ ICMS (%)", value=18.00, format="%.2f")
    difal_pct = c_v2.number_input("🌍 DIFAL (%)", value=0.00, format="%.2f") 

    st.markdown("---")
    st.subheader("🚚 Logística")
    peso = st.number_input("⚖️ Peso (Kg)", value=0.30, step=0.10, format="%.2f")
    frete_custo_fixo = 19.95 

# --- FUNÇÃO DE CÁLCULO GERAL ---
def calcular_cenario(margem_alvo, preco_venda_manual, comissao_pct, modo_calculo):
    
    custo_final_produto = st.session_state['custo_produto_final']
    detalhes_entrada = st.session_state['detalhes_custo']
    
    total_impostos_venda_pct = icms_venda_pct + difal_pct
    
    if modo_calculo == "margem":
        divisor = 1 - ((total_impostos_venda_pct + comissao_pct + margem_alvo) / 100)
        if divisor <= 0: divisor = 0.01 
        preco_final = (custo_final_produto + frete_custo_fixo) / divisor
        margem_real = margem_alvo
    else: 
        preco_final = preco_venda_manual
        custos_variaveis = preco_final * ((total_impostos_venda_pct + comissao_pct) / 100)
        lucro_bruto = preco_final - custos_variaveis - frete_custo_fixo - custo_final_produto
        margem_real = (lucro_bruto / preco_final) * 100 if preco_final > 0 else 0

    val_icms = preco_final * (icms_venda_pct / 100)
    val_difal = preco_final * (difal_pct / 100) 
    val_impostos_total = val_icms + val_difal
    
    val_comissao = preco_final * (comissao_pct / 100)
    val_marketplace_total = val_comissao + frete_custo_fixo
    val_lucro = preco_final - val_impostos_total - val_marketplace_total - custo_final_produto
    
    return {
        "preco": preco_final,
        "lucro": val_lucro,
        "margem": margem_real,
        "detalhes": {
            "impostos_venda_total": val_impostos_total,
            "val_icms": val_icms,
            "val_difal": val_difal,
            "mkt_total": val_marketplace_total,
            "mkt_comissao": val_comissao,
            "mkt_frete": frete_custo_fixo,
            "custo_prod_total": custo_final_produto,
            "fornecedor_base": detalhes_entrada.get('fornecedor_base', 0),
            "credito_icms": detalhes_entrada.get('credito_icms_total', 0),
            "credito_pis": detalhes_entrada.get('credito_pis', 0),
            "credito_cofins": detalhes_entrada.get('credito_cofins', 0),
            "preco_medio": detalhes_entrada.get('preco_medio', 0)
        }
    }

# --- HELPER HTML SEM INDENTAÇÃO ---
def render_card_html(d, comissao, nome_icms):
    difal_row = ""
    if d['val_difal'] > 0:
        difal_row = f'<div class="sub-row"><span>DIFAL ({difal_pct}%)</span> <span>R$ {d["val_difal"]:.2f}</span></div>'

    creditos_html = ""
    if d['credito_icms'] > 0:
        creditos_html += f'<div class="credit-row"><span>• Crédito ICMS</span> <span>- R$ {d["credito_icms"]:.2f}</span></div>'
    if d['credito_pis'] > 0:
        creditos_html += f'<div class="credit-row"><span>• Crédito PIS</span> <span>- R$ {d["credito_pis"]:.2f}</span></div>'
    if d['credito_cofins'] > 0:
        creditos_html += f'<div class="credit-row"><span>• Crédito COFINS</span> <span>- R$ {d["credito_cofins"]:.2f}</span></div>'
        
    html_content = f"""
<div class="custom-accordion">
<details>
<summary><span>(-) Impostos Venda</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['impostos_venda_total']:.2f}</span></summary>
<div class="details-content">
<div class="sub-row"><span>{nome_icms} ({icms_venda_pct}%)</span> <span>R$ {d['val_icms']:.2f}</span></div>
{difal_row}
</div>
</details>
<details>
<summary><span>(-) Taxas Marketplace</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['mkt_total']:.2f}</span></summary>
<div class="details-content">
<div class="sub-row"><span>Comissão ({comissao}%)</span> <span>R$ {d['mkt_comissao']:.2f}</span></div>
<div class="sub-row"><span>Frete Fixo</span> <span>R$ {d['mkt_frete']:.2f}</span></div>
</div>
</details>
<details>
<summary><span>(-) Custo Produto Final</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['custo_prod_total']:.2f}</span></summary>
<div class="details-content">
<div class="sub-row"><span>Preço Compra Médio</span> <span>R$ {d['preco_medio']:.2f}</span></div>
<div style="margin-top: 5px; border-top: 1px dashed #ddd; padding-top:4px;">
<span style="font-size:0.9em; color: #888;">Abatimentos Fiscais:</span>
{creditos_html}
</div>
</div>
</details>
</div>
"""
    return html_content

# --- LAYOUT PRINCIPAL E LÓGICA DE CARDS ---
st.markdown(f'<div class="main-header">🏷️ Calculadora - {canal}</div>', unsafe_allow_html=True)

tipo_calculo = st.radio("🎯 O que você deseja definir?", ["Definir Margem (%)", "Definir Preço de Venda (R$)"], horizontal=True)
modo = "margem" if "Margem" in tipo_calculo else "preco"
st.write("") 

# --- LÓGICA CONDICIONAL DE LAYOUT ---

if "Mercado Livre" in canal:
    # --- LAYOUT MERCADO LIVRE (2 COLUNAS) ---
    col_classico, col_premium = st.columns(2, gap="medium")

    # CARD CLÁSSICO
    with col_classico:
        with st.container(border=True):
            h1, h2 = st.columns([1, 1.5])
            h1.markdown('<div class="card-title">Clássico</div>', unsafe_allow_html=True)
            with h2:
                cc1, cc2 = st.columns(2)
                comissao_c = cc1.number_input("🏷️ Comis. (%)", value=11.5, format="%.1f", key="c_com")
                margem_c_input = cc2.number_input("📈 Margem (%)", value=15.0, format="%.1f", key="c_mar", disabled=(modo=="preco"))

            st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)

            preco_c_manual = 0.0
            if modo == "preco":
                preco_c_manual = st.number_input("", value=240.00, format="%.2f", key="c_price_man", label_visibility="collapsed")
                res_c = calcular_cenario(0, preco_c_manual, comissao_c, "preco")
            else:
                res_c = calcular_cenario(margem_c_input, 0, comissao_c, "margem")
                st.markdown(f'<div class="big-price">R$ {res_c["preco"]:.2f}</div>', unsafe_allow_html=True)

            st.markdown(render_card_html(res_c["detalhes"], comissao_c, "ICMS"), unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="result-box">
                <div class="lucro-label">Lucro Líquido (Margem Real: {res_c['margem']:.1f}%)</div>
                <div class="lucro-valor">⬆ R$ {res_c['lucro']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    # CARD PREMIUM
    with col_premium:
        with st.container(border=True):
            h1p, h2p = st.columns([1, 1.5])
            h1p.markdown('<div class="card-title">Premium</div>', unsafe_allow_html=True)
            with h2p:
                cp1, cp2 = st.columns(2)
                comissao_p = cp1.number_input("🏷️ Comis. (%)", value=16.5, format="%.1f", key="p_com")
                margem_p_input = cp2.number_input("📈 Margem (%)", value=15.0, format="%.1f", key="p_mar", disabled=(modo=="preco"))

            st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)

            preco_p_manual = 0.0
            if modo == "preco":
                preco_p_manual = st.number_input("", value=265.00, format="%.2f", key="p_price_man", label_visibility="collapsed")
                res_p = calcular_cenario(0, preco_p_manual, comissao_p, "preco")
            else:
                res_p = calcular_cenario(margem_p_input, 0, comissao_p, "margem")
                st.markdown(f'<div class="big-price">R$ {res_p["preco"]:.2f}</div>', unsafe_allow_html=True)

            st.markdown(render_card_html(res_p["detalhes"], comissao_p, "ICMS"), unsafe_allow_html=True)

            st.markdown(f"""
            <div class="result-box">
                <div class="lucro-label">Lucro Líquido (Margem Real: {res_p['margem']:.1f}%)</div>
                <div class="lucro-valor">⬆ R$ {res_p['lucro']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    # --- LAYOUT CARD ÚNICO (SHOPEE, MAGALU, ETC) ---
    # Usamos colunas para centralizar o card na tela
    c_left, c_center, c_right = st.columns([1, 2, 1])
    
    with c_center:
        with st.container(border=True):
            h1u, h2u = st.columns([1, 1.5])
            # Título dinâmico (nome do canal sem emoji)
            nome_canal = canal.split(' ')[-1] if ' ' in canal else canal
            if "Livre" in canal: nome_canal = "Mercado Livre" # Fallback caso bugue
            if "KaBuM" in canal: nome_canal = "KaBuM!"
            if "Próprio" in canal: nome_canal = "Site Próprio"
            
            h1u.markdown(f'<div class="card-title">{nome_canal}</div>', unsafe_allow_html=True)
            
            with h2u:
                cu1, cu2 = st.columns(2)
                # Comissão padrão sugerida para outros marketplaces (ex: 18%)
                comissao_u = cu1.number_input("🏷️ Comis. (%)", value=18.0, format="%.1f", key="u_com")
                margem_u_input = cu2.number_input("📈 Margem (%)", value=15.0, format="%.1f", key="u_mar", disabled=(modo=="preco"))

            st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)

            preco_u_manual = 0.0
            if modo == "preco":
                preco_u_manual = st.number_input("", value=240.00, format="%.2f", key="u_price_man", label_visibility="collapsed")
                res_u = calcular_cenario(0, preco_u_manual, comissao_u, "preco")
            else:
                res_u = calcular_cenario(margem_u_input, 0, comissao_u, "margem")
                st.markdown(f'<div class="big-price">R$ {res_u["preco"]:.2f}</div>', unsafe_allow_html=True)

            # Renderiza card único
            st.markdown(render_card_html(res_u["detalhes"], comissao_u, "ICMS"), unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="result-box">
                <div class="lucro-label">Lucro Líquido (Margem Real: {res_u['margem']:.1f}%)</div>
                <div class="lucro-valor">⬆ R$ {res_u['lucro']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)