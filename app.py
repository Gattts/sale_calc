import streamlit as st
import json
import pandas as pd
import os
from datetime import date, datetime

# ==============================================================================
# 1. CONFIGURAÇÃO E DADOS ESTÁTICOS
# ==============================================================================
st.set_page_config(page_title="Calculadora Market", layout="wide", page_icon="🧮")

# Tabela de Fretes Mercado Livre
TABELA_FRETE_ML = {
    "79-99": [(0.3, 11.97), (0.5, 12.87), (1.0, 13.47), (2.0, 14.07), (3.0, 14.97), (4.0, 16.17), (5.0, 17.07), (9.0, 26.67), (13.0, 39.57), (17.0, 44.07), (23.0, 51.57), (30.0, 59.37), (40.0, 61.17), (50.0, 63.27), (60.0, 67.47), (70.0, 72.27), (80.0, 75.57), (90.0, 83.97), (100.0, 95.97), (125.0, 107.37), (150.0, 113.97)],
    "100-119": [(0.3, 13.97), (0.5, 15.02), (1.0, 15.72), (2.0, 16.42), (3.0, 17.47), (4.0, 18.87), (5.0, 19.92), (9.0, 31.12), (13.0, 46.17), (17.0, 51.42), (23.0, 60.17), (30.0, 69.27), (40.0, 71.37), (50.0, 73.82), (60.0, 78.72), (70.0, 84.32), (80.0, 88.17), (90.0, 97.97), (100.0, 111.97), (125.0, 125.27)],
    "120-149": [(0.3, 15.96), (0.5, 17.16), (1.0, 17.96), (2.0, 18.76), (3.0, 19.96), (4.0, 21.56), (5.0, 22.76), (9.0, 35.56), (13.0, 52.76), (17.0, 58.76), (23.0, 68.76), (30.0, 79.16), (40.0, 81.56), (50.0, 84.36), (60.0, 89.96), (70.0, 96.36), (80.0, 100.76), (90.0, 111.96), (100.0, 127.96), (125.0, 143.16), (150.0, 151.96)],
    "150-199": [(0.3, 17.96), (0.5, 19.31), (1.0, 20.21), (2.0, 21.11), (3.0, 22.46), (4.0, 24.26), (5.0, 25.61), (9.0, 40.01), (13.0, 59.36), (17.0, 66.11), (23.0, 77.36), (30.0, 89.06), (40.0, 91.76), (50.0, 94.91), (60.0, 101.21), (70.0, 108.41), (80.0, 113.36), (90.0, 125.96), (100.0, 143.96), (125.0, 161.06)],
    "200+": [(0.3, 19.95), (0.5, 21.45), (1.0, 22.45), (2.0, 23.45), (3.0, 24.95), (4.0, 26.95), (5.0, 28.45), (9.0, 44.45), (13.0, 65.95), (17.0, 73.45), (23.0, 85.95), (30.0, 98.95), (40.0, 101.95), (50.0, 105.45), (60.0, 112.45), (70.0, 120.45), (80.0, 125.95), (90.0, 139.95), (100.0, 159.95), (125.0, 178.95), (150.0, 189.95)]
}

# ==============================================================================
# 2. FUNÇÕES DE SUPORTE
# ==============================================================================

def input_float(label, value, key, step=None):
    """Componente flexível: Aceita texto para permitir vírgula ou ponto."""
    val_str = st.text_input(label, value=str(value), key=key)
    try:
        return float(val_str.replace(',', '.'))
    except ValueError:
        return 0.0

