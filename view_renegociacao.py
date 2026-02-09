# -*- coding: utf-8 -*-

"""
Arquivo: view_renegociacao.py
Descricao: Contem a tela de renegociacao de planos.
"""

import ttkbootstrap as ttk
from tkinter import messagebox, Toplevel
from tkinter import ttk as standard_ttk
from datetime import date

from app_utils import (
    PLANOS,
    validar_matricula,
    formatar_data,
    formatar_reais,
    calcular_renegociacao,
)


class RenegociacaoView:
    def __init__(self, app, main_frame):
        self.app = app
        self.main_frame = main_frame
        self.calculo_resultado = {}
        self.popup_plano_valor = None

        header = ttk.Frame(self.main_frame)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(
            header,
            text="Renegociacao de Planos",
            font=self.app.FONT_TITLE,
            bootstyle="info"
        ).pack(anchor="w")

        frame_form = ttk.Frame(self.main_frame)
        frame_form.pack(padx=0, pady=5, fill="x", anchor="w")

        ttk.Label(frame_form, text="Data de inicio do contrato:", width=35, anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_data_inicio = ttk.Entry(frame_form, width=30)
        self.entry_data_inicio.grid(row=0, column=1, sticky="w", pady=5)
        self.entry_data_inicio.bind("<KeyRelease>", lambda e: formatar_data(e, self.entry_data_inicio))

        ttk.Label(frame_form, text="Data da ultima mensalidade paga:", width=35, anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_data_ultimo = ttk.Entry(frame_form, width=30)
        self.entry_data_ultimo.grid(row=1, column=1, sticky="w", pady=5)
        self.entry_data_ultimo.bind("<KeyRelease>", lambda e: formatar_data(e, self.entry_data_ultimo))

        ttk.Label(frame_form, text="Tipo de plano:", width=35, anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_plano = ttk.Combobox(frame_form, values=list(PLANOS.keys()), width=27, state="readonly")
        self.combo_plano.grid(row=2, column=1, sticky="w", pady=5)
        self.combo_plano.set("Anual (12 meses)")

        frame_botoes = ttk.Frame(frame_form)
        frame_botoes.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)

        ttk.Button(frame_botoes, text="Calcular", command=self.do_calculation, style="success.TButton", width=20).pack(side="left", padx=(0, 5), ipady=5)
        ttk.Button(frame_botoes, text="Nova Simulacao", command=self.clear_fields, style="danger.TButton", width=20).pack(side="left", padx=5, ipady=5)

        self.frame_resultado = ttk.Frame(self.main_frame, padding=(20, 15), relief="solid", borderwidth=1)
        self.frame_resultado.pack(pady=5, padx=10, fill="both", expand=True, anchor="w")

        highlight = ttk.Frame(self.frame_resultado, padding=(12, 8))
        highlight.pack(fill="x")
        ttk.Label(
            highlight,
            text="Duas opcoes de renegociacao: Cancelamento ou Plano Novo",
            font=self.app.FONT_BOLD,
            bootstyle="info"
        ).pack(anchor="w")

        self.placeholder_label = ttk.Label(self.frame_resultado, text="O resultado aparecera aqui...", font=self.app.FONT_MAIN, style="secondary.TLabel")
        self.placeholder_label.pack(expand=True)

        self.frame_acoes = standard_ttk.LabelFrame(self.frame_resultado, text=" Acoes de Renegociacao ", padding=(15, 10))

        vcmd_matricula = (self.app.register(validar_matricula), "%P")
        ttk.Label(self.frame_acoes, text="Matricula:").grid(row=0, column=1, sticky="w", pady=4)
        self.entry_matricula = ttk.Entry(self.frame_acoes, width=35, validate="key", validatecommand=vcmd_matricula)
        self.entry_matricula.grid(row=0, column=2, sticky="w", pady=4)

        ttk.Label(self.frame_acoes, text="Nome do aluno:").grid(row=1, column=1, sticky="w", pady=4)
        self.entry_nome_cliente = ttk.Entry(self.frame_acoes, width=35)
        self.entry_nome_cliente.grid(row=1, column=2, sticky="w", pady=4)

        frame_botoes_copiar = ttk.Frame(self.frame_acoes)
        frame_botoes_copiar.grid(row=2, column=1, columnspan=2, pady=15)

        ttk.Button(frame_botoes_copiar, text="Copiar Detalhes", style="info.Outline.TButton", command=self.copiar_detalhes).pack(side="left", padx=5)
        ttk.Button(frame_botoes_copiar, text="Confirmar Renegociacao", style="success.Outline.TButton", command=self.confirmar_renegociacao_cancelamento).pack(side="left", padx=5)

        self.frame_acoes.columnconfigure(0, weight=1)
        self.frame_acoes.columnconfigure(3, weight=1)

    def _ask_plan_value_popup(self):
        """Mostra um popup para escolher o valor do plano (jun/2025)."""
        self.popup_plano_valor = None

        popup = Toplevel(self.app)
        popup.title("Verificacao de Contrato")
        self.app._center_popup(popup, 450, 220)

        container = ttk.Frame(popup, padding=20)
        container.pack(fill="both", expand=True)

        msg = "Este contrato (iniciado em Junho/2025) e no valor novo ou antigo?"
        ttk.Label(container, text=msg, font=self.app.FONT_BOLD, wraplength=400, justify="center").pack(pady=(0, 15))
        ttk.Label(container, text="Selecione o valor correto do plano Anual:", font=self.app.FONT_MAIN).pack(pady=(0, 20))

        frame_botoes = ttk.Frame(container)
        frame_botoes.pack(fill="x", expand=True)
        frame_botoes.grid_columnconfigure(0, weight=1)
        frame_botoes.grid_columnconfigure(1, weight=1)

        def on_select(valor):
            self.popup_plano_valor = valor
            popup.destroy()

        btn_359 = ttk.Button(
            frame_botoes,
            text="R$ 359,00 (Antigo)",
            command=lambda: on_select(359.00),
            style="secondary.TButton",
            width=20,
        )
        btn_359.grid(row=0, column=0, padx=10, ipady=10)

        btn_389 = ttk.Button(
            frame_botoes,
            text="R$ 389,00 (Novo)",
            command=lambda: on_select(389.00),
            style="success.TButton",
            width=20,
        )
        btn_389.grid(row=0, column=1, padx=10, ipady=10)
        btn_389.focus_set()

        def on_close():
            self.popup_plano_valor = None
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_close)
        self.app.wait_window(popup)

    def _plural_mes(self, qtd):
        return "Mes" if qtd == 1 else "Meses"

    def _fmt_date(self, valor):
        if hasattr(valor, "strftime"):
            return valor.strftime("%d/%m/%Y")
        return str(valor)

    def do_calculation(self):
        data_inicio_str = self.entry_data_inicio.get()
        data_ultimo_str = self.entry_data_ultimo.get()
        tipo_plano = self.combo_plano.get()

        if not data_inicio_str or not data_ultimo_str or not tipo_plano:
            messagebox.showerror("Erro", "Preencha as datas e o tipo de plano.")
            return

        try:
            dia, mes, ano = map(int, data_inicio_str.split("/"))
            data_inicio = date(ano, mes, dia)
        except Exception:
            messagebox.showerror("Erro", "Formato de data de inicio invalido. Use dd/mm/aaaa.")
            return

        try:
            dia, mes, ano = map(int, data_ultimo_str.split("/"))
            data_ultimo = date(ano, mes, dia)
        except Exception:
            messagebox.showerror("Erro", "Formato da ultima mensalidade invalido. Use dd/mm/aaaa.")
            return

        data_simulacao_hoje = date.today()
        if data_inicio > data_simulacao_hoje or data_ultimo > data_simulacao_hoje:
            messagebox.showerror("Data Invalida", "As datas nao podem estar no futuro.")
            return

        DATA_INICIO_PERGUNTA = date(2025, 6, 1)
        DATA_FIM_PERGUNTA = date(2025, 6, 30)
        DATA_PRECO_NOVO_AUTO = date(2025, 7, 1)

        valor_override = None
        if tipo_plano == "Anual (12 meses)":
            if DATA_INICIO_PERGUNTA <= data_inicio <= DATA_FIM_PERGUNTA:
                self._ask_plan_value_popup()
                if self.popup_plano_valor is None:
                    messagebox.showwarning("Calculo Cancelado", "Voce deve selecionar um valor para continuar.")
                    return
                valor_override = self.popup_plano_valor
            elif data_inicio >= DATA_PRECO_NOVO_AUTO:
                valor_override = 389.00

        kwargs = {}
        if valor_override is not None:
            kwargs["valor_mensalidade_override"] = valor_override

        self.calculo_resultado = calcular_renegociacao(data_inicio, data_ultimo, tipo_plano, **kwargs)

        for widget in self.frame_resultado.winfo_children():
            if widget != self.frame_acoes:
                widget.destroy()

        if "erro_data" in self.calculo_resultado:
            messagebox.showerror("Data Invalida", self.calculo_resultado["erro_data"])
            ttk.Label(self.frame_resultado, text="O resultado aparecera aqui...", font=self.app.FONT_MAIN, style="secondary.TLabel").pack(expand=True)
            self.frame_acoes.pack_forget()
            return

        if "erro_geral" in self.calculo_resultado:
            messagebox.showerror("Erro", self.calculo_resultado["erro_geral"])
            ttk.Label(self.frame_resultado, text="O resultado aparecera aqui...", font=self.app.FONT_MAIN, style="secondary.TLabel").pack(expand=True)
            self.frame_acoes.pack_forget()
            return

        resultado = self.calculo_resultado
        plural_utilizados = self._plural_mes(resultado["meses_utilizados"])
        plural_restantes = self._plural_mes(resultado["meses_restantes"])
        plural_abonadas = self._plural_mes(resultado["parcelas_abonadas_qtd"])

        ttk.Label(self.frame_resultado, text=f"Data da simulacao: {self._fmt_date(resultado['data_simulacao'])}").pack(fill="x", anchor="w")
        ttk.Label(self.frame_resultado, text=f"Plano: {resultado['plano']} ({formatar_reais(resultado['valor_plano'])})").pack(fill="x", anchor="w")
        ttk.Label(self.frame_resultado, text=f"Inicio do contrato: {self._fmt_date(resultado['data_inicio_contrato'])}").pack(fill="x", anchor="w")
        ttk.Label(self.frame_resultado, text=f"Ultima mensalidade paga: {self._fmt_date(resultado['data_ultimo_pagamento'])}").pack(fill="x", anchor="w")
        ttk.Separator(self.frame_resultado).pack(fill="x", pady=5)

        container_opcoes = ttk.Frame(self.frame_resultado)
        container_opcoes.pack(fill="both", expand=True)
        container_opcoes.grid_columnconfigure(0, weight=1, uniform="opcao")
        container_opcoes.grid_columnconfigure(1, weight=1, uniform="opcao")

        frame_cancelamento = standard_ttk.LabelFrame(container_opcoes, text=" CANCELAMENTO ", padding=(12, 10))
        frame_cancelamento.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(frame_cancelamento, text="❌", font=self.app.FONT_TITLE, bootstyle="danger").pack(anchor="w")
        ttk.Label(
            frame_cancelamento,
            text="(multa calculada a partir do ultimo mes pago; parcelas em aberto ate hoje excluidas)",
            font=self.app.FONT_SMALL,
            bootstyle="secondary"
        ).pack(anchor="w")
        ttk.Label(frame_cancelamento, text=f"Meses utilizados: {resultado['meses_utilizados']} {plural_utilizados}", font=self.app.FONT_BOLD).pack(anchor="w")
        ttk.Label(frame_cancelamento, text=f"Multa: {formatar_reais(resultado['valor_multa'])} ({resultado['meses_restantes']} {plural_restantes})", font=self.app.FONT_BOLD).pack(anchor="w")
        ttk.Label(frame_cancelamento, text=f"Parcelas excluidas: {resultado['parcelas_abonadas_qtd']} {plural_abonadas} ({formatar_reais(resultado['valor_abonado'])})").pack(anchor="w")
        ttk.Separator(frame_cancelamento).pack(fill="x", pady=5)
        ttk.Label(frame_cancelamento, text=f"TOTAL A PAGAR: {formatar_reais(resultado['valor_multa'])}", font=self.app.FONT_BOLD).pack(anchor="w")

        frame_plano_novo = standard_ttk.LabelFrame(container_opcoes, text=" PLANO NOVO ", padding=(12, 10))
        frame_plano_novo.grid(row=0, column=1, sticky="nsew")

        ttk.Label(frame_plano_novo, text="✅", font=self.app.FONT_TITLE, bootstyle="success").pack(anchor="w")
        ttk.Label(
            frame_plano_novo,
            text="(todas parcelas em aberto excluidas, novo plano do zero sem taxa de matricula)",
            font=self.app.FONT_SMALL,
            bootstyle="secondary"
        ).pack(anchor="w")
        ttk.Label(frame_plano_novo, text=f"Parcelas excluidas: {resultado['parcelas_abonadas_qtd']} {plural_abonadas}", font=self.app.FONT_BOLD).pack(anchor="w")
        ttk.Label(frame_plano_novo, text=f"Valor total excluido: {formatar_reais(resultado['valor_abonado'])}", font=self.app.FONT_BOLD).pack(anchor="w")
        ttk.Separator(frame_plano_novo).pack(fill="x", pady=5)
        ttk.Label(frame_plano_novo, text="TOTAL A PAGAR: R$ 0,00", font=self.app.FONT_BOLD).pack(anchor="w")
        ttk.Label(frame_plano_novo, text="Fidelidade reiniciada do zero.").pack(anchor="w")

        self.frame_acoes.pack(pady=20, padx=10, fill="x", side="bottom")

    def clear_fields(self):
        self.entry_data_inicio.delete(0, "end")
        self.entry_data_ultimo.delete(0, "end")
        self.combo_plano.set("Anual (12 meses)")

        self.frame_acoes.pack_forget()
        for widget in self.frame_resultado.winfo_children():
            if widget != self.frame_acoes:
                widget.destroy()

        ttk.Label(self.frame_resultado, text="O resultado aparecera aqui...", font=self.app.FONT_MAIN, style="secondary.TLabel").pack(expand=True)
        self.entry_data_inicio.focus_set()

        self.entry_matricula.delete(0, "end")
        self.entry_nome_cliente.delete(0, "end")
        self.calculo_resultado = {}

    def _validar_dados_copia(self):
        if not self.calculo_resultado:
            messagebox.showerror("Erro", "Execute um calculo valido primeiro.")
            return None

        matricula = self.entry_matricula.get()
        nome_cliente = self.entry_nome_cliente.get()

        if not matricula or not nome_cliente:
            messagebox.showerror("Erro", "Preencha a Matricula e o Nome do aluno.")
            return None

        return matricula, nome_cliente

    def copiar_detalhes(self):
        dados = self._validar_dados_copia()
        if not dados:
            return

        matricula, nome_cliente = dados
        r = self.calculo_resultado
        plural_utilizados = self._plural_mes(r["meses_utilizados"])
        plural_restantes = self._plural_mes(r["meses_restantes"])
        plural_abonadas = self._plural_mes(r["parcelas_abonadas_qtd"])

        texto_formatado = (
            "*RENEGOCIACAO*\n\n"
            f"Matricula: {matricula}\n"
            f"Nome: {nome_cliente}\n\n"
            "*Dados do contrato*\n"
            f"- Plano: {r['plano']} ({formatar_reais(r['valor_plano'])})\n"
            f"- Assinou em: {self._fmt_date(r['data_inicio_contrato'])}\n"
            f"- Ultima parcela paga: {self._fmt_date(r['data_ultimo_pagamento'])}\n\n"
            "*OPCAO 1 - CANCELAMENTO* ❌ (multa calculada a partir do ultimo mes pago; parcelas em aberto ate hoje excluidas)\n"
            f"- Meses utilizados: {r['meses_utilizados']} {plural_utilizados}\n"
            f"- Multa: {formatar_reais(r['valor_multa'])} ({r['meses_restantes']} {plural_restantes})\n"
            f"- Parcelas excluidas: {r['parcelas_abonadas_qtd']} {plural_abonadas} ({formatar_reais(r['valor_abonado'])})\n\n"
            "*OPCAO 2 - PLANO NOVO* ✅ (todas parcelas em aberto excluidas, novo plano do zero sem taxa de matricula)\n"
            f"- Parcelas excluidas: {r['parcelas_abonadas_qtd']} {plural_abonadas} ({formatar_reais(r['valor_abonado'])})\n"
            "- TOTAL A PAGAR: R$ 0,00\n"
            "- Fidelidade reiniciada do zero\n"
        )

        self.app.clipboard_clear()
        self.app.clipboard_append(texto_formatado)
        self.app.show_toast("Texto Copiado!", "Detalhes da renegociacao copiados com sucesso.")

    def confirmar_renegociacao_cancelamento(self):
        dados = self._validar_dados_copia()
        if not dados:
            return

        matricula, nome_cliente = dados
        r = self.calculo_resultado
        plural_utilizados = self._plural_mes(r["meses_utilizados"])
        plural_restantes = self._plural_mes(r["meses_restantes"])

        texto_formatado = (
            "*RENEGOCIACAO - CANCELAMENTO*\n\n"
            f"Matricula: {matricula}\n"
            f"{nome_cliente}\n\n"
            f"*Assinou em:* {self._fmt_date(r['data_inicio_contrato'])}\n"
            f"*Ultima parcela paga:* {self._fmt_date(r['data_ultimo_pagamento'])}\n"
            f"*Meses utilizados:* {r['meses_utilizados']} {plural_utilizados}\n"
            f"*Multa:* {formatar_reais(r['valor_multa'])} ({r['meses_restantes']} {plural_restantes})\n\n"
            f"> {self.app.consultor_logado_data.get('nome', 'Consultor')}"
        )

        self.app.clipboard_clear()
        self.app.clipboard_append(texto_formatado)
        self.app.show_toast("Texto Copiado!", "Renegociacao de cancelamento copiada com sucesso.")
