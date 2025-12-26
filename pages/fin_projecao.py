import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from utils.db import run_command, run_query

st.header("📈 Projeção e Custos Fixos")

# --- 1. Gerenciador de Custos Fixos ---
with st.expander("⚙️ Configurar Custos Fixos Mensais"):
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    desc = c1.text_input("Descrição (Ex: Aluguel)")
    val = c2.number_input("Valor R$", min_value=0.0)
    dia = c3.number_input("Dia Vencimento", min_value=1, max_value=31)
    cat = c4.selectbox("Tipo", ["Infra", "Pessoal", "Sistema"])
    
    if st.button("➕ Adicionar Fixo"):
        run_command("INSERT INTO gastos_fixos (descricao, valor, dia_vencimento, categoria) VALUES (:d, :v, :dia, :cat)",
                    {"d": desc, "v": val, "dia": dia, "cat": cat})
        st.rerun()

    # Tabela de Edição Rápida
    df_fixos = run_query("SELECT * FROM gastos_fixos WHERE ativo = TRUE")
    if not df_fixos.empty:
        st.dataframe(df_fixos[['id', 'descricao', 'valor', 'dia_vencimento', 'categoria']], hide_index=True)
        
        # Botão simples de exclusão por ID
        col_del, _ = st.columns([1, 4])
        id_del = col_del.number_input("ID para remover", min_value=0, step=1)
        if col_del.button("🗑️ Remover"):
            run_command("UPDATE gastos_fixos SET ativo=FALSE WHERE id=:id", {"id": id_del})
            st.rerun()

st.divider()

# --- 2. O Motor de Projeção (Calculadora de Futuro) ---
if not df_fixos.empty:
    custo_fixo_total = df_fixos['valor'].sum()
    
    # Busca contas variáveis já lançadas no 'contas_pagar' para somar na previsão
    # (Logica simplificada: Fixo + Contas Variáveis Abertas)
    
    projecao = []
    data_cursor = date.today().replace(day=1) # Começo deste mês
    
    for i in range(6): # Projetar 6 meses
        mes_str = data_cursor.strftime("%m/%Y")
        
        # Soma os fixos
        total_mes = custo_fixo_total
        
        # Soma variáveis já lançadas neste mês específico no contas_pagar
        query_var = """
            SELECT SUM(valor) as total FROM contas_pagar 
            WHERE situacao='Aberto' AND MONTH(vencimento) = :m AND YEAR(vencimento) = :y
        """
        df_var = run_query(query_var, {"m": data_cursor.month, "y": data_cursor.year})
        variavel = df_var.iloc[0]['total'] if df_var.iloc[0]['total'] else 0.0
        
        total_final = total_mes + float(variavel)
        
        projecao.append({
            "Mês": mes_str,
            "Fixo": total_mes,
            "Variável Lançado": variavel,
            "Total Previsto": total_final
        })
        
        # Avança um mês
        proximo_mes = data_cursor.month + 1 if data_cursor.month < 12 else 1
        proximo_ano = data_cursor.year + 1 if data_cursor.month == 12 else data_cursor.year
        data_cursor = date(proximo_ano, proximo_mes, 1)

    df_proj = pd.DataFrame(projecao)

    # Exibição
    k1, k2 = st.columns(2)
    k1.metric("Custo Fixo Recorrente", f"R$ {custo_fixo_total:,.2f}")
    k2.metric("Previsão Próximos 6 Meses", f"R$ {df_proj['Total Previsto'].sum():,.2f}")
    
    st.subheader("📊 Fluxo de Caixa Previsto")
    st.bar_chart(df_proj, x="Mês", y=["Fixo", "Variável Lançado"], color=["#FF9800", "#2196F3"], stack=True)

else:
    st.info("Cadastre custos fixos acima para ver a projeção.")