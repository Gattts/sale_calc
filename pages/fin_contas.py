import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.db import run_command, run_query
try:
    from utils.sync_db import buscar_dados_externos
except ImportError:
    buscar_dados_externos = None

st.header("💸 Contas a Pagar")

# ==============================================================================
# 1. SIDEBAR & SYNC (Mantido)
# ==============================================================================
with st.sidebar:
    st.header("🔄 Conexão Externa")
    if st.button("📡 Puxar do Banco Externo", type="primary"):
        if buscar_dados_externos is None:
            st.error("Arquivo sync_db não encontrado.")
        else:
            status = st.status("Sincronizando...", expanded=True)
            dados = buscar_dados_externos()
            if isinstance(dados, str): st.error(dados)
            elif dados.empty: status.write("Nada encontrado.")
            else:
                novos, att = 0, 0
                total_lido = len(dados)
                status.write(f"Lidos {total_lido} registros na origem. Processando...")
                
                for _, row in dados.iterrows():
                    sit_origem = str(row['situacao_nome']).lower()
                    if 'cancelad' in sit_origem: sit_final, dt_pg = 'Cancelado', None
                    elif any(x in sit_origem for x in ['paga', 'pago', 'liquidada']): sit_final, dt_pg = 'Pago', row['vencimento']
                    else: sit_final, dt_pg = 'Aberto', None

                    check = run_query("SELECT id, situacao FROM contas_pagar WHERE id_origem=:ido", {"ido": str(row['id_origem'])})
                    if check.empty:
                        run_command("""INSERT INTO contas_pagar (id_origem, fornecedor, nro_documento, valor, vencimento, descricao, categoria, situacao, data_pagamento)
                                       VALUES (:ido, :forn, :doc, :val, :venc, :desc, :cat, :sit, :dtpg)""",
                                    {"ido": str(row['id_origem']), "forn": row['fornecedor'], "doc": str(row['nro_documento']),
                                     "val": float(row['valor']), "venc": row['vencimento'], "desc": row['descricao'], 
                                     "cat": row['categoria'], "sit": sit_final, "dtpg": dt_pg})
                        novos += 1
                    else:
                        if check.iloc[0]['situacao'] != sit_final:
                            run_command("UPDATE contas_pagar SET situacao=:sit, data_pagamento=:dt WHERE id=:id", 
                                        {"sit": sit_final, "dt": dt_pg, "id": check.iloc[0]['id']})
                            att += 1
                status.update(label=f"Concluído! Total Processado: {total_lido}", state="complete", expanded=False)
                st.toast(f"Sync: {novos} novos | {att} atualizados")
                st.rerun()

# ==============================================================================
# 2. DIALOG DE BAIXA EM MASSA (NOVO!)
# ==============================================================================
@st.dialog("✅ Baixa em Massa (Pagamento em Lote)")
def dialog_baixa_massa(df_origem):
    st.caption("Selecione na tabela abaixo quais contas você deseja marcar como PAGAS.")
    
    # Prepara o DataFrame para edição (Adiciona checkbox)
    if df_origem.empty:
        st.warning("Não há contas pendentes para baixar na seleção atual.")
        return

    df_edit = df_origem[['id', 'fornecedor', 'nro_documento', 'vencimento', 'valor']].copy()
    df_edit.insert(0, "Pagar?", False) # Coluna de Checkbox

    # Editor de Dados (Tabela Interativa)
    edited_df = st.data_editor(
        df_edit,
        column_config={
            "Pagar?": st.column_config.CheckboxColumn("Selecionar", help="Marque para dar baixa", default=False),
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            "id": None # Oculta o ID
        },
        disabled=["fornecedor", "nro_documento", "valor", "vencimento"], # Bloqueia edição dos dados, libera só o check
        hide_index=True,
        use_container_width=True,
        height=400
    )

    # Filtra apenas os selecionados
    selecionados = edited_df[edited_df["Pagar?"] == True]

    st.divider()

    if not selecionados.empty:
        qtd = len(selecionados)
        total = selecionados['valor'].sum()

        c1, c2 = st.columns(2)
        c1.metric("Itens Selecionados", f"{qtd}")
        c2.metric("Valor Total a Pagar", f"R$ {total:,.2f}")

        # Data do Pagamento (Única para todos)
        dt_pg = st.date_input("Data do Pagamento", value=date.today())

        if st.button(f"💸 Confirmar Baixa ({qtd} contas)", type="primary", use_container_width=True):
            # Barra de progresso visual
            prog_bar = st.progress(0, text="Processando baixas...")
            
            ids_para_baixar = selecionados['id'].tolist()
            total_items = len(ids_para_baixar)
            
            for i, id_conta in enumerate(ids_para_baixar):
                run_command(
                    "UPDATE contas_pagar SET situacao='Pago', data_pagamento=:dt WHERE id=:id", 
                    {"dt": dt_pg, "id": id_conta}
                )
                prog_bar.progress((i + 1) / total_items)
            
            st.toast(f"Sucesso! {qtd} contas foram baixadas.", icon="✅")
            st.rerun()
    else:
        st.info("Marque as caixas na coluna 'Selecionar' para prosseguir.")


