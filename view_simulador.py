# -*- coding: utf-8 -*-

"""
Arquivo: view_simulador.py
Descrição: Contém a classe SimuladorView, que constrói e gerencia
a tela do Simulador de Cancelamento.
(v5.6.10 - Regra de negócio para perguntar o valor APENAS em Junho)
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, StringVar, scrolledtext
# --- NOVA IMPORTAÇÃO ---
from tkinter import ttk as standard_ttk 
from datetime import date
import requests
import random

# --- Importa as funções de utilidade ---
from app_utils import (
    PLANOS, MOTIVOS_CANCELAMENTO, validar_matricula, 
    validar_e_formatar_cpf_input, limpar_cpf, validar_cpf_algoritmo, 
    formatar_data, logica_de_calculo
)

class SimuladorView:
    
    def __init__(self, app, main_frame):
        """
        Constrói a tela do Simulador.
        'app' é a referência à classe principal (App)
        'main_frame' é o frame onde esta tela será desenhada
        """
        self.app = app  # Referência ao app principal
        self.main_frame = main_frame
        
        # Variável para guardar o resultado do cálculo
        self.calculo_resultado = {}
        
        # Variável para o resultado do popup customizado
        self.popup_plano_valor = None 

        # --- Início: Código de create_cancellation_view ---
        
        ttk.Label(self.main_frame, text="Simulador de Cancelamento", font=self.app.FONT_TITLE).pack(pady=(0, 10), anchor='w')

        frame_form = ttk.Frame(self.main_frame)
        frame_form.pack(padx=0, pady=5, fill="x", anchor='w')

        ttk.Label(frame_form, text="Data de Início (dd/mm/aaaa):", width=25, anchor='w').grid(row=0, column=0, sticky="w", pady=5)
        self.entry_data_inicio = ttk.Entry(frame_form, width=30)
        self.entry_data_inicio.grid(row=0, column=1, sticky="w", pady=5)
        self.entry_data_inicio.bind("<KeyRelease>", lambda e: formatar_data(e, self.entry_data_inicio))

        ttk.Label(frame_form, text="Tipo de Plano:", width=25, anchor='w').grid(row=1, column=0, sticky="w", pady=5)
        self.combo_plano = ttk.Combobox(frame_form, values=list(PLANOS.keys()), width=27, state="readonly")
        self.combo_plano.grid(row=1, column=1, sticky="w", pady=5)
        self.combo_plano.set('Anual (12 meses)')

        ttk.Label(frame_form, text="Mensalidades em Atraso:", width=25, anchor='w').grid(row=2, column=0, sticky="w", pady=5)
        self.entry_parcelas_atraso = ttk.Entry(frame_form, width=30)
        self.entry_parcelas_atraso.grid(row=2, column=1, sticky="w", pady=5)

        frame_botoes = ttk.Frame(frame_form)
        frame_botoes.grid(row=3, column=0, columnspan=2, sticky='w', pady=10)

        # Comandos agora chamam métodos desta classe
        ttk.Button(frame_botoes, text="Calcular", command=self.do_calculation, style='success.TButton', width=20).pack(side="left", expand=False, padx=(0, 5), ipady=5)
        ttk.Button(frame_botoes, text="Nova Simulação", command=self.clear_fields, style='danger.TButton', width=20).pack(side="left", expand=False, padx=5, ipady=5)

        self.frame_resultado = ttk.Frame(self.main_frame, padding=(20, 15), relief="solid", borderwidth=1)
        self.frame_resultado.pack(pady=5, padx=10, fill="both", expand=True, anchor='w')

        self.placeholder_label = ttk.Label(self.frame_resultado, text="O resultado aparecerá aqui...", font=self.app.FONT_MAIN, style="secondary.TLabel")
        self.placeholder_label.pack(expand=True)

        self.frame_whatsapp = standard_ttk.LabelFrame(self.frame_resultado, text=" Ações Finais ", padding=(15, 10))

        vcmd_matricula = (self.app.register(validar_matricula), '%P')
        ttk.Label(self.frame_whatsapp, text="Matrícula:").grid(row=0, column=1, sticky="w", pady=4)

        self.entry_matricula = ttk.Entry(self.frame_whatsapp, width=35, validate="key",
                                         validatecommand=vcmd_matricula)
        self.entry_matricula.grid(row=0, column=2, sticky="w", pady=4)

        ttk.Label(self.frame_whatsapp, text="Nome do Cliente:").grid(row=1, column=1, sticky="w", pady=4)
        self.entry_nome_cliente = ttk.Entry(self.frame_whatsapp, width=35)
        self.entry_nome_cliente.grid(row=1, column=2, sticky="w", pady=4)

        frame_botoes_copiar = ttk.Frame(self.frame_whatsapp)
        frame_botoes_copiar.grid(row=2, column=1, columnspan=2, pady=15)

        ttk.Button(frame_botoes_copiar, text="Copiar (Pendências)", style='success.Outline.TButton', command=self.copiar_texto_gerencia).pack(side="left", padx=5)
        ttk.Button(frame_botoes_copiar, text="Copiar Detalhes", style='info.Outline.TButton', command=self.copiar_texto_cliente).pack(side="right", padx=5)

        ttk.Button(self.frame_whatsapp, text="Gerar Link de Assinatura", style='danger.TButton', command=self.gerar_documento_popup).grid(row=3, column=1, columnspan=2, pady=(5,0), sticky='ew')

        self.frame_whatsapp.columnconfigure(0, weight=1)
        self.frame_whatsapp.columnconfigure(3, weight=1)

        # --- Fim: Código de create_cancellation_view ---

    # --- NOVO POPUP CUSTOMIZADO ---
    def _ask_plan_value_popup(self):
        """Mostra um popup customizado para perguntar o valor do plano."""
        self.popup_plano_valor = None # Reseta o valor
        
        popup = Toplevel(self.app)
        popup.title("Verificação de Contrato")
        
        # Centraliza o popup
        self.app._center_popup(popup, 450, 220) # (popup, largura, altura)
        
        container = ttk.Frame(popup, padding=20)
        container.pack(fill='both', expand=True)
        
        # Mensagem
        msg = "Este contrato (iniciado em Junho/2025) é no valor novo ou antigo?"
        ttk.Label(container, text=msg, font=self.app.FONT_BOLD, wraplength=400, justify='center').pack(pady=(0, 15))
        
        ttk.Label(container, text="Selecione o valor correto do plano Anual:", font=self.app.FONT_MAIN).pack(pady=(0, 20))

        # Frame dos botões
        frame_botoes = ttk.Frame(container)
        frame_botoes.pack(fill='x', expand=True)
        
        # Preenche o espaço entre os botões
        frame_botoes.grid_columnconfigure(0, weight=1)
        frame_botoes.grid_columnconfigure(1, weight=1)

        def on_select(valor):
            self.popup_plano_valor = valor
            popup.destroy()

        # Botão 1
        btn_359 = ttk.Button(
            frame_botoes, 
            text="R$ 359,00 (Antigo)", 
            command=lambda: on_select(359.00),
            style="secondary.TButton",
            width=20
        )
        btn_359.grid(row=0, column=0, padx=10, ipady=10)

        # Botão 2
        btn_389 = ttk.Button(
            frame_botoes, 
            text="R$ 389,00 (Novo)", 
            command=lambda: on_select(389.00),
            style="success.TButton",
            width=20
        )
        btn_389.grid(row=0, column=1, padx=10, ipady=10)
        
        # Foca no botão novo por padrão
        btn_389.focus_set()
        
        # Garante que o usuário não pode fechar pelo 'X' sem uma resposta
        def on_close():
            self.popup_plano_valor = None # Aborta o cálculo
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_close)
        
        # Espera o usuário responder
        self.app.wait_window(popup)

    def _popup_data_invalida_inauguracao(self, data_inicio):
        """Popup moderno para data anterior à inauguração (out/2024), sem depender de API."""
        popup = Toplevel(self.app)
        # Remove barra de título (sem X) e força fechamento pelo botão
        self.app._center_popup(popup, 640, 310)
        popup.overrideredirect(True)

        container = ttk.Frame(popup, padding=18, relief='solid', borderwidth=1)
        container.pack(fill='both', expand=True)

        # Cabeçalho para arrastar o popup
        header = ttk.Frame(container)
        header.pack(fill='x', pady=(0, 8))
        header_lbl = ttk.Label(header, text="Data impossível", style='secondary.TLabel', font=("Segoe UI", 9))
        header_lbl.pack(anchor='w')

        drag_state = {'x': 0, 'y': 0}

        def _start_drag(evt):
            drag_state['x'] = evt.x_root
            drag_state['y'] = evt.y_root

        def _on_drag(evt):
            try:
                dx = evt.x_root - drag_state['x']
                dy = evt.y_root - drag_state['y']
                x = popup.winfo_x() + dx
                y = popup.winfo_y() + dy
                popup.geometry(f"+{x}+{y}")
                drag_state['x'] = evt.x_root
                drag_state['y'] = evt.y_root
            except Exception:
                pass

        header.bind('<ButtonPress-1>', _start_drag)
        header.bind('<B1-Motion>', _on_drag)
        header_lbl.bind('<ButtonPress-1>', _start_drag)
        header_lbl.bind('<B1-Motion>', _on_drag)

        area = ttk.Frame(container)
        area.pack(fill='both', expand=True)

        left = ttk.Frame(area)
        left.pack(side='left', fill='y', padx=(0, 18))

        right = ttk.Frame(area)
        right.pack(side='left', fill='both', expand=True)

        ttk.Label(
            right,
            text="Ops… essa data não tem como",
            font=self.app.FONT_BOLD,
            style='danger.TLabel'
        ).pack(anchor='w')

        msg = (
            f"A academia inaugurou em outubro de 2024.\n"
            f"Então um contrato começando em {data_inicio.strftime('%d/%m/%Y')} é impossível.\n\n"
            f"Digite outubro de 2024 (ou qualquer data a partir daí)."
        )

        ttk.Label(
            right,
            text=msg,
            font=self.app.FONT_MAIN,
            wraplength=430,
            justify='left'
        ).pack(anchor='w', pady=(10, 0))

        # Mascote animado (tipo GIF), desenhado localmente e rodando sozinho
        img_label = ttk.Label(left)
        img_label.pack(pady=(6, 4))

        try:
            from PIL import Image, ImageDraw, ImageTk

            def desenhar_frame(idx: int):
                img = Image.new('RGBA', (112, 112), (0, 0, 0, 0))
                d = ImageDraw.Draw(img)

                # Paleta "nervosa"
                face = (235, 90, 90, 255)
                outline = (120, 30, 30, 255)
                white = (255, 255, 255, 255)
                black = (25, 25, 25, 255)

                # Pequena tremida
                shake = [-2, -1, 0, 1, 2, 1][idx % 6]

                # Cabeça
                d.ellipse((6 + shake, 6, 106 + shake, 106), fill=face, outline=outline, width=4)

                # Olhos
                d.ellipse((30 + shake, 46, 50 + shake, 66), fill=white, outline=outline, width=2)
                d.ellipse((62 + shake, 46, 82 + shake, 66), fill=white, outline=outline, width=2)
                d.ellipse((38 + shake, 54, 44 + shake, 60), fill=black)
                d.ellipse((70 + shake, 54, 76 + shake, 60), fill=black)

                # Sobrancelha brava (mudando um pouco)
                brow = [0, 1, 2, 1, 0, -1][idx % 6]
                d.line((28 + shake, 42 + brow, 52 + shake, 48 + brow), fill=outline, width=5)
                d.line((84 + shake, 42 + brow, 60 + shake, 48 + brow), fill=outline, width=5)

                # Boca emburrada
                d.arc((36 + shake, 74, 76 + shake, 104), start=210, end=330, fill=outline, width=4)

                # "Vapor" saindo (alternando lado)
                steam_dx = [0, 2, 4, 2, 0, -2][idx % 6]
                d.arc((12 + steam_dx, 12, 40 + steam_dx, 40), start=240, end=40, fill=outline, width=3)
                d.arc((78 - steam_dx, 12, 106 - steam_dx, 40), start=140, end=300, fill=outline, width=3)

                return ImageTk.PhotoImage(img)

            self._mascote_inaug_anim = [desenhar_frame(i) for i in range(6)]
            self._mascote_inaug_anim_idx = 0

            def tick():
                try:
                    if not popup.winfo_exists():
                        return
                    img_label.config(image=self._mascote_inaug_anim[self._mascote_inaug_anim_idx])
                    self._mascote_inaug_anim_idx = (self._mascote_inaug_anim_idx + 1) % len(self._mascote_inaug_anim)
                    popup.after(180, tick)
                except Exception:
                    pass

            tick()
        except Exception:
            img_label.config(text="(mascote nervoso)")

        ttk.Separator(container).pack(fill='x', pady=12)
        frame_btn = ttk.Frame(container)
        frame_btn.pack(fill='x')

        def focar_data():
            try:
                self.entry_data_inicio.focus_set()
                self.entry_data_inicio.selection_range(0, 'end')
            except Exception:
                pass

        def ok():
            popup.destroy()
            focar_data()

        btn_ok = ttk.Button(
            frame_btn,
            text="Beleza, vou corrigir a merda que eu fiz",
            command=ok,
            style='success.TButton',
            width=38
        )
        btn_ok.pack(pady=(4, 0), ipady=10)
        btn_ok.focus_set()

        # Não permite fechar por teclas/"X" (não existe X por overrideredirect)
        popup.protocol("WM_DELETE_WINDOW", lambda: None)
        popup.bind("<Escape>", lambda e: None)
        popup.bind("<Alt-F4>", lambda e: None)
        popup.bind("<Return>", lambda e: ok())
        popup.transient(self.app)
        popup.grab_set()
        self.app.wait_window(popup)

    def do_calculation(self):
        """Função de cálculo (ATUALIZADA)."""
        data_inicio_str = self.entry_data_inicio.get()
        try:
            dia, mes, ano = map(int, data_inicio_str.split('/'))
            data_inicio = date(ano, mes, dia)
        except Exception:
            messagebox.showerror("Erro", "Formato de data inválido. Use dd/mm/aaaa.")
            return

        tipo_plano = self.combo_plano.get()
        parcelas_atrasadas_str = self.entry_parcelas_atraso.get() or "0"
        if not data_inicio_str or not tipo_plano:
            messagebox.showerror("Erro", "Preencha a Data de Início e o Tipo de Plano.")
            return

        data_simulacao_hoje = date.today()
        if data_inicio > data_simulacao_hoje:
            messagebox.showerror("Data Inválida", "A Data de Início do contrato não pode ser uma data no futuro.")
            return

        # --- ***** INÍCIO DA NOVA LÓGICA DE PREÇO (v5.6.10) ***** ---
        
        # Datas de referência
        DATA_INICIO_PERGUNTA = date(2025, 6, 1) # 1º de Junho de 2025
        DATA_FIM_PERGUNTA = date(2025, 6, 30)    # 30 de Junho de 2025
        DATA_PRECO_NOVO_AUTO = date(2025, 7, 1) # 1º de Julho de 2025
        
        valor_override = None # Nenhum valor especial por padrão

        # 1. Verifica se é o plano Anual
        if tipo_plano == 'Anual (12 meses)':
            
            # 2. Se a data de início for EM JUNHO 2025 (o mês da virada), PERGUNTA.
            if DATA_INICIO_PERGUNTA <= data_inicio <= DATA_FIM_PERGUNTA:
                
                # 2a. CHAMA O POPUP CUSTOMIZADO
                self._ask_plan_value_popup()
                
                # 2b. Verifica a resposta
                if self.popup_plano_valor is None:
                    # Usuário fechou o popup (clicou no 'X'), cancela o cálculo
                    messagebox.showwarning("Cálculo Cancelado", "Você deve selecionar um valor de plano para continuar.")
                    return 
                
                valor_override = self.popup_plano_valor # Recebe 359.00 ou 389.00
            
            # 3. Se a data de início for A PARTIR DE JULHO 2025, usa 389 direto.
            elif data_inicio >= DATA_PRECO_NOVO_AUTO:
                valor_override = 389.00
            
            # 4. (Implícito) Se for antes de Junho 2025, valor_override continua None,
            #    e a 'logica_de_calculo' usará o valor base (359).
            
        # --- ***** FIM DA NOVA LÓGICA DE PREÇO ***** ---


        def processar_calculo(pagamento_hoje_status=None):
            
            # --- Prepara o parâmetro para a lógica ---
            kwargs = {}
            if valor_override is not None:
                kwargs['valor_mensalidade_override'] = valor_override

            # 3. Chama a lógica com o parâmetro extra
            self.calculo_resultado = logica_de_calculo(
                data_inicio, 
                tipo_plano, 
                parcelas_atrasadas_str, 
                pagamento_hoje_status,
                **kwargs  # <--- Passa o valor_override para a função
            )

            for widget in self.frame_resultado.winfo_children():
                if widget != self.frame_whatsapp:
                    widget.destroy()

            if 'erro_data' in self.calculo_resultado:
                erro = str(self.calculo_resultado.get('erro_data', ''))
                if 'outubro de 2024' in erro.lower():
                    self._popup_data_invalida_inauguracao(data_inicio)
                else:
                    messagebox.showerror("Data Inválida", erro)
                ttk.Label(self.frame_resultado, text="O resultado aparecerá aqui...", font=self.app.FONT_MAIN, style="secondary.TLabel").pack(expand=True)
                self.frame_whatsapp.pack_forget()
                return
            elif 'erro_geral' in self.calculo_resultado:
                messagebox.showerror("Erro", self.calculo_resultado['erro_geral'])
                ttk.Label(self.frame_resultado, text="O resultado aparecerá aqui...").pack(expand=True)
                self.frame_whatsapp.pack_forget()
                return

            # O 'valor_plano' agora virá como 389 ou 359, baseado na lógica
            ttk.Label(self.frame_resultado, text=f"Data da Simulação: {self.calculo_resultado['data_simulacao'].strftime('%d/%m/%Y')}").pack(fill='x', anchor='w')
            ttk.Label(self.frame_resultado, text=f"Plano: {self.calculo_resultado['plano']} (R$ {self.calculo_resultado['valor_plano']:.2f})").pack(fill='x', anchor='w')
            ttk.Label(self.frame_resultado, text=f"Início do Contrato: {self.calculo_resultado['data_inicio_contrato'].strftime('%d/%m/%Y')}").pack(fill='x', anchor='w')
            ttk.Separator(self.frame_resultado).pack(fill='x', pady=5)
            ttk.Label(self.frame_resultado, text=f"Valor por parcelas em atraso ({self.calculo_resultado['parcelas_atrasadas_qtd']}x): R$ {self.calculo_resultado['valor_atrasado']:.2f}", font=self.app.FONT_BOLD).pack(fill='x', anchor='w')
            ttk.Label(self.frame_resultado, text=f"Mensalidade a vencer: {self.calculo_resultado['linha_mensalidade_a_vencer']}", font=self.app.FONT_BOLD).pack(fill='x', anchor='w')
            # A multa aqui será calculada em cima dos 359, como pedido
            ttk.Label(self.frame_resultado, text=f"Multa contratual (10% sobre {self.calculo_resultado['meses_para_multa']} meses): R$ {self.calculo_resultado['valor_multa']:.2f}", font=self.app.FONT_BOLD).pack(fill='x', anchor='w')
            ttk.Separator(self.frame_resultado).pack(fill='x', pady=5)
            ttk.Label(self.frame_resultado, text=f"TOTAL A SER PAGO: R$ {self.calculo_resultado['total_a_pagar']:.2f}", font=self.app.FONT_BOLD).pack(fill='x', anchor='w')
            ttk.Separator(self.frame_resultado).pack(fill='x', pady=5)
            ttk.Label(self.frame_resultado, text=f"O acesso à academia será encerrado em: {self.calculo_resultado['data_acesso_final'].strftime('%d/%m/%Y')}").pack(fill='x', anchor='w')

            self.frame_whatsapp.pack(pady=20, padx=10, fill="x", side='bottom')

        if data_simulacao_hoje.day == data_inicio.day and data_simulacao_hoje >= data_inicio:
            resposta = messagebox.askyesno("Verificação de Pagamento", "A parcela de hoje já foi debitada do cartão do cliente?")
            processar_calculo(resposta)
        else:
            processar_calculo()

    def clear_fields(self):
        """Limpa os campos do simulador."""
        self.entry_data_inicio.delete(0, 'end')
        self.entry_parcelas_atraso.delete(0, 'end')
        self.combo_plano.set('Anual (12 meses)')

        self.frame_whatsapp.pack_forget()
        for widget in self.frame_resultado.winfo_children():
            if widget != self.frame_whatsapp:
                widget.destroy()

        ttk.Label(self.frame_resultado, text="O resultado aparecerá aqui...", font=self.app.FONT_MAIN, style="secondary.TLabel").pack(expand=True)
        self.entry_data_inicio.focus_set()

        self.entry_matricula.delete(0, 'end')
        self.entry_nome_cliente.delete(0, 'end')
        self.calculo_resultado = {}

    def _ask_for_reason_popup(self):
        """Popup para perguntar o motivo do cancelamento."""
        self.popup_motivo = None
        popup = Toplevel(self.app)
        popup.title("Motivo do Cancelamento")
        popup_width = 550
        popup_height = 450
        
        # Chama o método de centralizar do app principal
        self.app._center_popup(popup, popup_width, popup_height) 
        
        container = ttk.Frame(popup, padding=20)
        container.pack(fill='both', expand=True)
        ttk.Label(container, text="Selecione o motivo do cancelamento:", font=("-weight bold")).pack(pady=(0, 10), anchor='w')
        selected_reason = StringVar(value="")
        self.entry_other_reason = None
        radio_frame = ttk.Frame(container)
        radio_frame.pack(fill='x', anchor='w')

        def update_other_entry_state():
            if selected_reason.get() == "OUTROS":
                if self.entry_other_reason is None:
                    other_entry_container = ttk.Frame(container)
                    other_entry_container.pack(fill='both', expand=True, pady=5, anchor='w')
                    ttk.Label(other_entry_container, text="Descreva:").pack(side='top', anchor='w')
                    self.entry_other_reason = scrolledtext.ScrolledText(other_entry_container, height=5, width=60, font=self.app.FONT_MAIN)
                    self.entry_other_reason.pack(side='left', fill='both', expand=True)
                    self.entry_other_reason.focus_set()
            else:
                if self.entry_other_reason is not None:
                    self.entry_other_reason.master.destroy()
                    self.entry_other_reason = None

        for motivo in MOTIVOS_CANCELAMENTO:
            rb = ttk.Radiobutton(radio_frame, text=motivo, variable=selected_reason, value=motivo, command=update_other_entry_state, style='Toolbutton')
            rb.pack(anchor='w', pady=2)

        def on_confirm():
            motivo_selecionado = selected_reason.get()
            final_motivo = ""
            if not motivo_selecionado:
                messagebox.showwarning("Campo Vazio", "Por favor, selecione ou descreva um motivo.", parent=popup)
                return
            if motivo_selecionado == "OUTROS":
                motivo_digitado = self.entry_other_reason.get("1.0", "end-1c").strip()
                if not motivo_digitado:
                    messagebox.showwarning("Campo Vazio", "Por favor, descreva o motivo em 'Outros'.", parent=popup)
                    return
                final_motivo = f"OUTROS: {motivo_digitado.upper()}"
            else:
                final_motivo = motivo_selecionado
            self.popup_motivo = final_motivo
            popup.destroy()

        ttk.Button(container, text="Confirmar e Copiar", style="success.TButton", command=on_confirm).pack(pady=15, side='bottom')
        self.app.wait_window(popup)

    def copiar_texto_gerencia(self):
        """Copia o texto para a gerência (pendências)."""
        if 'total_a_pagar' not in self.calculo_resultado:
            messagebox.showerror("Erro", "Execute um cálculo válido primeiro.")
            return

        matricula = self.entry_matricula.get()
        nome_cliente = self.entry_nome_cliente.get()

        if not matricula or not nome_cliente:
            messagebox.showerror("Erro", "Preencha a Matrícula e o Nome do Cliente.")
            return
        
        self._ask_for_reason_popup()
        motivo = self.popup_motivo
        if not motivo:
            return
        
        data_acesso_str = self.calculo_resultado['data_acesso_final'].strftime('%d/%m/%Y')
        texto_formatado = (f"*CANCELAMENTO*\n\nMatrícula: {matricula}\nNome: {nome_cliente}\n\nMotivo: {motivo}\nAcesso até: {data_acesso_str}\n\n> {self.app.consultor_logado_data.get('nome', 'Consultor')}")
        
        self.app.clipboard_clear()
        self.app.clipboard_append(texto_formatado)
        self.app.show_toast("Texto Copiado!", "Mensagem para pendências copiada com sucesso.")

    def copiar_texto_cliente(self):
        """Copia o texto de detalhes para o cliente."""
        if 'total_a_pagar' not in self.calculo_resultado:
            messagebox.showerror("Erro", "Execute um cálculo válido primeiro.")
            return

        matricula = self.entry_matricula.get()
        nome_cliente = self.entry_nome_cliente.get()

        if not matricula or not nome_cliente:
            messagebox.showerror("Erro", "Preencha a Matrícula e o Nome do Cliente.")
            return
        
        linha_proxima_parcela = ""
        if self.calculo_resultado['valor_proxima_parcela'] > 0:
            texto_parcela_formatado = self.calculo_resultado['linha_mensalidade_a_vencer']
            linha_proxima_parcela = (f"- Próxima parcela: {texto_parcela_formatado}\n")
            
        texto_formatado = (f"*INFORMAÇÕES CANCELAMENTO*\n\n- Nome: {nome_cliente}\n- Matricula: {matricula}\n\n*💸 VALORES*\n- Parcelas vencidas: R$ {self.calculo_resultado['valor_atrasado']:.2f} ({self.calculo_resultado['parcelas_atrasadas_qtd']} Parcelas)\n{linha_proxima_parcela}- Valor da multa: R$ {self.calculo_resultado['valor_multa']:.2f} (10% de {self.calculo_resultado['meses_para_multa']} Meses)\n> TOTAL A SER PAGO: *R$ {self.calculo_resultado['total_a_pagar']:.2f}*\n\nApós o cancelamento, *seu acesso permanecerá ativo até*: {self.calculo_resultado['data_acesso_final'].strftime('%d/%m/%Y')}")
        
        self.app.clipboard_clear()
        self.app.clipboard_append(texto_formatado)
        self.app.show_toast("Texto Copiado!", "Detalhes do cancelamento copiados com sucesso.")

    def mostrar_janela_com_link(self, link):
        """Popup que mostra o link de assinatura gerado."""
        janela_link = Toplevel(self.app)
        janela_link.title("Link Gerado com Sucesso!")
        popup_width = 450
        popup_height = 180
        self.app._center_popup(janela_link, popup_width, popup_height)
        
        container = ttk.Frame(janela_link, padding=20)
        container.pack(fill='both', expand=True)
        ttk.Label(container, text="Envie este link para o cliente:", font=("-weight bold")).pack(pady=(0, 10))
        
        entry_link = ttk.Entry(container, width=60)
        entry_link.insert(0, link)
        entry_link.pack(padx=10, pady=5)
        entry_link.config(state="readonly")

        def copiar_link_e_mensagem():
            nome_cliente = self.entry_nome_cliente.get().split(' ')[0]
            mensagem_completa = (f"Para prosseguir com o cancelamento da sua matrícula, "
                                 "Preciso que preencha as informações e assine "
                                 f"através deste link: {link}\n\n"
                                 "Por favor, me mande o PDF assim que finalizar, ok? 😉")
            self.app.clipboard_clear()
            self.app.clipboard_append(mensagem_completa)
            self.app.show_toast("Mensagem Copiada!", "O link e a mensagem para o cliente foram copiados!")
            janela_link.destroy()

        ttk.Button(container, text="Copiar Mensagem e Link", command=copiar_link_e_mensagem, style='primary.TButton').pack(pady=10)
        self.app.wait_window(janela_link)

    def gerar_documento_popup(self):
        """Popup para pedir o CPF e gerar o link de assinatura."""
        if 'total_a_pagar' not in self.calculo_resultado:
            messagebox.showerror("Erro", "Execute um cálculo válido primeiro.")
            return

        nome_cliente = self.entry_nome_cliente.get()
        matricula = self.entry_matricula.get()

        if not nome_cliente or not matricula:
            messagebox.showerror("Erro", "Preencha Nome e Matrícula para gerar o documento.")
            return
        
        popup = Toplevel(self.app)
        popup.title("Informação Adicional")
        popup_width = 450
        popup_height = 200
        self.app._center_popup(popup, popup_width, popup_height)
        
        container = ttk.Frame(popup, padding=20)
        container.pack(fill='both', expand=True)
        ttk.Label(container, text="Digite o CPF do Cliente:", font=("-weight bold")).pack(pady=(0, 10))
        
        vcmd_cpf = (self.app.register(validar_e_formatar_cpf_input), '%P')
        entry_cpf_popup = ttk.Entry(container, width=30, validate="key", validatecommand=vcmd_cpf)
        entry_cpf_popup.pack(pady=5)
        entry_cpf_popup.focus_set()

        def on_paste_cpf(event):
            try:
                texto_colado = self.app.clipboard_get()
                cpf_limpo = limpar_cpf(texto_colado)
                entry_cpf_popup.delete(0, 'end')
                entry_cpf_popup.insert(0, cpf_limpo[:11])
            except:
                pass
            return "break"
        entry_cpf_popup.bind("<<Paste>>", on_paste_cpf)

        def finalizar_geracao():
            cpf_limpo = limpar_cpf(entry_cpf_popup.get())
            if not validar_cpf_algoritmo(cpf_limpo):
                messagebox.showerror("CPF Inválido", "O CPF digitado não é válido.", parent=popup)
                return
            
            dados_para_enviar = {
                "nome": nome_cliente.upper(),
                "cpf": cpf_limpo,
                "matricula": matricula,
                "valor_multa": f"{self.calculo_resultado['total_a_pagar']:.2f}",
                "data_inicio_contrato": self.calculo_resultado['data_inicio_contrato'].strftime('%d/%m/%Y'),
                "consultor": self.app.consultor_logado_data.get('nome', 'CONSULTOR').upper()
            }
            popup.destroy()
            
            try:
                url_api = "https://assinagym.onrender.com/api/gerar-link"
                self.app.config(cursor="watch")
                self.app.update_idletasks()
                
                response = requests.post(url_api, json=dados_para_enviar, timeout=20)
                
                self.app.config(cursor="")
                if response.status_code == 200:
                    self.mostrar_janela_com_link(response.json().get("link_assinatura"))
                else:
                    messagebox.showerror("Erro de Servidor", f"O servidor respondeu com um erro: {response.status_code}\n{response.text}")
            except requests.exceptions.RequestException as e:
                self.app.config(cursor="")
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor. Verifique sua conexão e se o servidor AssinaGym está online.")

        ttk.Button(container, text="Confirmar e Gerar Link", command=finalizar_geracao, style='success.TButton').pack(pady=10)
        self.app.wait_window(popup)