def ler_catalogo():
    if os.path.exists('produtos.csv'):
        try:
            df = pd.read_csv('produtos.csv')
            cols_num = ['preco_partida', 'ipi_percent', 'icms_percent', 'preco_final']
            for c in cols_num:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def calcular_custo_aquisicao(preco_compra, frete, ipi_pct, outros, st_val, icms_frete, icms_prod, pis_pct, cofins_pct, is_lucro_real):
    valor_ipi = preco_compra * (ipi_pct / 100)
    preco_medio = preco_compra + frete + valor_ipi + outros + st_val
    
    credito_icms = 0.0
    credito_pis = 0.0
    credito_cofins = 0.0
    
    if is_lucro_real:
        # 1. ICMS (Base Cheia)
        c_icms_frete = frete * (icms_frete / 100)
        c_icms_prod = preco_compra * (icms_prod / 100)
        credito_icms = c_icms_frete + c_icms_prod
        
        # 2. PIS/COFINS (Base Reduzida: Exclui ICMS da base conforme Lei 14.754)
        # Base Produto = Valor Produto - ICMS Produto
        base_pis_cofins_prod = preco_compra - c_icms_prod
        # Base Frete = Valor Frete - ICMS Frete
        base_pis_cofins_frete = frete - c_icms_frete
        
        base_total = base_pis_cofins_prod + base_pis_cofins_frete
        
        credito_pis = base_total * (pis_pct / 100)
        credito_cofins = base_total * (cofins_pct / 100)
    
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
    if preco < 79.00: return 0.00
    faixa_key = "200+"
    if 79.00 <= preco < 100.00: faixa_key = "79-99"
    elif 100.00 <= preco < 120.00: faixa_key = "100-119"
    elif 120.00 <= preco < 150.00: faixa_key = "120-149"
    elif 150.00 <= preco < 200.00: faixa_key = "150-199"

    lista_precos = TABELA_FRETE_ML[faixa_key]
    for peso_limite, valor in lista_precos:
        if peso <= peso_limite: return valor
    return lista_precos[-1][1]

def calcular_cenario(margem_alvo, preco_venda_manual, comissao_pct, modo_calculo, canal_atual, custo_final_produto, detalhes_entrada, icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct):
    icms_rate, difal_rate = icms_venda_pct/100, difal_pct/100
    pis_rate, cofins_rate = detalhes_entrada.get('pis_rate', 1.65)/100, detalhes_entrada.get('cofins_rate', 7.60)/100
    total_impostos_pct = icms_venda_pct + difal_pct + ((1-icms_rate)*pis_rate*100) + ((1-icms_rate)*cofins_rate*100)
    
    frete_aplicado, taxa_fixa_extra, custo_armaz_fixo, taxa_armaz_variavel = 0.0, 0.0, 0.0, 0.0
    
    if is_fulfillment: custo_armaz_fixo = custo_final_produto * (armazenagem_pct/100)
    else: taxa_armaz_variavel = armazenagem_pct

    if "Shopee" in canal_atual: taxa_fixa_extra = 4.00
    elif "Mercado Livre" in canal_atual:
        if modo_calculo == "preco": frete_aplicado = obter_frete_ml(preco_venda_manual, peso_input)
        else:
            frete_temp = 0.0
            for _ in range(3):
                divisor = 1 - ((total_impostos_pct + comissao_pct + taxa_armaz_variavel + margem_alvo)/100)
                numerador = custo_final_produto + frete_temp + taxa_fixa_extra + custo_armaz_fixo
                preco_simulado = numerador / max(divisor, 0.01)
                frete_temp = obter_frete_ml(preco_simulado, peso_input)
            frete_aplicado = frete_temp

    if modo_calculo == "margem":
        divisor = 1 - ((total_impostos_pct + comissao_pct + taxa_armaz_variavel + margem_alvo)/100)
        preco_final = (custo_final_produto + frete_aplicado + taxa_fixa_extra + custo_armaz_fixo) / max(divisor, 0.01)
        margem_real = margem_alvo
    else: 
        preco_final = preco_venda_manual
        custos_variaveis = preco_final * ((total_impostos_pct + comissao_pct + taxa_armaz_variavel)/100)
        lucro_bruto = preco_final - custos_variaveis - (frete_aplicado + taxa_fixa_extra + custo_final_produto + custo_armaz_fixo)
        margem_real = (lucro_bruto / preco_final) * 100 if preco_final > 0 else 0

    val_icms = preco_final * icms_rate
    val_marketplace_total = (preco_final * (comissao_pct/100)) + frete_aplicado + taxa_fixa_extra + (custo_armaz_fixo if is_fulfillment else (preco_final*(taxa_armaz_variavel/100)))
    val_impostos_total = val_icms + (preco_final*difal_rate) + ((preco_final-val_icms)*pis_rate) + ((preco_final-val_icms)*cofins_rate)
    val_lucro = preco_final - val_impostos_total - val_marketplace_total - custo_final_produto
    val_repasse = preco_final - val_marketplace_total

    return {
        "preco": preco_final, "lucro": val_lucro, "margem": margem_real, "repasse": val_repasse,
        "detalhes": {
            "impostos_venda_total": val_impostos_total, "val_icms": val_icms, "val_difal": preco_final*difal_rate, "val_pis": (preco_final-val_icms)*pis_rate, "val_cofins": (preco_final-val_icms)*cofins_rate,
            "pis_rate_used": pis_rate*100, "cofins_rate_used": cofins_rate*100, "mkt_total": val_marketplace_total, "mkt_comissao": preco_final*(comissao_pct/100), "mkt_frete": frete_aplicado,
            "mkt_taxa_extra": taxa_fixa_extra, "mkt_armazenagem": (custo_armaz_fixo if is_fulfillment else (preco_final*(taxa_armaz_variavel/100))),
            "custo_prod_total": custo_final_produto, "preco_medio": detalhes_entrada.get('preco_medio', 0),
            "credito_icms": detalhes_entrada.get('credito_icms_total', 0), "credito_pis": detalhes_entrada.get('credito_pis', 0), "credito_cofins": detalhes_entrada.get('credito_cofins', 0),
        }
    }