# ==============================================================================
# 3. INCLUSÃO MANUAL E HEADER (Mantido)
# ==============================================================================
with st.expander("➕ Inclusão Manual"):
    c1, c2, c3 = st.columns(3)
    forn, doc, cat = c1.text_input("Fornecedor"), c2.text_input("Nota"), c3.selectbox("Categoria", ["Estoque", "Infra", "Impostos", "Pessoal", "Mkt", "Outros"])
    c4, c5, c6 = st.columns(3)
    desc, val, venc = c4.text_input("Desc"), c5.number_input("Valor", min_value=0.0), c6.date_input("Vencimento")
    if st.button("Salvar"):
        run_command("INSERT INTO contas_pagar (fornecedor, nro_documento, categoria, descricao, valor, vencimento, situacao) VALUES (:f, :d, :c, :de, :v, :ve, 'Aberto')",
                    {"f": forn, "d": doc, "c": cat, "de": desc, "v": val, "ve": venc})
        st.rerun()

st.divider()

# ==============================================================================
# 4. KPI E FILTROS
# ==============================================================================
stats = run_query("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN situacao = 'Aberto' THEN 1 ELSE 0 END) as aberto,
        SUM(CASE WHEN situacao = 'Pago' THEN 1 ELSE 0 END) as pago,
        SUM(CASE WHEN situacao = 'Cancelado' THEN 1 ELSE 0 END) as canc
    FROM contas_pagar
""").iloc[0]

c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
c_kpi1.metric("📚 Total Registros (BD)", f"{stats['total']}")
c_kpi2.metric("🔴 Pendentes", f"{stats['aberto']}")
c_kpi3.metric("🟢 Pagos", f"{stats['pago']}")
c_kpi4.metric("🚫 Cancelados", f"{stats['canc']}")

with st.container(border=True):
    st.caption("🔍 Filtros de Visualização")
    c1, c2, c3, c4 = st.columns(4)
    b_forn = c1.text_input("Fornecedor", placeholder="Nome...")
    b_doc = c2.text_input("Documento", placeholder="Nota...")
    d_ini = c3.date_input("De", value=date(2023, 1, 1)) 
    d_fim = c4.date_input("Até", value=date(2026, 12, 31))

def get_data(situacao):
    sql = "SELECT * FROM contas_pagar WHERE situacao "
    if isinstance(situacao, list): sql += f"IN {tuple(situacao)} "
    else: sql += f"= '{situacao}' "
    
    params = {}
    if b_forn: sql += "AND fornecedor LIKE :f "; params['f'] = f"%{b_forn}%"
    if b_doc: sql += "AND nro_documento LIKE :d "; params['d'] = f"%{b_doc}%"
    
    col_data = "data_pagamento" if situacao == 'Pago' else "vencimento"
    sql += f"AND {col_data} BETWEEN :d1 AND :d2 ORDER BY {col_data} "
    sql += "DESC" if situacao == 'Pago' else "ASC"
    
    params.update({'d1': d_ini, 'd2': d_fim})
    return run_query(sql, params)

st.divider()

# ==============================================================================
# 5. LISTAGEM (COM BOTÃO DE MASSA)
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["🔴 Pendentes", "🟢 Pagos", "🚫 Cancelados"])

# --- ABA 1: PENDENTES ---
with tab1:
    df = get_data('Aberto')
    
    # CABEÇALHO DA ABA COM BOTÃO DE AÇÃO
    col_info, col_btn = st.columns([4, 1.5])
    
    if df.empty:
        st.info("Nada pendente neste período.")
    else:
        # Informações de totais
        col_info.markdown(f"**Exibindo {len(df)} contas** | Total Visível: **R$ {df['valor'].sum():,.2f}**")
        
        # Botão de Baixa em Massa
        if col_btn.button("✅ Baixa em Massa", use_container_width=True):
            dialog_baixa_massa(df) # Passa o DataFrame filtrado atual para o modal

        # Lista de Cards
        for _, row in df.iterrows():
            with st.container(border=True):
                c_inf, c_val, c_btn = st.columns([4, 1.5, 0.8])
                dt = pd.to_datetime(row['vencimento']).date()
                hoje = date.today()
                cor = "red" if dt < hoje else "orange" if dt == hoje else "green"
                txt_venc = "VENCIDO" if dt < hoje else "HOJE" if dt == hoje else "No prazo"
                
                with c_inf:
                    st.markdown(f"**{row['fornecedor']}**")
                    st.markdown(f"<span style='color:gray; font-size:12px'>Doc: {row['nro_documento']} | {row['categoria']}</span>", unsafe_allow_html=True)
                    st.markdown(f"Vence: :{cor}[**{dt.strftime('%d/%m/%Y')}**] ({txt_venc})")
                
                with c_val:
                    st.markdown(f"**R$ {row['valor']:,.2f}**")
                    if row['descricao']: st.caption(f"{row['descricao'][:30]}...")
                
                with c_btn:
                    if st.button("Baixar", key=f"pay_{row['id']}"):
                        run_command("UPDATE contas_pagar SET situacao='Pago', data_pagamento=:hj WHERE id=:id", 
                                    {"hj": date.today(), "id": row['id']})
                        st.rerun()

# --- ABA 2: PAGOS ---
with tab2:
    df = get_data('Pago')
    if df.empty: st.info("Nada pago neste período.")
    else:
        st.markdown(f"**Exibindo {len(df)} pagamentos** | Total: **R$ {df['valor'].sum():,.2f}**")
        for _, row in df.iterrows():
            with st.container(border=True):
                c_inf, c_val = st.columns([4, 1.5])
                dt_pg = pd.to_datetime(row['data_pagamento']).date() if row['data_pagamento'] else None
                str_dt = dt_pg.strftime('%d/%m/%Y') if dt_pg else "Data N/A"
                
                with c_inf:
                    st.markdown(f"✅ **{row['fornecedor']}**")
                    st.markdown(f"<span style='color:gray; font-size:12px'>Doc: {row['nro_documento']} | {row['categoria']}</span>", unsafe_allow_html=True)
                    st.markdown(f":green[Pago em: **{str_dt}**]")
                
                with c_val:
                    st.markdown(f":green[**R$ {row['valor']:,.2f}**]")

# --- ABA 3: CANCELADOS ---
with tab3:
    df = get_data('Cancelado')
    if df.empty: st.info("Nada cancelado neste período.")
    else:
        st.markdown(f"**Exibindo {len(df)} registros**")
        for _, row in df.iterrows():
            with st.container(border=True):
                c_inf, c_val = st.columns([4, 1.5])
                dt = pd.to_datetime(row['vencimento']).date()
                
                with c_inf:
                    st.markdown(f"🚫 ~~{row['fornecedor']}~~")
                    st.caption(f"Doc: {row['nro_documento']}")
                    st.markdown(f":grey[Venceria em: {dt.strftime('%d/%m/%Y')}]")
                
                with c_val:
                    st.markdown(f":grey[**R$ {row['valor']:,.2f}**]")