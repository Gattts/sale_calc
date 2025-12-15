import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Catálogo de Produtos", page_icon="📦", layout="wide")

# ==============================================================================
# 1. CONEXÃO COM O BANCO AWS
# ==============================================================================
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

def carregar_produtos():
    """Busca todos os produtos ativos no banco"""
    query = """
        SELECT id, sku, nome, quantidade, preco_partida, preco_final, nro_nf, data_compra, criado_em
        FROM produtos 
        ORDER BY data_compra DESC, id DESC
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
        return pd.DataFrame()

def excluir_produto(id_produto):
    """Remove um produto pelo ID"""
    query = "DELETE FROM produtos WHERE id = :id"
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(query), {"id": id_produto})
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False

# ==============================================================================
# 2. INTERFACE
# ==============================================================================
st.title("📦 Catálogo de Produtos (Nuvem)")

# Botão de refresh manual
if st.button("🔄 Atualizar Lista"):
    st.cache_data.clear()
    st.rerun()

df = carregar_produtos()

if not df.empty:
    # --- MÉTRICAS ---
    c1, c2, c3 = st.columns(3)
    qtd_total = df['quantidade'].sum()
    investimento = (df['quantidade'] * df['preco_partida']).sum()
    valor_venda_est = (df['quantidade'] * df['preco_final']).sum() # Estimativa baseada no custo final (mínimo)

    c1.metric("Itens em Estoque", qtd_total)
    c2.metric("Custo de Estoque", f"R$ {investimento:,.2f}")
    c3.metric("Valor Base (Min)", f"R$ {valor_venda_est:,.2f}", help="Baseado no Custo Final calculado")
    
    st.divider()

    # --- FILTROS ---
    col_search, col_del = st.columns([3, 1])
    
    with col_search:
        busca = st.text_input("🔍 Buscar por Nome ou SKU", placeholder="Ex: Monitor Dell...")
    
    # Filtra o DataFrame
    if busca:
        mask = df['nome'].str.contains(busca, case=False, na=False) | df['sku'].str.contains(busca, case=False, na=False)
        df_show = df[mask]
    else:
        df_show = df

    # --- TABELA ---
    st.subheader(f"Listagem ({len(df_show)} produtos)")
    
    # Renomear colunas para ficar bonito
    df_display = df_show[['id', 'sku', 'nome', 'nro_nf', 'quantidade', 'preco_partida', 'preco_final', 'data_compra']].copy()
    df_display.columns = ['ID', 'SKU', 'Produto', 'NF', 'Qtd', 'Preço Compra', 'Custo Final', 'Data']
    
    # Formatação visual
    st.dataframe(
        df_display.style.format({
            "Preço Compra": "R$ {:,.2f}",
            "Custo Final": "R$ {:,.2f}",
            "Data": "{:%d/%m/%Y}"
        }),
        use_container_width=True,
        hide_index=True,
        height=500
    )

    # --- ÁREA DE EXCLUSÃO ---
    with col_del:
        with st.container(border=True):
            st.write("🗑️ **Excluir Item**")
            id_para_excluir = st.number_input("ID do Produto", min_value=0, value=0, help="Veja o ID na tabela ao lado")
            
            if st.button("Excluir", type="primary"):
                if id_para_excluir > 0:
                    # Verifica se existe antes de tentar apagar (opcional, mas bom pra UX)
                    if id_para_excluir in df['id'].values:
                        if excluir_produto(id_para_excluir):
                            st.toast(f"Produto ID {id_para_excluir} removido!", icon="🗑️")
                            import time
                            time.sleep(1) # Espera um pouquinho pro toast aparecer
                            st.rerun()
                    else:
                        st.error("ID não encontrado.")
                else:
                    st.warning("Informe um ID válido.")

else:
    st.info("O catálogo está vazio. Cadastre produtos na página inicial.")