def render_result_box(repasse, lucro, margem):
    if lucro > 0: cor, seta = "var(--success-color)", "⬆"
    elif lucro < 0: cor, seta = "var(--danger-color)", "⬇"
    else: cor, seta = "var(--text-muted)", "➖"
    return f"""<div class="result-box"><div style="border-right: 1px solid var(--border-color); padding-right: 10px;"><div class="lucro-label">Repasse Mkt</div><div class="lucro-valor" style="color: var(--secondary-color);">R$ {repasse:.2f}</div></div><div style="padding-left: 10px;"><div class="lucro-label">Lucro ({margem:.1f}%)</div><div class="lucro-valor" style="color: {cor};">{seta} R$ {lucro:.2f}</div></div></div>"""

def render_card_html(d, comissao, nome_icms, icms_venda_pct, difal_pct, is_fulfillment):
    base_calc = "Custo" if is_fulfillment else "Venda"
    armaz_html = f'<div class="sub-row"><span>Armaz. (% s/ {base_calc})</span> <span>R$ {d["mkt_armazenagem"]:.2f}</span></div>' if d.get('mkt_armazenagem', 0) > 0 else ""
    return f"""<div class="custom-accordion"><details><summary><span>(-) Impostos Venda</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['impostos_venda_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>{nome_icms} ({icms_venda_pct}%)</span> <span>R$ {d['val_icms']:.2f}</span></div><div class="sub-row"><span>DIFAL ({difal_pct}%)</span> <span>R$ {d['val_difal']:.2f}</span></div><div class="sub-row"><span>PIS ({d['pis_rate_used']:.2f}%)</span> <span>R$ {d['val_pis']:.2f}</span></div><div class="sub-row"><span>COFINS ({d['cofins_rate_used']:.2f}%)</span> <span>R$ {d['val_cofins']:.2f}</span></div></div></details><details><summary><span>(-) Custos Marketplace</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['mkt_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>Comissão ({comissao}%)</span> <span>R$ {d['mkt_comissao']:.2f}</span></div><div class="sub-row"><span>Frete</span> <span>R$ {d['mkt_frete']:.2f}</span></div>{armaz_html}</div></details><details><summary><span>(-) Custo Produto Final</span><span class="dotted-fill"></span><span class="summary-value">R$ {d['custo_prod_total']:.2f}</span></summary><div class="details-content"><div class="sub-row"><span>Preço Compra Médio</span> <span>R$ {d['preco_medio']:.2f}</span></div><div style="margin-top:5px;border-top:1px dashed var(--border-color);padding-top:4px;"><span style="font-size:0.9em;color:var(--text-muted);">Abatimentos:</span><div class="credit-row"><span>• ICMS</span> <span>- R$ {d['credito_icms']:.2f}</span></div><div class="credit-row"><span>• PIS</span> <span>- R$ {d['credito_pis']:.2f}</span></div><div class="credit-row"><span>• COFINS</span> <span>- R$ {d['credito_cofins']:.2f}</span></div></div></div></details></div>"""

