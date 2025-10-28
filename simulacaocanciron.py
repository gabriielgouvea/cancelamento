# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from dateutil.relativedelta import relativedelta
from docx import Document
import os
import sys
from docxtopdf import convert

# --- Variáveis Globais ---
calculo_resultado = {}
consultor_selecionado = None

# --- Lista de Consultores ---
CONSULTORES = [
    "GABRIEL GOUVÊA", "GUILHERME VIEIRA", "ALANA TELES", "NATALIA ROCHA",
    "RAPHAELA ALVES", "DAVI FERREIRA", "JANAINA SIBINELI", "LARISSA ROCHA",
    "ROBERTA FREIRIA", "JOÃO VITOR", "DANIELA MARTINS", "ROTIELY LOPES", "ROMULO ALVES", "GABRIEL FERNANDES"
]

# --- CONFIGURAÇÃO DOS PLANOS ---
PLANOS = {
    'Anual (12 meses)': {'valor': 359.00, 'duracao': 12},
    'Semestral (6 meses)': {'valor': 499.00, 'duracao': 6}
}

# --- FUNÇÕES DE VALIDAÇÃO ---
def validar_matricula(P):
    if len(P) > 6: return False
    if str.isdigit(P) or P == "": return True
    return False

def validar_cpf_input(P):
    if len(P) > 11: return False
    if str.isdigit(P) or P == "": return True
    return False

