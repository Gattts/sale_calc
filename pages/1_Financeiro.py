import streamlit as st
import json
import pandas as pd
import os
import sys
from datetime import date, datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(raiz_projeto)

from gerar_totais_csv import main as gerar_dados

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Financeiro", page_icon="💰", layout="wide")

# --- FUNÇÕES ---
def carregar_dados():
    arquivo_json = os.path.join(raiz_projeto, 'totais_financeiro.json')
    
    if not os.path.exists(arquivo_json):
        gerar_dados()
        
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("JSON não encontrado.")
        return None

def destacar_situacao(val):
    """Define as cores da tabela baseado no texto da célula"""
    color = ''
    font_color = 'black'
    font_weight = 'normal'
    
    if val == 'Pago':
        color = '#d4edda' # Verde claro
        font_color = '#155724'
        font_weight = 'bold'
    elif val == 'Atrasado':
        color = '#f8d7da' # Vermelho claro
        font_color = '#721c24'
        font_weight = 'bold'
    elif val == 'Aberto':
        color = '#fff3cd' # Amarelo claro
        font_color = '#856404'
        font_weight = 'bold'
        
    return f'background-color: {color}; color: {font_color}; font-weight: {font_weight};'

# --- INTERFACE ---
st.title("📊 Gestão de Contas a Pagar")

if st.button("🔄 Atualizar Dados"):
    with st.spinner('Processando...'):
        gerar_dados()
        st.rerun()

dados = carregar_dados()

if dados:
    # Carrega dados brutos
    df = pd.DataFrame(dados['grid_detalhes'])

    # ==============================================================================
    # CORREÇÃO CRÍTICA DE DATAS E STATUS
    # ==============================================================================
    
    # 1. Converter a coluna 'vencimento' (que vem como texto) para DATA REAL
    df['vencimento_dt'] = pd.to_datetime(df['vencimento'], errors='coerce').dt.date
    
    # 2. Pega a data de hoje
    hoje = date.today()

    # 3. Função Lógica de Status
    def recalcular_status(row):
        # Se no CSV já diz "Pago", confiamos no CSV
        if str(row['situacao']).strip().lower() == 'pago':
            return 'Pago'
        
        # Se não tem data de vencimento válida, consideramos Aberto
        if pd.isna(row['vencimento_dt']):
            return 'Aberto'
            
        # Lógica de Atraso
        # Se a data de vencimento é MENOR que hoje -> ATRASADO
        if row['vencimento_dt'] < hoje:
            return 'Atrasado'
        else:
            return 'Aberto'

    # 4. Aplica a lógica linha a linha criando uma NOVA coluna 'status_real'
    df['status_real'] = df.apply(recalcular_status, axis=1)
    
    # ==============================================================================

    # --- FILTROS (SIDEBAR) ---
    st.sidebar.header("Filtros Avançados")
    
    # Usamos a coluna NOVA 'status_real' para os filtros e gráficos
    todas_situacoes = df['status_real'].unique()
    todos_fornecedores = df['fornecedor'].unique()
    
    sel_fornecedor = st.sidebar.multiselect("Fornecedor", todos_fornecedores, default=todos_fornecedores)
    sel_situacao = st.sidebar.multiselect("Situação (Calculada)", todas_situacoes, default=todas_situacoes)

    # Filtra o DataFrame usando o status recalculado
    df_final = df[
        (df['fornecedor'].isin(sel_fornecedor)) & 
        (df['status_real'].isin(sel_situacao))
    ]

    # --- KPIs (INDICADORES) ---
    # Agora os totais vão bater com a realidade (Atrasado vs Aberto)
    col1, col2, col3, col4 = st.columns(4)
    
    total_filtrado = df_final['valor'].sum()
    val_atrasado = df_final[df_final['status_real'] == 'Atrasado']['valor'].sum()
    val_aberto = df_final[df_final['status_real'] == 'Aberto']['valor'].sum()
    val_pago = df_final[df_final['status_real'] == 'Pago']['valor'].sum()

    col1.metric("Total Visualizado", f"R$ {total_filtrado:,.2f}")
    col2.metric("⚠️ Vencidos/Atrasados", f"R$ {val_atrasado:,.2f}", delta="-Atenção" if val_atrasado > 0 else None)
    col3.metric("📅 A Vencer (Aberto)", f"R$ {val_aberto:,.2f}")
    col4.metric("✅ Realizados (Pago)", f"R$ {val_pago:,.2f}")

    st.divider()

    # --- GRID COLORIDA ---
    # Mostramos a coluna 'status_real' no lugar da 'situacao' original do CSV
    df_display = df_final[['fornecedor', 'nro_documento', 'vencimento', 'valor', 'status_real']].copy()
    
    # Renomeia para ficar bonito na tela
    df_display.columns = ['Fornecedor', 'Documento', 'Vencimento', 'Valor', 'Situação Atual']

    # Aplica a estilização (Cores)
    st.dataframe(
        df_display.style.map(destacar_situacao, subset=['Situação Atual'])
        .format({"Valor": "R$ {:,.2f}"}), 
        use_container_width=True,
        height=600,
        hide_index=True
    )