# ==============================================================================
# 3. DIALOG: POP-UP DE REGISTRO
# ==============================================================================
@st.dialog("📋 Registrar Nova Compra")
def dialog_registrar_compra(dados_calculados, inputs_originais):
    st.caption("Preencha os detalhes para salvar no histórico de produtos.")
    
    nome_sugerido = ""
    sku_sugerido = ""
    
    if st.session_state.get('last_selected_product') and st.session_state.get('last_selected_product') != "Teste (Novo Produto)":
        full_text = st.session_state['last_selected_product']
        try:
            nome_sugerido = full_text.split(" (")[0]
            sku_sugerido = full_text.split(" (")[-1].replace(")", "")
        except:
            nome_sugerido = full_text

    sku = st.text_input("SKU (Código)", value=sku_sugerido)
    nome = st.text_input("Nome do Produto", value=nome_sugerido)
    
    c1, c2, c3 = st.columns(3)
    nf = c1.text_input("Nro Nota Fiscal")
    qtd = c2.number_input("Quantidade", min_value=1, step=1, value=1)
    data_compra = c3.date_input("Data da Compra", value=date.today())

    st.divider()
    st.markdown(f"**Custo Final Unitário:** R$ {dados_calculados['custo_final']:.2f}")

    if st.button("💾 Confirmar e Salvar", type="primary", use_container_width=True):
        if not sku or not nome or not nf:
            st.error("Preencha SKU, Nome e Nota Fiscal.")
        else:
            novo_registro = {
                'sku': sku,
                'nome': nome,
                'preco_partida': inputs_originais['p_compra'],
                'ipi_percent': inputs_originais['ipi'],
                'icms_percent': inputs_originais['icms_prod'],
                'preco_final': dados_calculados['custo_final'],
                'nro_nf': nf,
                'data_compra': data_compra.strftime('%Y-%m-%d'),
                'quantidade': qtd
            }
            
            arquivo = 'produtos.csv'
            df_novo = pd.DataFrame([novo_registro])
            
            if os.path.exists(arquivo):
                df_novo.to_csv(arquivo, mode='a', header=False, index=False)
            else:
                df_novo.to_csv(arquivo, mode='w', header=True, index=False)
                
            st.toast(f"Produto {sku} registrado com sucesso!", icon="✅")
            st.rerun()

# ==============================================================================
# 4. GESTÃO DE ESTADO
# ==============================================================================
if 'custo_produto_final' not in st.session_state: st.session_state['custo_produto_final'] = 0.00
if 'detalhes_custo' not in st.session_state: st.session_state['detalhes_custo'] = {'preco_medio': 0.00, 'credito_icms_total': 0.0, 'credito_pis': 0.0, 'credito_cofins': 0.0, 'pis_rate': 1.65, 'cofins_rate': 7.60}

