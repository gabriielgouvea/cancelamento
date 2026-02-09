# -*- coding: utf-8 -*-

"""
Arquivo: app_utils.py
Descrição: Contém todas as funções de lógica de negócio, validação,
formatação e constantes globais do aplicativo Veritas.
"""

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# --- Constantes Globais ---

PLANOS = {
    'Anual (12 meses)': {'valor': 359.00, 'duracao': 12},
    'Semestral (6 meses)': {'valor': 499.00, 'duracao': 6}
}
MOTIVOS_CANCELAMENTO = [
    "NÃO GOSTEI DO ATENDIMENTO DOS PROFESSORES",
    "NÃO GOSTEI DO ATENDIMENTO DA RECEPÇÃO",
    "ESTOU COM PROBLEMAS DE SAÚDE",
    "ESTOU COM DIFICULDADE FINANCEIRA",
    "MUDEI DE ENDEREÇO",
    "OUTROS"
]

# --- Funções de Validação ---

def validar_matricula(P):
    """Valida se a entrada é um número e tem no máximo 6 dígitos."""
    if len(P) > 6: 
        return False
    return str.isdigit(P) or P == ""

def validar_e_formatar_cpf_input(P):
    """Permite apenas números no campo de CPF, com limite de 11."""
    numeros = ''.join(filter(str.isdigit, P))
    if len(numeros) > 11: 
        return False
    return True

def limpar_cpf(cpf_sujo):
    """Remove toda formatação de um CPF."""
    return ''.join(filter(str.isdigit, cpf_sujo))