def validar_cpf_algoritmo(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    try:
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        if digito1 != int(cpf[9]): return False
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        if digito2 != int(cpf[10]): return False
    except ValueError: return False
    return True

# --- FUNÇÃO PARA FORMATAR A DATA ---
def formatar_data(event):
    texto_atual = entry_data_inicio.get()
    numeros = "".join(filter(str.isdigit, texto_atual))
    data_formatada = ""
    if len(numeros) > 0: data_formatada = numeros[:2]
    if len(numeros) > 2: data_formatada += "/" + numeros[2:4]
    if len(numeros) > 4: data_formatada += "/" + numeros[4:8]
    entry_data_inicio.delete(0, tk.END)
    entry_data_inicio.insert(0, data_formatada)
    entry_data_inicio.icursor(tk.END)

# --- LÓGICA DE CÁLCULO ATUALIZADA ---
def logica_de_calculo(data_inicio, tipo_plano_str, parcelas_em_atraso_str, pagamento_hoje_confirmado=None):
    try:
        dados_retorno = {}
        if data_inicio < date(2024, 10, 1):
            return {'erro_data': "A academia foi inaugurada em Outubro de 2024. A data de início do contrato não pode ser anterior a isso."}
        parcelas_em_atraso = int(parcelas_em_atraso_str)
        plano_selecionado = PLANOS[tipo_plano_str]
        valor_mensalidade = plano_selecionado['valor']
        duracao_plano = plano_selecionado['duracao']
        data_hoje = date.today()
        valor_atrasado = parcelas_em_atraso * valor_mensalidade
        meses_decorridos = 0
        vencimento_iterador = data_inicio
        while vencimento_iterador <= data_hoje:
            meses_decorridos += 1
            vencimento_iterador += relativedelta(months=1)
        proximo_vencimento = vencimento_iterador
        meses_restantes_base = duracao_plano - meses_decorridos
        valor_mensalidade_adicional = 0.0
        meses_a_pagar_adiantado = 0
        data_acesso_final = proximo_vencimento + relativedelta(days=-1)
        dias_para_vencimento = (proximo_vencimento - data_hoje).days
        linha_mensalidade_adicional = "Não se aplica"
        if pagamento_hoje_confirmado == False:
            valor_mensalidade_adicional = valor_mensalidade
            meses_a_pagar_adiantado = 1
            data_acesso_final = data_hoje + relativedelta(months=1, days=-1)
            linha_mensalidade_adicional = f"R$ {valor_mensalidade_adicional:.2f} (referente a hoje - {data_hoje.strftime('%d/%m/%Y')})"
        elif 0 < dias_para_vencimento <= 30:
            valor_mensalidade_adicional = valor_mensalidade
            meses_a_pagar_adiantado = 1
            data_acesso_final = proximo_vencimento + relativedelta(months=1, days=-1)
            linha_mensalidade_adicional = f"R$ {valor_mensalidade_adicional:.2f} (em {dias_para_vencimento} dias - {proximo_vencimento.strftime('%d/%m/%Y')})"
        meses_para_multa = max(0, meses_restantes_base - meses_a_pagar_adiantado)
        valor_multa = (meses_para_multa * valor_mensalidade) * 0.10
        total_a_pagar = valor_atrasado + valor_mensalidade_adicional + valor_multa
        dados_retorno.update({'data_simulacao': data_hoje, 'plano': tipo_plano_str, 'valor_plano': valor_mensalidade, 'data_inicio_contrato': data_inicio, 'parcelas_atrasadas_qtd': parcelas_em_atraso, 'valor_atrasado': valor_atrasado, 'linha_mensalidade_a_vencer': linha_mensalidade_adicional, 'meses_para_multa': meses_para_multa, 'valor_multa': valor_multa, 'total_a_pagar': total_a_pagar, 'data_acesso_final': data_acesso_final, 'valor_proxima_parcela': valor_mensalidade_adicional, 'vencimento_proxima': proximo_vencimento.strftime('%d/%m/%Y') if valor_mensalidade_adicional > 0 else "Não se aplica"})
        return dados_retorno
    except Exception as e:
        return {'erro_geral': f"Erro nos dados de entrada. Verifique a data e os números.\nDetalhe: {e}"}

# --- FUNÇÕES DA INTERFACE GRÁFICA ---
def executar_calculo():
    global calculo_resultado
    data_inicio_str = entry_data_inicio.get(); tipo_plano = combo_plano.get(); parcelas_atrasadas = entry_parcelas_atraso.get()
    if not data_inicio_str or not tipo_plano or not parcelas_atrasadas: messagebox.showerror("Erro", "Por favor, preencha todos os campos do cálculo."); return
    try:
        dia, mes, ano = map(int, data_inicio_str.split('/')); data_inicio = date(ano, mes, dia)
    except Exception:
        messagebox.showerror("Erro", "Formato de data inválido."); return
    def processar_calculo(pagamento_hoje_status=None):
        global calculo_resultado
        calculo_resultado = logica_de_calculo(data_inicio, tipo_plano, parcelas_atrasadas, pagamento_hoje_status)
        for widget in frame_resultado.winfo_children(): widget.destroy()
        if 'erro_data' in calculo_resultado: messagebox.showerror("Data Inválida", calculo_resultado['erro_data']); frame_whatsapp.pack_forget(); return
        elif 'erro_geral' in calculo_resultado: messagebox.showerror("Erro", calculo_resultado['erro_geral']); frame_whatsapp.pack_forget(); return
        font_normal = ("Arial", 9); font_bold = ("Arial", 10, "bold")
        tk.Label(frame_resultado, text=f"Data da Simulação: {calculo_resultado['data_simulacao'].strftime('%d/%m/%Y')}", font=font_normal, anchor='w').pack(fill='x')
        tk.Label(frame_resultado, text=f"Plano: {calculo_resultado['plano']} (R$ {calculo_resultado['valor_plano']:.2f})", font=font_normal, anchor='w').pack(fill='x')
        tk.Label(frame_resultado, text=f"Início do Contrato: {calculo_resultado['data_inicio_contrato'].strftime('%d/%m/%Y')}", font=font_normal, anchor='w').pack(fill='x')
        tk.Label(frame_resultado, text="-"*60, font=font_normal).pack(fill='x', pady=2)
        tk.Label(frame_resultado, text=f"Valor por parcelas em atraso ({calculo_resultado['parcelas_atrasadas_qtd']}x): R$ {calculo_resultado['valor_atrasado']:.2f}", font=font_bold, anchor='w').pack(fill='x')
        tk.Label(frame_resultado, text=f"Mensalidade a vencer: {calculo_resultado['linha_mensalidade_a_vencer']}", font=font_bold, anchor='w').pack(fill='x')
        tk.Label(frame_resultado, text=f"Multa contratual (10% sobre {calculo_resultado['meses_para_multa']} meses): R$ {calculo_resultado['valor_multa']:.2f}", font=font_bold, anchor='w').pack(fill='x')
        tk.Label(frame_resultado, text="-"*60, font=font_normal).pack(fill='x', pady=2)
        tk.Label(frame_resultado, text=f"TOTAL A SER PAGO: R$ {calculo_resultado['total_a_pagar']:.2f}", font=font_bold, anchor='w').pack(fill='x')
        tk.Label(frame_resultado, text="-"*60, font=font_normal).pack(fill='x', pady=2)
        tk.Label(frame_resultado, text=f"O acesso à academia será encerrado em: {calculo_resultado['data_acesso_final'].strftime('%d/%m/%Y')}", font=font_normal, anchor='w').pack(fill='x')
        if 'total_a_pagar' in calculo_resultado: frame_whatsapp.pack(pady=10, padx=10, fill="x")
        else: frame_whatsapp.pack_forget()
    if date.today().day == data_inicio.day:
        resposta = messagebox.askyesno("Verificação de Pagamento", "A parcela de hoje já foi debitada do cartão do cliente?")
        processar_calculo(resposta)
    else:
        processar_calculo()

def limpar_campos():
    global calculo_resultado
    entry_data_inicio.delete(0, tk.END); entry_parcelas_atraso.delete(0, tk.END); combo_plano.set('Anual (12 meses)')
    for widget in frame_resultado.winfo_children(): widget.destroy()
    tk.Label(frame_resultado, text="O resultado aparecerá aqui...", anchor="nw", justify=tk.LEFT, wraplength=400).pack(fill="both", expand=True)
    entry_data_inicio.focus_set()
    entry_matricula.delete(0, tk.END); entry_nome_cliente.delete(0, tk.END); entry_motivo.delete(0, tk.END)
    calculo_resultado = {}; frame_whatsapp.pack_forget()

def copiar_texto_gerencia():
    global consultor_selecionado
    if 'total_a_pagar' not in calculo_resultado: messagebox.showerror("Erro", "Execute um cálculo válido primeiro."); return
    matricula = entry_matricula.get(); nome_cliente = entry_nome_cliente.get(); motivo = entry_motivo.get()
    if not matricula or not nome_cliente or not motivo: messagebox.showerror("Erro", "Preencha todos os campos da mensagem."); return
    data_acesso_str = calculo_resultado['data_acesso_final'].strftime('%d/%m/%Y')
    texto_formatado = (f"*CANCELAMENTO*\n\nMatrícula: {matricula}\nNome: {nome_cliente}\n\nMotivo: {motivo}\nAcesso até: {data_acesso_str}\n\n> {consultor_selecionado}")
    app.clipboard_clear(); app.clipboard_append(texto_formatado)

def copiar_texto_cliente():
    if 'total_a_pagar' not in calculo_resultado: messagebox.showerror("Erro", "Execute um cálculo válido primeiro."); return
    matricula = entry_matricula.get(); nome_cliente = entry_nome_cliente.get()
    if not matricula or not nome_cliente: messagebox.showerror("Erro", "Preencha a Matrícula e o Nome do Cliente."); return
    linha_proxima_parcela = ""
    if calculo_resultado['valor_proxima_parcela'] > 0: linha_proxima_parcela = (f"- Próxima parcela: R$ {calculo_resultado['valor_proxima_parcela']:.2f} (dia {calculo_resultado['vencimento_proxima']})\n")
    texto_formatado = (f"*INFORMAÇÕES CANCELAMENTO*\n\n- Nome: {nome_cliente}\n- Matricula: {matricula}\n\n*💸 VALORES*\n- Parcelas vencidas: R$ {calculo_resultado['valor_atrasado']:.2f} ({calculo_resultado['parcelas_atrasadas_qtd']} Parcelas)\n{linha_proxima_parcela}- Valor da multa: R$ {calculo_resultado['valor_multa']:.2f} (10% de {calculo_resultado['meses_para_multa']} Meses)\n> TOTAL A SER PAGO: *R$ {calculo_resultado['total_a_pagar']:.2f}*\n\nApós o cancelamento, *seu acesso permanecerá ativo até*: {calculo_resultado['data_acesso_final'].strftime('%d/%m/%Y')}")
    app.clipboard_clear(); app.clipboard_append(texto_formatado)

def gerar_documento_popup():
    if 'total_a_pagar' not in calculo_resultado: messagebox.showerror("Erro", "Execute um cálculo válido primeiro."); return
    nome_cliente = entry_nome_cliente.get(); matricula = entry_matricula.get()
    if not nome_cliente or not matricula: messagebox.showerror("Erro", "Preencha Nome e Matrícula para gerar o documento."); return
    
    popup = tk.Toplevel(app); popup.title("Informação Adicional"); popup.geometry("300x150"); popup.resizable(False, False)
    tk.Label(popup, text="Digite o CPF do Cliente:", font=("Arial", 10)).pack(pady=10)
    vcmd_cpf = (popup.register(validar_cpf_input), '%P')
    entry_cpf_popup = tk.Entry(popup, width=30, validate="key", validatecommand=vcmd_cpf); entry_cpf_popup.pack(pady=5); entry_cpf_popup.focus_set()

    def finalizar_geracao():
        cpf_cliente = entry_cpf_popup.get()
        if not validar_cpf_algoritmo(cpf_cliente): messagebox.showerror("CPF Inválido", "O CPF digitado não é válido.", parent=popup); return
        popup.destroy()
        try:
            if getattr(sys, 'frozen', False): base_path = sys._MEIPASS
            else: base_path = os.path.dirname(__file__)
            modelo_path = os.path.join(base_path, "modelo_final.docx")
            doc = Document(modelo_path)
            
            # --- INÍCIO DA CORREÇÃO ---
            # Limpa o nome do cliente para que seja um nome de arquivo válido
            caracteres_invalidos = '<>:"/\\|?*\n\r\t'
            nome_cliente_para_arquivo = nome_cliente
            for char in caracteres_invalidos:
                nome_cliente_para_arquivo = nome_cliente_para_arquivo.replace(char, ' ').strip()
            # --- FIM DA CORREÇÃO ---

            substituicoes = {"NOME_CLIENTE": nome_cliente.upper(), "CPF_CLIENTE": cpf_cliente, "MATRICULA_CLIENTE": matricula, "DATA_INICIO_CONTRATO": calculo_resultado['data_inicio_contrato'].strftime('%d/%m/%Y'), "VALOR_TOTAL": f"R$ {calculo_resultado['valor_multa']:.2f}", "DATA_SOLICITACAO": calculo_resultado['data_simulacao'].strftime('%d/%m/%Y'), "NOME_CONSULTOR": consultor_selecionado.upper()}
            for p in doc.paragraphs:
                for run in p.runs:
                    for key, value in substituicoes.items():
                        if key in run.text: run.text = run.text.replace(key, value)
            
            pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
            # Usa o nome limpo para criar o arquivo
            nome_arquivo_base = f"Cancelamento - {nome_cliente_para_arquivo}"
            caminho_saida_docx = os.path.join(pasta_downloads, f"{nome_arquivo_base}.docx")
            caminho_saida_pdf = os.path.join(pasta_downloads, f"{nome_arquivo_base}.pdf")
            doc.save(caminho_saida_docx)
            convert(caminho_saida_docx, caminho_saida_pdf)
            os.remove(caminho_saida_docx)
            messagebox.showinfo("Sucesso", f"Documento PDF gerado com sucesso!\nSalvo em: {caminho_saida_pdf}")
        except FileNotFoundError: messagebox.showerror("Erro Crítico", "O arquivo 'modelo_final.docx' não foi encontrado.")
        except Exception as e: messagebox.showerror("Erro ao Gerar Documento", f"Ocorreu um erro inesperado:\n{e}")
    
    botao_confirmar = tk.Button(popup, text="Confirmar e Gerar PDF", command=finalizar_geracao, font=("Arial", 10, "bold"), bg="#4CAF50", fg="white")
    botao_confirmar.pack(pady=10)

def mostrar_calculadora():
    global consultor_selecionado
    consultor_selecionado = combo_consultor_login.get()
    if not consultor_selecionado: messagebox.showwarning("Atenção", "Por favor, selecione um consultor para continuar."); return
    login_frame.pack_forget(); calculator_frame.pack()

# --- CRIAÇÃO DA JANELA PRINCIPAL ---
app = tk.Tk()
app.title("SIMULAÇÃO DE CANCELAMENTO IRONBERG")
app.geometry("450x850")
app.resizable(False, False)

# --- TELA DE LOGIN ---
login_frame = tk.Frame(app, padx=20, pady=20)
tk.Label(login_frame, text="Selecione o Consultor", font=("Arial", 14, "bold")).pack(pady=10)
combo_consultor_login = ttk.Combobox(login_frame, values=CONSULTORES, width=30, font=("Arial", 12), state="readonly")
combo_consultor_login.pack(pady=10)
botao_entrar = tk.Button(login_frame, text="Entrar", command=mostrar_calculadora, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", width=20)
botao_entrar.pack(pady=20)

# --- TELA DA CALCULADORA ---
calculator_frame = tk.Frame(app)
frame_entrada = tk.Frame(calculator_frame, padx=10, pady=10); frame_entrada.pack(padx=10, pady=5, fill="x")
tk.Label(frame_entrada, text="Data de Início (dd/mm/aaaa):").grid(row=0, column=0, sticky="w", pady=2)
entry_data_inicio = tk.Entry(frame_entrada, width=25); entry_data_inicio.grid(row=0, column=1, sticky="w", pady=2)
entry_data_inicio.bind("<KeyRelease>", formatar_data)
tk.Label(frame_entrada, text="Tipo de Plano:").grid(row=1, column=0, sticky="w", pady=2)
combo_plano = ttk.Combobox(frame_entrada, values=list(PLANOS.keys()), width=22, state="readonly"); combo_plano.grid(row=1, column=1, sticky="w", pady=2)
combo_plano.set('Anual (12 meses)')
tk.Label(frame_entrada, text="Mensalidades em Atraso:").grid(row=2, column=0, sticky="w", pady=2)
entry_parcelas_atraso = tk.Entry(frame_entrada, width=25); entry_parcelas_atraso.grid(row=2, column=1, sticky="w", pady=2)
frame_botoes = tk.Frame(calculator_frame); frame_botoes.pack(pady=5, padx=20, fill="x")
botao_calcular = tk.Button(frame_botoes, text="Calcular", command=executar_calculo, font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", width=18)
botao_calcular.pack(side="left", expand=True)
botao_limpar = tk.Button(frame_botoes, text="Nova Simulação", command=limpar_campos, font=("Arial", 10, "bold"), bg="#f44336", fg="white", width=18)
botao_limpar.pack(side="right", expand=True)
frame_resultado = tk.Frame(calculator_frame, padx=10, pady=10, relief="sunken", borderwidth=1); frame_resultado.pack(pady=5, padx=10, fill="both", expand=True)
tk.Label(frame_resultado, text="O resultado aparecerá aqui...", anchor="nw", justify=tk.LEFT, wraplength=400).pack(fill="both", expand=True)

# --- SEÇÃO DE AÇÕES FINAIS ---
frame_whatsapp = ttk.LabelFrame(calculator_frame, text=" Ações Finais ", padding=(10, 5))
vcmd_matricula = (app.register(validar_matricula), '%P')
tk.Label(frame_whatsapp, text="Matrícula:").grid(row=0, column=0, sticky="w", pady=2)
entry_matricula = tk.Entry(frame_whatsapp, width=30, validate="key", validatecommand=vcmd_matricula); entry_matricula.grid(row=0, column=1, columnspan=2, sticky="w", pady=2)
tk.Label(frame_whatsapp, text="Nome do Cliente:").grid(row=1, column=0, sticky="w", pady=2)
entry_nome_cliente = tk.Entry(frame_whatsapp, width=30); entry_nome_cliente.grid(row=1, column=1, columnspan=2, sticky="w", pady=2)
tk.Label(frame_whatsapp, text="Motivo:").grid(row=3, column=0, sticky="w", pady=2)
entry_motivo = tk.Entry(frame_whatsapp, width=30); entry_motivo.grid(row=3, column=1, columnspan=2, sticky="w", pady=2)
frame_botoes_copiar = tk.Frame(frame_whatsapp); frame_botoes_copiar.grid(row=5, column=0, columnspan=3, pady=10)
botao_copiar_gerencia = tk.Button(frame_botoes_copiar, text="Copiar (Pendências)", command=copiar_texto_gerencia, font=("Arial", 10, "bold"), bg="#25D366", fg="white", width=22)
botao_copiar_gerencia.pack(side="left", padx=5)
botao_copiar_cliente = tk.Button(frame_botoes_copiar, text="Copiar Detalhes", command=copiar_texto_cliente, font=("Arial", 10, "bold"), bg="#007bff", fg="white", width=22)
botao_copiar_cliente.pack(side="right", padx=5)
botao_gerar_docx = tk.Button(frame_whatsapp, text="Gerar Documento PDF", command=gerar_documento_popup, font=("Arial", 10, "bold"), bg="#c0392b", fg="white", width=46)
botao_gerar_docx.grid(row=6, column=0, columnspan=3, pady=(5,0))

# --- INICIA A APLICAÇÃO ---
login_frame.pack(pady=100)
app.mainloop()