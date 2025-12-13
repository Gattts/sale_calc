# 🏷️ Calculadora de Precificação E-commerce

> **Versão:** 2.0 (Stable) | **Stack:** Python + Streamlit

Uma ferramenta robusta de precificação para Mercado Livre, Shopee e outros marketplaces, com suporte a cálculo de impostos (Lucro Real/Presumido), frete dinâmico e logística Full/Flex.

-----

## 📖 Sobre o Projeto

Este projeto é uma **Single Page Application (SPA)** construída com **Streamlit**. O objetivo é oferecer agilidade na tomada de decisão de preços, garantindo precisão fiscal e margem de lucro real.

A aplicação executa o script integralmente a cada interação do usuário, utilizando gerenciamento de estado para persistir dados complexos entre recarregamentos.

-----

## 🏗️ Arquitetura e Decisões Técnicas

### 1\. Configuração e Layout

```python
st.set_page_config(layout="wide")
```

  * **Decisão:** Uso de layout `wide` (tela cheia).
  * **Motivo:** O Mercado Livre exige a visualização simultânea de dois cenários (Clássico e Premium). O layout centralizado padrão cortaria a visualização lado a lado.

### 2\. Banco de Dados de Fretes (`TABELA_FRETE_ML`)

  * **Estrutura:** Dicionário Python na memória RAM.
  * **Decisão:** *Hardcoded* vs Banco de Dados.
  * **Motivo:** Performance. A tabela de fretes muda com baixa frequência. Manter os dados em memória elimina a latência de consultas SQL a cada simulação de preço, tornando a UI instantânea.

### 3\. Gerenciamento de Estado (`st.session_state`)

O Streamlit não retém variáveis entre interações por padrão. Utilizamos o `session_state` para:

  * Persistir o **Custo Final** calculado no Pop-up Fiscal.
  * Manter as alíquotas de impostos (PIS/COFINS) definidas na entrada para uso na saída.

### 4\. Interface (UI/UX) e CSS Injection

  * **Modo Escuro:** Implementado via variáveis CSS (`--primary-color`, etc.) trocadas dinamicamente pelo Python, evitando múltiplos arquivos `.css`.
  * **Accordion Customizado:** Substituímos o componente nativo `st.expander` por HTML puro (`<details>`, `<summary>`) injetado via `st.markdown`.
      * *Objetivo:* Compactar a visualização e customizar a seta de expansão (`›`), criando uma experiência de "App Nativo".

-----

## 🧮 Módulo Fiscal e Matemático

### 1\. Pop-up de Tributação (`@st.dialog`)

Calcula o custo real do produto considerando o regime tributário:

  * **Lucro Real:** Abate créditos de ICMS, PIS e COFINS do custo de aquisição.
  * **Trava de ICMS ST:** Se houver Substituição Tributária na entrada, o sistema bloqueia o crédito de ICMS automaticamente.
  * **Importação:** Ajusta alíquotas de PIS/COFINS automaticamente (2.10%/9.65%) vs Nacional (1.65%/7.60%).

### 2\. Motor de Cálculo (`calcular_cenario`)

Esta função resolve dois grandes desafios matemáticos:

#### A. Tratamento de Impostos (Base Dupla)

Seguindo a jurisprudência atual ("Tese do Século"), o PIS/COFINS de saída é calculado sobre a receita líquida.

```python
base_pis_cofins = preco_final - val_icms
```

Isso evita o "imposto sobre imposto", garantindo um preço final competitivo.

#### B. Algoritmo de Frete (Dependência Circular)

O custo do frete no Mercado Livre depende do preço de venda. Porém, o preço de venda (baseado na margem) depende do custo total (que inclui o frete).

  * **Solução:** Loop de Convergência.
      * O sistema simula o cálculo 3 vezes consecutivas. Isso permite que o valor matemático estabilize na faixa de frete correta da tabela.

#### C. Matemática Reversa (Markup Divisor)

Não aplicamos um *markup* multiplicador sobre o custo. Utilizamos a fórmula de divisor para garantir a margem líquida exata:

```python
divisor = 1 - ((impostos + comissao + margem) / 100)
Preço = Custo Total / divisor
```

### 3\. Logística (Full vs. Flex)

A chave `is_fulfillment` altera a natureza contábil da taxa de armazenagem:

  * **Full Ativo:** Armazenagem é tratada como **Custo Fixo** (soma ao numerador).
  * **Full Inativo:** Armazenagem é tratada como **Taxa Variável** sobre a venda (subtrai do divisor).

-----

## ⚠️ Detalhes de Implementação

### Renderização HTML (`render_card_html`)

Ao inspecionar o código, nota-se que o HTML dentro das f-strings **não possui indentação**.

  * **Motivo Crítico:** O interpretador Markdown do Streamlit é sensível a espaços em branco. Indentar o código HTML dentro do Python faz com que ele seja renderizado como "bloco de código" (texto puro) em vez de elementos visuais. A falta de indentação é proposital para garantir a renderização correta.

### Lógica Condicional de Layout

  * **Mercado Livre:** Renderiza 2 colunas (Clássico e Premium).
  * **Outros Canais:** Renderiza 1 coluna centralizada, reduzindo a carga cognitiva do operador.

-----

## 🚀 Como Rodar o Projeto

### Pré-requisitos

  * Python 3.8+
  * Streamlit

### Instalação Local

1.  Clone o repositório.
2.  Instale as dependências:
    ```bash
    pip install streamlit
    ```
3.  Execute a aplicação:
    ```bash
    streamlit run app.py
    ```

### Deploy (Streamlit Cloud)

1.  Suba o código no GitHub.
2.  Conecte sua conta no [share.streamlit.io](https://share.streamlit.io).
3.  Selecione o repositório e clique em **Deploy**.

-----

## 🔮 Roadmap (Futuro)

  * [ ] Integração com Banco de Dados para histórico de simulações.
  * [ ] Externalização da tabela de fretes (JSON/API).
  * [ ] Login de usuário com níveis de acesso.
