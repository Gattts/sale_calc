# Tabelas e Funções Puras (Sem Streamlit aqui para manter rápido)

TABELA_FRETE_ML = {
    "79-99": [(0.3, 11.97), (0.5, 12.87), (1.0, 13.47), (2.0, 14.07), (3.0, 14.97), (4.0, 16.17), (5.0, 17.07), (9.0, 26.67), (13.0, 39.57)],
    "100-119": [(0.3, 13.97), (0.5, 15.02), (1.0, 15.72), (2.0, 16.42), (3.0, 17.47), (4.0, 18.87), (5.0, 19.92), (9.0, 31.12), (13.0, 46.17)],
    "120-149": [(0.3, 15.96), (0.5, 17.16), (1.0, 17.96), (2.0, 18.76), (3.0, 19.96), (4.0, 21.56), (5.0, 22.76), (9.0, 35.56), (13.0, 52.76)],
    "150-199": [(0.3, 17.96), (0.5, 19.31), (1.0, 20.21), (2.0, 21.11), (3.0, 22.46), (4.0, 24.26), (5.0, 25.61), (9.0, 40.01), (13.0, 59.36)],
    "200+": [(0.3, 19.95), (0.5, 21.45), (1.0, 22.45), (2.0, 23.45), (3.0, 24.95), (4.0, 26.95), (5.0, 28.45), (9.0, 44.45), (13.0, 65.95)]
}

def str_to_float(valor_str):
    if not valor_str: return 0.0
    if isinstance(valor_str, (float, int)): return float(valor_str)
    try:
        return float(str(valor_str).replace(',', '.').strip())
    except:
        return 0.0

def obter_taxa_fixa_ml(preco):
    if preco >= 79.00: return 0.00
    elif preco >= 50.00: return 6.75
    elif preco >= 29.00: return 6.50
    elif preco > 12.50: return 6.25
    else: return 0.50

def obter_frete_ml_tabela(preco, peso):
    if preco < 79.00: return 0.00
    faixa = "200+"
    if 79 <= preco < 100: faixa = "79-99"
    elif 100 <= preco < 120: faixa = "100-119"
    elif 120 <= preco < 150: faixa = "120-149"
    elif 150 <= preco < 200: faixa = "150-199"
    
    lista = TABELA_FRETE_ML.get(faixa, TABELA_FRETE_ML["200+"])
    for limite, valor in lista:
        if peso <= limite: return valor
    return lista[-1][1]

def calcular_custo_aquisicao(pc, frete, ipi, outros, st_val, icms_frete, icms_prod, l_real):
    v_pc, v_frete, v_ipi = str_to_float(pc), str_to_float(frete), str_to_float(ipi)
    v_outros, v_st = str_to_float(outros), str_to_float(st_val)
    v_icms_frete, v_icms_prod = str_to_float(icms_frete), str_to_float(icms_prod)

    valor_ipi = v_pc * (v_ipi / 100)
    preco_medio = v_pc + v_frete + valor_ipi + v_outros + v_st
    
    credito_icms = 0.0
    if l_real:
        c_frete = v_frete * (v_icms_frete / 100)
        c_prod = v_pc * (v_icms_prod / 100)
        credito_icms = c_frete + c_prod
    
    credito_pis_cofins = preco_medio * (0.0925) if l_real else 0.0 
    
    total_creditos = credito_icms + credito_pis_cofins
    custo_final = preco_medio - total_creditos
    
    return {'custo_final': custo_final, 'creditos': total_creditos, 'icms_rec': credito_icms, 'pis_cof_rec': credito_pis_cofins}

def calcular_cenario(margem_alvo, preco_manual, comissao, modo, canal, custo_base, impostos, peso, is_full, armaz):
    v_margem = str_to_float(margem_alvo)
    v_preco_man = str_to_float(preco_manual)
    v_comissao = str_to_float(comissao)
    v_icms = str_to_float(impostos['icms']) / 100
    v_difal = str_to_float(impostos['difal']) / 100
    v_peso = str_to_float(peso)
    v_armaz = str_to_float(armaz)

    imposto_total = v_icms + v_difal + 0.0925
    perc_variaveis = imposto_total + (v_comissao/100) + (v_armaz/100 if not is_full else 0.0)
    
    taxa_fixa = 4.00 if "Shopee" in canal else 0.0
    custo_full = custo_base * (v_armaz/100) if is_full else 0.0
    
    preco = 0.0
    frete = 0.0

    if modo == "preco":
        preco = v_preco_man
        if "Mercado Livre" in canal:
            taxa_fixa += obter_taxa_fixa_ml(preco)
            frete = obter_frete_ml_tabela(preco, v_peso)
    else:
        divisor = 1 - (perc_variaveis + (v_margem/100))
        if divisor <= 0: divisor = 0.01
        custos_fixos = custo_base + custo_full + taxa_fixa
        
        if "Mercado Livre" in canal:
            frete_est = obter_frete_ml_tabela(100.0, v_peso)
            p_teste = (custos_fixos + frete_est) / divisor
            frete = obter_frete_ml_tabela(p_teste, v_peso)
            p_final = (custos_fixos + frete) / divisor
            
            if p_final >= 79.00:
                preco = p_final
            else:
                taxa_ml = obter_taxa_fixa_ml((custos_fixos + 6.00)/divisor)
                preco = (custos_fixos + taxa_ml) / divisor
                taxa_fixa += taxa_ml
                frete = 0.0
        else:
            preco = custos_fixos / divisor

    receita_liq = preco * (1 - perc_variaveis) - frete - taxa_fixa - custo_full
    lucro = receita_liq - custo_base
    margem_real = (lucro / preco * 100) if preco > 0 else 0.0

    return {
        "preco": preco, "lucro": lucro, "margem": margem_real, "frete": frete,
        "detalhes": {"v_icms": preco*v_icms, "v_comissao": preco*(v_comissao/100), "v_taxa": taxa_fixa}
    }
