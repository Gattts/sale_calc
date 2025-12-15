import json
import pandas as pd
from datetime import date
import numpy as np
import os

def main():
    # --- CORREÇÃO DE CAMINHOS (CRÍTICO) ---
    # Garante que o script ache o CSV na mesma pasta que ele está,
    # não importa de onde o comando python/streamlit foi chamado.
    DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
    arquivo_csv = os.path.join(DIRETORIO_ATUAL, 'financeiro_pagar_import.csv')
    arquivo_saida = os.path.join(DIRETORIO_ATUAL, 'totais_financeiro.json')
    
    try:
        # Lê o CSV sem cabeçalho (header=None)
        # sep=None deixa o python detectar se é virgula ou ponto e virgula
        df = pd.read_csv(arquivo_csv, sep=None, engine='python', header=None)

        # Mapeia as colunas conforme a estrutura do seu arquivo
        df.columns = [
            'id', 'fornecedor', 'nro_documento', 'data_emissao', 'vencimento', 
            'data_baixa', 'data_pagamento', 'valor', 'situacao', 'observacao', 'origem'
        ]

        # --- LIMPEZA DE DADOS ---
        # 1. Strings: Remove espaços em branco extras
        for col in ['fornecedor', 'nro_documento', 'situacao']:
            df[col] = df[col].astype(str).str.strip()

        # 2. Valores: Trata R$, pontos e vírgulas para converter em número
        def limpar_valor(val):
            val = str(val).replace('R$', '').strip()
            # Lógica para moeda brasileira (1.000,00)
            if ',' in val and '.' in val: 
                val = val.replace('.', '').replace(',', '.')
            elif ',' in val: 
                val = val.replace(',', '.')
            return val

        df['valor'] = df['valor'].apply(limpar_valor)
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)

        # 3. Datas: Padroniza para YYYY-MM-DD
        cols_data = ['vencimento', 'data_emissao', 'data_baixa', 'data_pagamento']
        for col in cols_data:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
        # Substitui NaN (Not a Number) por None para o JSON não quebrar
        df = df.replace({np.nan: None})

        # --- PREPARAÇÃO PARA O DASHBOARD (As chaves que faltavam) ---
        
        # 1. Resumo Agrupado (Para os Gráficos/Cards)
        resumo = df.groupby(['fornecedor', 'situacao']).agg(
            total=('valor', 'sum'),
            qtd_titulos=('valor', 'count')
        ).reset_index().sort_values(by=['fornecedor', 'situacao'])

        # 2. Detalhes (Para a Tabela/Grid)
        detalhes = df.sort_values(by='vencimento')

        # --- EXPORTAÇÃO FINAL ---
        dados_exportacao = {
            "gerado_em": str(date.today()),
            "dashboard_resumo": resumo.to_dict(orient='records'), # AQUI ESTÁ A CHAVE QUE FALTAVA
            "grid_detalhes": detalhes.to_dict(orient='records')
        }

        # Salva o arquivo JSON usando o caminho absoluto
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(dados_exportacao, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Sucesso! JSON atualizado em: {arquivo_saida}")

    except FileNotFoundError:
        print(f"❌ Erro Crítico: O arquivo CSV não foi encontrado em: {arquivo_csv}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()
