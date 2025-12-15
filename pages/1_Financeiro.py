import streamlit as st
import json
import pandas as pd
import os
import sys

# Garante que conseguimos importar scripts da pasta raiz (pai)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Agora importa seu script gerador que está na raiz
from gerar_totais_csv import main as gerar_dados

# --- Configuração da Página ---
st.set_page_config(
    page_title="Financeiro",
    page_icon="💰",
    layout="wide"
)

# --- Função Ajustada para Caminhos ---
def carregar_dados():
    # Caminho absoluto para garantir que ache os arquivos na raiz
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    arquivo_json = os.path.join(base_dir, 'totais_financeiro.json')
    
    # Se não existe, roda o gerador
    if not os.path.exists(arquivo_json):
        # Precisamos garantir que o gerador saiba onde está o CSV
        # Uma dica é mudar o diretório de trabalho temporariamente ou ajustar o script gerador
        # Mas vamos confiar que o script gerador procura na pasta atual dele
        os.chdir(base_dir) # Muda para a raiz para rodar o script
        gerar_dados()
        
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        return dados
    except FileNotFoundError:
        st.error("JSON não encontrado. Tente clicar em Recarregar.")
        return None

# --- Título e Botão de Atualização ---
st.title("📊 Painel Financeiro")

if st.button("🔄 Atualizar Dados"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(base_dir) # Garante que estamos na raiz para ler o CSV
    with st.spinner('Lendo CSV e atualizando...'):
        gerar_dados()
        st.rerun()

dados = carregar_dados()

if dados:
    # Separação dos dados
    df_resumo = pd.DataFrame(dados['dashboard_resumo'])
    df_detalhes = pd.DataFrame(dados['grid_detalhes'])

    # --- Filtros Laterais ---
    st.sidebar.header("Filtros")
    
    fornecedores = st.sidebar.multiselect(
        "Fornecedor", 
        options=df_detalhes['fornecedor'].unique(),
        default=df_detalhes['fornecedor'].unique()
    )
    
    situacoes = st.sidebar.multiselect(
        "Situação", 
        options=df_detalhes['situacao'].unique(),
        default=df_detalhes['situacao'].unique()
    )

    # Aplica filtro
    df_filtered = df_detalhes[
        (df_detalhes['fornecedor'].isin(fornecedores)) &
        (df_detalhes['situacao'].isin(situacoes))
    ]

    # --- KPIs ---
    col1, col2, col3 = st.columns(3)
    total_aberto = df_filtered[df_filtered['situacao'] != 'Pago']['valor'].sum()
    total_pago = df_filtered[df_filtered['situacao'] == 'Pago']['valor'].sum()
    
    col1.metric("A Pagar (Aberto)", f"R$ {total_aberto:,.2f}")
    col2.metric("Já Pago", f"R$ {total_pago:,.2f}")
    col3.metric("Total Filtrado", f"R$ {df_filtered['valor'].sum():,.2f}")

    st.divider()

    # --- Grid ---
    st.subheader("Detalhamento")
    st.dataframe(
        df_filtered,
        column_config={
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            "situacao": st.column_config.TextColumn("Status")
        },
        use_container_width=True,
        hide_index=True
    )
