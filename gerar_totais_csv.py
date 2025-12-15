import json
import pandas as pd
from datetime import date
import numpy as np

def main():
    arquivo_csv = 'financeiro_pagar_import.csv'
    
    try:
        # Lê o CSV sem cabeçalho
        df = pd.read_csv(arquivo_csv, sep=None, engine='python', header=None)

        # Define as colunas
        df.columns = [
            'id', 'fornecedor', 'nro_documento', 'data_emissao', 'vencimento', 
            'data_baixa', 'data_pagamento', 'valor', 'situacao', 'observacao', 'origem'
        ]

        # --- LIMPEZA DE DADOS ---
        
        # 1. Strings: Remove espaços extras
        for col in ['fornecedor', 'nro_documento', 'situacao']:
            df[col] = df[col].astype(str).str.strip()

        # 2. Valores: Trata R$, pontos e vírgulas
        def limpar_valor(val):
            val = str(val).replace('R$', '').strip()
            if ',' in val and '.' in val: 
                val = val.replace('.', '').replace(',', '.')
            elif ',' in val: 
                val = val.replace(',', '.')
            return val

        df['valor'] = df['valor'].apply(limpar_valor)
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)

        # 3. Datas: Tenta converter para YYYY-MM-DD, se falhar vira null
        cols_data = ['vencimento', 'data_emissao', 'data_baixa', 'data_pagamento']
        for col in cols_data:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
        # Substitui NaN por None (para virar null no JSON válido)
        df = df.replace({np.nan: None})

        # --- PARTE 1: O RESUMO (Para Dashboards) ---
        resumo = df.groupby(['fornecedor', 'situacao']).agg(
            total=('valor', 'sum'),
            qtd_titulos=('valor', 'count')
        ).reset_index().sort_values(by=['fornecedor', 'situacao'])

        # --- PARTE 2: OS DETALHES (Para a Tabela/Grid) ---
        # Ordenamos por vencimento para facilitar a visualização
        detalhes = df.sort_values(by='vencimento')

        # --- EXPORTAÇÃO ---
        dados_exportacao = {
            "gerado_em": str(date.today()),
            "dashboard_resumo": resumo.to_dict(orient='records'), # Dados agrupados
            "grid_detalhes": detalhes.to_dict(orient='records')   # Dados linha a linha
        }

        with open('totais_financeiro.json', 'w', encoding='utf-8') as f:
            json.dump(dados_exportacao, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Sucesso!")
        print(f"   - Resumo: {len(resumo)} grupos gerados.")
        print(f"   - Detalhes: {len(detalhes)} títulos exportados.")

    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{arquivo_csv}' não encontrado.")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