# ==============================================================================
# 5. SIDEBAR
# ==============================================================================
with st.sidebar:
    c_head, c_tog = st.columns([2,1])
    c_head.header("⚙️ Config.")
    dark_mode = c_tog.toggle("🌘", value=False)
    
    canal = st.selectbox("🏪 Canal", ["🟡 Mercado Livre", "🟠 Shopee", "🔵 Amazon", "🔵 Magalu", "🟠 KaBuM!", "🌐 Site Próprio"])
    st.markdown("---")
    
    st.subheader("📦 Selecionar Produto")
    df_produtos = ler_catalogo()
    opcoes_produtos = ["Teste (Novo Produto)"]
    if not df_produtos.empty:
        df_produtos['label'] = df_produtos['nome'] + " (" + df_produtos['sku'].astype(str) + ")"
        opcoes_produtos += df_produtos['label'].unique().tolist()
    
    produto_selecionado = st.selectbox("Buscar no Catálogo", options=opcoes_produtos, key="last_selected_product")
    
    if produto_selecionado == "Teste (Novo Produto)":
        st.caption("Modo Manual: Edite na aba Cadastro.")
    else:
        if not df_produtos.empty:
            sku_selecionado = produto_selecionado.split("(")[-1].replace(")", "")
            item_data = df_produtos[df_produtos['sku'].astype(str) == sku_selecionado]
            if not item_data.empty:
                if 'data_compra' in item_data.columns:
                    item_data['data_compra'] = pd.to_datetime(item_data['data_compra'])
                    item_data = item_data.sort_values(by='data_compra', ascending=False)
                ultimo_registro = item_data.iloc[0]
                st.session_state['pc_cad'] = float(ultimo_registro.get('preco_partida', 0.0))
                st.session_state['ipi_cad'] = float(ultimo_registro.get('ipi_percent', 0.0))
                st.session_state['icmsp_cad'] = float(ultimo_registro.get('icms_percent', 0.0))
                st.success("Valores carregados!")
    
    custo_display = st.session_state.get('custo_produto_final', 0.0)
    st.markdown(f"""<div style="background:var(--hover-bg);padding:10px;border-radius:8px;border:1px solid var(--border-color);margin-bottom:10px;color:var(--text-color);"><small style="color:var(--text-muted)">Custo Final Calculado</small><br><b style="font-size:1.4em;color:var(--primary-color)">R$ {custo_display:,.2f}</b></div>""", unsafe_allow_html=True)

    st.subheader("💸 Tributos Venda")
    col_t1, col_t2 = st.columns(2)
    icms_venda_pct = input_float("ICMS (%)", 18.0, key="icms_venda_pct")
    difal_pct = input_float("DIFAL (%)", 0.0, key="difal_pct")
    
    st.subheader("🚚 Logística")
    is_fulfillment = st.toggle("⚡ Envio Full?", value=False)
    col_l1, col_l2 = st.columns(2)
    peso_input = input_float("Peso (Kg)", 0.3, key="peso_input")
    armazenagem_pct = input_float("Armaz. (%)", 0.0, key="armazenagem_pct")

# CSS
css_variables = "--primary-color: #1e3a8a; --secondary-color: #2c3e50; --card-bg: #ffffff; --text-color: #333; --text-muted: #666; --border-color: #e0e0e0; --success-color: #27ae60; --danger-color: #ef4444; --hover-bg: #f8f9fa; --dotted-color: #ccc;"
if dark_mode: css_variables = "--primary-color: #60a5fa; --secondary-color: #e2e8f0; --card-bg: #1f2937; --text-color: #e2e8f0; --text-muted: #9ca3af; --border-color: #374151; --success-color: #34d399; --danger-color: #f87171; --hover-bg: #374151; --dotted-color: #555;"
st.markdown(f"""<style>:root {{ {css_variables} }} .main-header {{ font-size: 2.2em; font-weight: bold; margin-bottom: 10px; color: var(--secondary-color); }} .card-title {{ font-size: 1.6em; font-weight: bold; color: var(--text-color); margin-top: 5px; }} .price-label {{ font-size: 0.85em; color: var(--text-muted); margin-bottom: -5px; margin-top: 10px; }} .big-price {{ font-size: 2.5em; font-weight: 800; color: var(--primary-color); margin-bottom: 15px; }} div[data-testid="stNumberInput"] input {{ font-weight: bold; color: var(--primary-color); background-color: transparent; }} .result-box {{ margin-top: 15px; padding-top: 10px; border-top: 1px solid var(--border-color); display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }} .lucro-label {{ font-size: 0.75em; font-weight: bold; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }} .lucro-valor {{ font-size: 1.5em; font-weight: bold; display: flex; align-items: center; justify-content: start; gap: 5px; }} .custom-accordion details {{ border: 1px solid var(--border-color); border-radius: 6px; margin-bottom: 8px; background-color: var(--card-bg); color: var(--text-color); }} .custom-accordion summary {{ display: flex; align-items: center; padding: 10px 12px; cursor: pointer; font-weight: 500; color: var(--text-color); }} .dotted-fill {{ flex-grow: 1; border-bottom: 2px dotted var(--dotted-color); margin: 0 8px; height: 0.8em; opacity: 0.4; }} .summary-value {{ font-weight: 700; color: var(--text-color); }} .details-content {{ padding: 8px 12px 12px 35px; background-color: var(--hover-bg); font-size: 0.85em; color: var(--text-color); border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; border-top: 1px solid var(--border-color); }} .sub-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; }} .credit-row {{ display: flex; justify-content: space-between; margin-bottom: 2px; color: var(--success-color); font-size: 0.9em; padding-left: 10px; }} [data-testid="stVerticalBlock"] > [style*="border"] {{ border-color: var(--border-color) !important; background-color: var(--card-bg); }}</style>""", unsafe_allow_html=True)

