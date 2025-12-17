import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Histórico de Compras", page_icon="🛍️", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; }
    .label-info { font-size: 13px; color: #555; font-weight: bold; }
    .value-info { font-size: 16px; color: #000; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. CONEXÃO AWS
# ==============================================================================
DB_HOST = "market-db.clsgwcgyufqp.us-east-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "Sigmacomjp25"
DB_NAME = "marketmanager"

@st.cache_resource
def get_engine():
    return create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

def run_command(query, params):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Erro: {e}")
        return False

def carregar_historico():
    query = """
        SELECT p.id, p.sku, p.nome, p.nro_nf, p.data_compra, p.quantidade, 
               p.preco_partida, p.ipi_percent, p.icms_percent, p.preco_final,
               p.fornecedor
        FROM produtos p
        ORDER BY p.data_compra DESC, p.id DESC
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception as e:
        return pd.DataFrame()

# ==============================================================================
# 2. INTERFACE
# ==============================================================================
st.title("🛍️ Histórico de Compras")

col_refresh, col_space = st.columns([1, 6])
if col_refresh.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

df = carregar_historico()

if not df.empty:
    # --- ÁREA DE FILTROS ---
    with st.expander("🔍 Filtros Avançados", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        
        # Filtro 1: Texto
        busca = f1.text_input("Produto/SKU", placeholder="Nome ou SKU")
        
        # Filtro 2: Fornecedor
        lista_fornecedores = sorted(list(set(df['fornecedor'].dropna().unique())))
        forn_sel = f2.multiselect("Fornecedor", options=lista_fornecedores)
        
        # Filtro 3: NF
        nf_busca = f3.text_input("Nota Fiscal", placeholder="Nº NF")
        
        # Filtro 4: Data
        data_range = f4.date_input("Período da Compra", value=[], help="Selecione Data Inicial e Final")

    # APLICAÇÃO DOS FILTROS (NO DATAFRAME)
    df_filtrado = df.copy()
    
    if busca:
        mask = df_filtrado['nome'].str.contains(busca, case=False, na=False) | df_filtrado['sku'].str.contains(busca, case=False, na=False)
        df_filtrado = df_filtrado[mask]
        
    if forn_sel:
        df_filtrado = df_filtrado[df_filtrado['fornecedor'].isin(forn_sel)]
        
    if nf_busca:
        df_filtrado = df_filtrado[df_filtrado['nro_nf'].astype(str).str.contains(nf_busca, case=False)]
        
    if len(data_range) == 2:
        start_date, end_date = data_range
        # Converte para datetime para comparar
        df_filtrado['data_compra'] = pd.to_datetime(df_filtrado['data_compra']).dt.date
        df_filtrado = df_filtrado[(df_filtrado['data_compra'] >= start_date) & (df_filtrado['data_compra'] <= end_date)]

    # --- RESULTADO AGRUPADO ---
    skus_unicos = df_filtrado['sku'].unique()
    
    if len(df_filtrado) == 0:
        st.warning("Nenhum registro encontrado com esses filtros.")
    else:
        st.caption(f"Mostrando {len(skus_unicos)} produtos distintos em {len(df_filtrado)} compras.")
        
        for sku in skus_unicos:
            historico_produto = df_filtrado[df_filtrado['sku'] == sku]
            ultima_compra = historico_produto.iloc[0]
            
            nome_prod = ultima_compra['nome']
            data_recente = pd.to_datetime(ultima_compra['data_compra']).strftime('%d/%m/%Y')
            preco_recente = ultima_compra['preco_final']
            
            # Título do Expander
            with st.expander(f"📦 {sku} | {nome_prod} — Última: R$ {preco_recente:,.2f} ({data_recente})"):
                
                # Dados Principais
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"<div class='label-info'>Fornecedor</div><div class='value-info'>{ultima_compra['fornecedor']}</div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='label-info'>Preço NF (Un)</div><div class='value-info'>R$ {ultima_compra['preco_partida']:,.2f}</div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='label-info'>Custo Final</div><div class='value-info'>R$ {ultima_compra['preco_final']:,.2f}</div>", unsafe_allow_html=True)
                c4.markdown(f"<div class='label-info'>Nota Fiscal</div><div class='value-info'>{ultima_compra['nro_nf']}</div>", unsafe_allow_html=True)

                st.divider()
                
                # Tabela de Histórico
                st.markdown("###### 🕒 Histórico de Entradas")
                cols_show = ['data_compra', 'nro_nf', 'quantidade', 'preco_partida', 'preco_final']
                
                # Prepara tabela visual
                df_visual = historico_produto[cols_show].copy()
                df_visual.columns = ['Data', 'NF', 'Qtd', 'Vlr NF', 'Custo Final']
                df_visual['Data'] = pd.to_datetime(df_visual['Data']).dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_visual.style.format({'Vlr NF': 'R$ {:,.2f}', 'Custo Final': 'R$ {:,.2f}'}),
                    use_container_width=True,
                    hide_index=True
                )
                
                # --- ÁREA DE EXCLUSÃO ---
                st.markdown("---")
                col_del_txt, col_del_btn = st.columns([3, 1])
                
                # Selectbox para escolher qual registro apagar (pelo ID, mostrando a data/NF)
                opcoes_exclusao = {f"ID {row['id']} - NF {row['nro_nf']} ({pd.to_datetime(row['data_compra']).strftime('%d/%m')})": row['id'] for idx, row in historico_produto.iterrows()}
                
                with col_del_txt:
                    registro_para_apagar = st.selectbox("Selecione um registro para excluir:", options=list(opcoes_exclusao.keys()), key=f"sel_{sku}")
                
                with col_del_btn:
                    st.write("") # Espaço para alinhar
                    st.write("") 
                    if st.button("🗑️ Excluir Registro", key=f"btn_{sku}", type="primary"):
                        id_apagar = opcoes_exclusao[registro_para_apagar]
                        if run_command("DELETE FROM produtos WHERE id = :id", {"id": id_apagar}):
                            st.toast("Registro removido!", icon="🗑️")
                            time.sleep(1)
                            st.rerun()

else:
    st.info("O banco de dados de produtos está vazio.")