def validar_cpf_algoritmo(cpf):
    """Valida o CPF usando o algoritmo (dígitos verificadores)."""
    cpf = limpar_cpf(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11: 
        return False
    try:
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        if digito1 != int(cpf[9]): 
            return False
        
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        if digito2 != int(cpf[10]): 
            return False
    
    # --- VOLTANDO AO CÓDIGO ORIGINAL (COMO PEDIDO) ---
    except ValueError: 
        return False
    # --- FIM DA CORREÇÃO ---
    
    return True

# --- Funções de Formatação ---

def formatar_data(event, entry):
    """Formata automaticamente um campo de Entry para dd/mm/aaaa."""
    texto_atual = entry.get()
    numeros = "".join(filter(str.isdigit, texto_atual))
    data_formatada = ""
    
    if len(numeros) > 0: 
        data_formatada = numeros[:2]
    if len(numeros) > 2: 
        data_formatada += "/" + numeros[2:4]
    if len(numeros) > 4: 
        data_formatada += "/" + numeros[4:8]
        
    entry.delete(0, 'end')
    entry.insert(0, data_formatada)
    entry.icursor('end')

def formatar_reais(valor):
    """Formata um float para o padrão R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- Lógica de Negócio Principal (ATUALIZADA) ---

def logica_de_calculo(data_inicio, tipo_plano_str, parcelas_em_atraso_str, pagamento_hoje_confirmado=None, **kwargs):
    """
    Executa a lógica central de cálculo de cancelamento.
    Retorna um dicionário com o resultado ou com uma chave de erro.
    
    **kwargs pode incluir:
    - valor_mensalidade_override: (float) Usado para o novo plano de R$389.
    """
    try:
        parcelas_em_atraso = int(parcelas_em_atraso_str)
        
        # 1. Pega os dados base do plano (ex: 359.00 e 12 meses)
        plano_selecionado = PLANOS[tipo_plano_str]
        valor_mensalidade_base = plano_selecionado['valor'] 
        duracao_plano = plano_selecionado['duracao']
        
        data_hoje = date.today()

        if data_inicio < date(2024, 10, 1): 
            return {'erro_data': "A data de início não pode ser anterior a Outubro de 2024."}
        
        # --- LÓGICA DO NOVO PREÇO ---
        # Pega o valor passado pelo popup (ex: 389.00)
        valor_mensalidade_override = kwargs.get('valor_mensalidade_override', None)
        
        # O valor 'real' para atrasos/próxima parcela é o R$389 (se existir) ou o R$359 (base)
        valor_mensalidade_real = valor_mensalidade_override if valor_mensalidade_override is not None else valor_mensalidade_base
        
        # O valor 'para multa' é SEMPRE o R$359 (base) se for Anual
        if tipo_plano_str == 'Anual (12 meses)':
            valor_para_multa = valor_mensalidade_base # Sempre 359.00
        else:
            valor_para_multa = valor_mensalidade_real # Outros planos (Semestral) usam seu próprio valor
        # --- FIM DA LÓGICA DO PREÇO ---

        diff = relativedelta(data_hoje, data_inicio)
        meses_passados_total = diff.years * 12 + diff.months
        ultimo_vencimento_ocorrido = data_inicio + relativedelta(months=meses_passados_total)

        if data_hoje < ultimo_vencimento_ocorrido:
            meses_efetivamente_pagos = meses_passados_total
            proximo_vencimento = ultimo_vencimento_ocorrido
        else:
            meses_efetivamente_pagos = meses_passados_total + 1
            proximo_vencimento = ultimo_vencimento_ocorrido + relativedelta(months=1)

        valor_mensalidade_adicional = 0.0
        meses_a_pagar_adiantado = 0
        linha_mensalidade_adicional = "Não se aplica"

        if data_hoje.day == data_inicio.day and data_hoje >= data_inicio:
            if pagamento_hoje_confirmado is False:
                valor_mensalidade_adicional = valor_mensalidade_real # Usa valor REAL
                meses_a_pagar_adiantado = 1
                linha_mensalidade_adicional = f"R$ {valor_mensalidade_real:.2f} (referente a hoje - {data_hoje.strftime('%d/%m/%Y')})"
        else:
            dias_para_vencimento = (proximo_vencimento - data_hoje).days
            
            # Verifica se CAI na regra dos 30 dias (independente de estar isento ou não)
            caiu_regra_30_dias = (0 < dias_para_vencimento <= 30)
            
            # Só cobra se caiu na regra E NÃO foi solicitado isenção
            if caiu_regra_30_dias and not kwargs.get('isencao_proxima', False):
                valor_mensalidade_adicional = valor_mensalidade_real # Usa valor REAL
                meses_a_pagar_adiantado = 1
                linha_mensalidade_adicional = f"R$ {valor_mensalidade_real:.2f} (em {dias_para_vencimento} dias - {proximo_vencimento.strftime('%d/%m/%Y')})"
            
            # Se caiu na regra, mas foi isento, registramos que "caiu mas não cobrou"
            elif caiu_regra_30_dias and kwargs.get('isencao_proxima', False):
                 linha_mensalidade_adicional = "Isento (Regra 30 dias ignorada)"

        meses_restantes_contrato = duracao_plano - meses_efetivamente_pagos
        is_due_date_scenario = data_hoje.day == data_inicio.day and data_hoje >= data_inicio
        is_30_day_rule_scenario = meses_a_pagar_adiantado > 0 and not is_due_date_scenario

        if is_30_day_rule_scenario: 
            meses_para_multa = max(0, meses_restantes_contrato - 1)
        else: 
            meses_para_multa = max(0, meses_restantes_contrato)

        # --- CÁLCULOS ATUALIZADOS ---
        valor_multa = (meses_para_multa * valor_para_multa) * 0.10     # Usa valor PARA MULTA (359)
        valor_atrasado = parcelas_em_atraso * valor_mensalidade_real  # Usa valor REAL (389 ou 359)
        total_a_pagar = valor_atrasado + valor_mensalidade_adicional + valor_multa

        if data_hoje.day == data_inicio.day and data_hoje >= data_inicio:
            data_acesso_final = proximo_vencimento + relativedelta(days=-1)
        elif meses_a_pagar_adiantado > 0:
            data_acesso_final = proximo_vencimento + relativedelta(months=1, days=-1)
        else:
            # Se não pagou adiantado (seja porque não caiu na regra, ou porque foi ISENTO), o acesso termina antes
            data_acesso_final = proximo_vencimento + relativedelta(days=-1)

        return {
            'data_simulacao': data_hoje,
            'plano': tipo_plano_str,
            'valor_plano': valor_mensalidade_real, # Mostra o valor real (389 ou 359)
            'data_inicio_contrato': data_inicio,
            'parcelas_atrasadas_qtd': parcelas_em_atraso,
            'valor_atrasado': valor_atrasado,
            'linha_mensalidade_a_vencer': linha_mensalidade_adicional,
            'meses_para_multa': meses_para_multa,
            'valor_multa': valor_multa,
            'total_a_pagar': total_a_pagar,
            'data_acesso_final': data_acesso_final,
            'valor_proxima_parcela': valor_mensalidade_adicional,
            'vencimento_proxima': proximo_vencimento.strftime('%d/%m/%Y') if valor_mensalidade_adicional > 0 else "Não se aplica",
            # Flag nova para UI saber se deve mostrar botão
            'caiu_regra_30_dias': (0 < (proximo_vencimento - data_hoje).days <= 30) if data_hoje.day != data_inicio.day else False
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {'erro_geral': f"Erro no cálculo. Verifique os dados.\nDetalhe: {e}"}


def _contar_meses_entre_datas(data_inicio, data_fim):
    """Conta quantos vencimentos mensais ocorreram entre duas datas (inclusive fim)."""
    if data_fim <= data_inicio:
        return 0
    contador = 0
    proximo = data_inicio + relativedelta(months=1)
    while proximo <= data_fim:
        contador += 1
        proximo += relativedelta(months=1)
    return contador


def _contar_meses_pagos(data_inicio, data_ultimo_pagamento):
    """Conta quantos meses foram pagos, contando o primeiro mês."""
    if data_ultimo_pagamento < data_inicio:
        return 0
    contador = 1
    proximo = data_inicio + relativedelta(months=1)
    while proximo <= data_ultimo_pagamento:
        contador += 1
        proximo += relativedelta(months=1)
    return contador


def calcular_renegociacao(data_inicio, data_ultimo_pagamento, tipo_plano_str, **kwargs):
    """
    Calcula os dados de renegociação (cancelamento ou plano novo).

    **kwargs pode incluir:
    - valor_mensalidade_override: (float) Usado para o novo plano de R$389.
    """
    try:
        data_hoje = date.today()

        if data_inicio < date(2024, 10, 1):
            return {'erro_data': "A data de início não pode ser anterior a Outubro de 2024."}

        if data_inicio > data_hoje:
            return {'erro_data': "A data de início não pode ser futura."}

        if data_ultimo_pagamento > data_hoje:
            return {'erro_data': "A data da última mensalidade paga não pode ser futura."}

        if data_ultimo_pagamento < data_inicio:
            return {'erro_data': "A última mensalidade paga não pode ser anterior ao início do contrato."}

        plano_selecionado = PLANOS[tipo_plano_str]
        valor_mensalidade_base = plano_selecionado['valor']
        duracao_plano = plano_selecionado['duracao']

        valor_mensalidade_override = kwargs.get('valor_mensalidade_override', None)
        valor_mensalidade_real = valor_mensalidade_override if valor_mensalidade_override is not None else valor_mensalidade_base

        if tipo_plano_str == 'Anual (12 meses)':
            valor_para_multa = valor_mensalidade_base
        else:
            valor_para_multa = valor_mensalidade_real

        meses_utilizados = _contar_meses_pagos(data_inicio, data_ultimo_pagamento)
        meses_utilizados = min(meses_utilizados, duracao_plano)
        meses_restantes = max(0, duracao_plano - meses_utilizados)

        parcelas_abonadas_qtd = _contar_meses_entre_datas(data_ultimo_pagamento, data_hoje)
        valor_abonado = parcelas_abonadas_qtd * valor_mensalidade_real

        valor_multa = (meses_restantes * valor_para_multa) * 0.10

        return {
            'data_simulacao': data_hoje,
            'plano': tipo_plano_str,
            'valor_plano': valor_mensalidade_real,
            'data_inicio_contrato': data_inicio,
            'data_ultimo_pagamento': data_ultimo_pagamento,
            'meses_utilizados': meses_utilizados,
            'meses_restantes': meses_restantes,
            'parcelas_abonadas_qtd': parcelas_abonadas_qtd,
            'valor_abonado': valor_abonado,
            'valor_multa': valor_multa,
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {'erro_geral': f"Erro no cálculo. Verifique os dados.\nDetalhe: {e}"}