# ==============================================================================
# 6. ÁREA PRINCIPAL
# ==============================================================================
tab_calc, tab_cadastro = st.tabs(["🧮 Calculadora", "📝 Cadastro de Custos"])

# --- ABA 1: CALCULADORA ---
with tab_calc:
    nome_canal_titulo = canal.split(' ', 1)[1] if ' ' in canal else canal
    st.markdown(f'<div class="main-header">🏷️ Calculadora - {nome_canal_titulo}</div>', unsafe_allow_html=True)
    if st.session_state['custo_produto_final'] <= 0: st.warning("⚠️ O custo do produto está zerado. Vá na aba 'Cadastro de Custos' e clique em 'Simular' ou 'Registrar' para começar.")
    
    tipo_calculo = st.radio("🎯 O que você deseja definir?", ["Definir Margem (%)", "Definir Preço de Venda (R$)"], horizontal=True)
    modo = "margem" if "Margem" in tipo_calculo else "preco"
    st.write("") 

    if "Mercado Livre" in canal:
        col_c, col_p = st.columns(2, gap="medium")
        for col, tipo_anuncio, com_padrao, price_padrao in [(col_c, "Clássico", 11.5, 75.0), (col_p, "Premium", 16.5, 85.0)]:
            with col:
                with st.container(border=True):
                    h1, h2 = st.columns([1, 1.5])
                    h1.markdown(f'<div class="card-title">{tipo_anuncio}</div>', unsafe_allow_html=True)
                    with h2:
                        cc1, cc2 = st.columns(2)
                        com = input_float("🏷️ Comis.", com_padrao, key=f"c_{tipo_anuncio}")
                        margem_in = input_float("📈 Margem", 15.0, key=f"m_{tipo_anuncio}")
                    st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)
                    if modo == "preco":
                        price_man = input_float("", price_padrao, key=f"p_{tipo_anuncio}")
                        res = calcular_cenario(0, price_man, com, "preco", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                    else:
                        res = calcular_cenario(margem_in, 0, com, "margem", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                    st.markdown(f'<div class="big-price">R$ {res["preco"]:.2f}</div>', unsafe_allow_html=True)
                    st.markdown(render_card_html(res["detalhes"], com, "ICMS", icms_venda_pct, difal_pct, is_fulfillment), unsafe_allow_html=True)
                    st.markdown(render_result_box(res['repasse'], res['lucro'], res['margem']), unsafe_allow_html=True)
    else:
        c_left, c_center, c_right = st.columns([1, 2, 1])
        with c_center:
            with st.container(border=True):
                h1u, h2u = st.columns([1, 1.5])
                h1u.markdown(f'<div class="card-title">{nome_canal_titulo}</div>', unsafe_allow_html=True)
                with h2u:
                    cu1, cu2 = st.columns(2)
                    com = input_float("🏷️ Comis.", 18.0, key="c_u")
                    margem_in = input_float("📈 Margem", 15.0, key="m_u")
                st.markdown('<p class="price-label">Preço Calculado</p>', unsafe_allow_html=True)
                if modo == "preco":
                    price_man = input_float("", 100.00, key="p_u")
                    res = calcular_cenario(0, price_man, com, "preco", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                else:
                    res = calcular_cenario(margem_in, 0, com, "margem", canal, st.session_state['custo_produto_final'], st.session_state['detalhes_custo'], icms_venda_pct, difal_pct, peso_input, is_fulfillment, armazenagem_pct)
                st.markdown(f'<div class="big-price">R$ {res["preco"]:.2f}</div>', unsafe_allow_html=True)
                st.markdown(render_card_html(res["detalhes"], com, "ICMS", icms_venda_pct, difal_pct, is_fulfillment), unsafe_allow_html=True)
                st.markdown(render_result_box(res['repasse'], res['lucro'], res['margem']), unsafe_allow_html=True)

# --- ABA 2: CADASTRO ---
with tab_cadastro:
    st.markdown("## 📝 Editor de Custos de Produtos")
    st.caption("Preencha os dados da Nota Fiscal. Use 'Simular' para testar ou 'Registrar' para salvar no estoque.")
    
    col_form, col_resumo = st.columns([2, 1], gap="large")
    
    with col_form:
        with st.container(border=True):
            if produto_selecionado != "Teste (Novo Produto)": st.info(f"Baseado no produto: {produto_selecionado}")
            l_real = st.toggle("Lucro Real?", value=True, key="regime_cad")
            
            c1, c2, c3 = st.columns(3)
            p_compra = input_float("Preço Compra ($)", 0.0, key="pc_cad")
            p_frete = input_float("Frete Entrada ($)", 0.0, key="fr_cad")
            p_ipi = input_float("IPI (%)", 0.0, key="ipi_cad")
            
            c4, c5 = st.columns(2)
            p_outros = input_float("Outros Custos ($)", 0.0, key="out_cad")
            p_st = input_float("ICMS ST ($)", 0.0, key="st_cad")
            
            st.markdown("#### Créditos")
            cc1, cc2 = st.columns(2)
            icms_fr_pct = input_float("ICMS Frete (%)", 0.0, key="icmsf_cad")
            travado = (p_st > 0)
            if travado:
                st.caption("ICMS Prod. bloqueado (ST > 0)")
                icms_pr_pct = 0.0
            else:
                icms_pr_pct = input_float("ICMS Produto (%)", 12.0, key="icmsp_cad")
            
            is_imp = st.toggle("Importação?", False, key="imp_cad")
            pis_c, cofins_c = (2.10, 9.65) if is_imp else (1.65, 7.60)
            st.caption(f"PIS: {pis_c}% | COFINS: {cofins_c}%")

            st.write("")
            col_b1, col_b2 = st.columns(2)
            
            if col_b1.button("🔄 SIMULAR CUSTO (CACHE)", use_container_width=True):
                res = calcular_custo_aquisicao(p_compra, p_frete, p_ipi, p_outros, p_st, icms_fr_pct, icms_pr_pct, pis_c, cofins_c, l_real)
                st.session_state['custo_produto_final'] = res['custo_final']
                st.session_state['detalhes_custo'] = res
                st.session_state['preview_cadastro'] = res
                st.toast("Custo simulado! Veja na aba Calculadora.", icon="🟦")

            if col_b2.button("💾 REGISTRAR COMPRA (CSV)", type="primary", use_container_width=True):
                res = calcular_custo_aquisicao(p_compra, p_frete, p_ipi, p_outros, p_st, icms_fr_pct, icms_pr_pct, pis_c, cofins_c, l_real)
                inputs_raw = {'p_compra': p_compra, 'ipi': p_ipi, 'icms_prod': icms_pr_pct}
                dialog_registrar_compra(res, inputs_raw)
            
    with col_resumo:
        if 'preview_cadastro' in st.session_state:
            res = st.session_state['preview_cadastro']
            st.info(f"### Custo Final: R$ {res['custo_final']:.2f}")
            st.write(f"Preço Médio: R$ {res['preco_medio']:.2f}")
            st.success(f"Créditos Recuperados: R$ {res['credito_icms_total'] + res['credito_pis'] + res['credito_cofins']:.2f}")
            st.divider()
            st.markdown("👉 **Vá para a aba 'Calculadora' para ver o preço de venda.**")
