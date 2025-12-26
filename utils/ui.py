import streamlit as st

def carregar_css():
    with open("styles/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def card_resultado(titulo, dados):
    st.markdown(f"""
    <div class="result-card">
        <div class="card-title">{titulo}</div>
        <div class="card-price">R$ {dados['preco']:.2f}</div>
        <div class="card-profit">Lucro: R$ {dados['lucro']:.2f} ({dados['margem']:.1f}%)</div>
        <div class="card-footer">
            <span>🚚 Frete: {dados['frete']:.2f}</span>
            <span>💰 Taxas: {dados['detalhes']['v_comissao'] + dados['detalhes']['v_taxa']:.2f}</span>
        </div>
    </div>""", unsafe_allow_html=True)

def card_meta(valor):
    st.markdown(f"""
    <div class="card-azul">
        <h3>META: {valor}</h3>
    </div>
    """, unsafe_allow_html=True)