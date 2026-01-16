# -*- coding: utf-8 -*-

"""
Arquivo: view_notinhas.py
Descrição: Tela de Contagem de Notinhas (Crédito/Débito) com entrada rápida.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import ttkbootstrap as ttk
from tkinter import messagebox
from tkinter import ttk as standard_ttk


_TWO_PLACES = Decimal("0.01")


def _parse_money_ptbr(raw: str) -> Decimal:
    """Parse monetário pt-BR com modo "maquininha" (comportamento original).

    Regras:
    - Com vírgula: 10,2 -> 10,20; 10,20 -> 10,20; 1.234,56 -> 1234,56
    - Só dígitos:
        - 0..99 -> reais inteiros (35 -> 35,00)
        - >= 3 dígitos -> últimos 2 dígitos são centavos (3590 -> 35,90; 350 -> 3,50)
    """
    s = (raw or "").strip()
    if not s:
        raise ValueError("vazio")

    # Normaliza espaços
    s = s.replace(" ", "")

    if s.isdigit():
        if len(s) >= 3:
            v = (Decimal(int(s)) / Decimal(100)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
            return v
        v = Decimal(int(s)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        return v

    # Se tem vírgula, consideramos vírgula como decimal e pontos como milhar
    if "," in s:
        s = s.replace(".", "")
        s = s.replace(",", ".")

    # Permite digitar só inteiro
    try:
        v = Decimal(s)
    except InvalidOperation as e:
        raise ValueError("inválido") from e

    if v < 0:
        raise ValueError("negativo")

    return v.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def _format_money_ptbr(value: Decimal) -> str:
    # Formata como 1.234,56 (simples)
    q = value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    s = f"{q:.2f}"  # 1234.56
    inteiro, dec = s.split(".")
    inteiro_rev = inteiro[::-1]
    grupos = [inteiro_rev[i : i + 3] for i in range(0, len(inteiro_rev), 3)]
    inteiro_pt = ".".join(g[::-1] for g in grupos[::-1])
    return f"{inteiro_pt},{dec}"


@dataclass(frozen=True)
class Lancamento:
    tipo: str  # "Crédito" | "Débito"
    valor: Decimal


class NotinhasView:
    def __init__(self, app, main_frame):
        self.app = app
        self.main_frame = main_frame

        # Estado persistido no App (não some ao trocar de tela)
        if not hasattr(self.app, "notinhas_state") or not isinstance(getattr(self.app, "notinhas_state"), dict):
            self.app.notinhas_state = {"tipo": "Crédito", "lancamentos": []}

        self.lancamentos: list[Lancamento] = []
        self.tipo_var = ttk.StringVar(value=str(self.app.notinhas_state.get("tipo", "Crédito")))

        ttk.Label(self.main_frame, text="Contagem de Notinhas", font=self.app.FONT_TITLE).pack(
            pady=(0, 10), anchor="w"
        )

        # Controles topo
        frame_top = ttk.Frame(self.main_frame)
        frame_top.pack(fill="x", pady=(0, 10))
        frame_top.grid_columnconfigure(3, weight=1)

        ttk.Label(frame_top, text="Tipo:", font=self.app.FONT_BOLD).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            frame_top,
            text="Crédito",
            variable=self.tipo_var,
            value="Crédito",
            bootstyle="success-toolbutton",
            command=self._on_tipo_change,
        ).grid(row=0, column=1, sticky="w", padx=(10, 10))
        ttk.Radiobutton(
            frame_top,
            text="Débito",
            variable=self.tipo_var,
            value="Débito",
            bootstyle="info-toolbutton",
            command=self._on_tipo_change,
        ).grid(row=0, column=2, sticky="w")

        ttk.Label(frame_top, text="Valor:", font=self.app.FONT_BOLD).grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.entry_valor = ttk.Entry(frame_top, width=20, font=(self.app.FONT_MAIN[0], 14))
        self.entry_valor.grid(row=1, column=1, sticky="w", padx=(10, 10), pady=(10, 0))
        self.entry_valor.bind("<Return>", self._on_enter_add)
        self.entry_valor.bind("<KeyRelease>", self._on_valor_typing)

        self.lbl_preview = ttk.Label(frame_top, text="Interpretado: —", style="secondary.TLabel")
        self.lbl_preview.grid(row=2, column=1, columnspan=2, sticky="w", padx=(10, 10), pady=(6, 0))

        ttk.Button(
            frame_top,
            text="Adicionar (Enter)",
            style="success.TButton",
            command=self._add_value,
            width=20,
        ).grid(row=1, column=2, sticky="w", pady=(10, 0))

        frame_actions = ttk.Frame(frame_top)
        frame_actions.grid(row=1, column=3, sticky="e", pady=(10, 0))
        ttk.Button(
            frame_actions,
            text="Desfazer último",
            style="secondary.Outline.TButton",
            command=self._undo_last,
            width=18,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            frame_actions,
            text="Limpar sessão",
            style="danger.Outline.TButton",
            command=self._clear_all,
            width=16,
        ).pack(side="left")

        # Corpo: lista + totais
        frame_body = ttk.Frame(self.main_frame)
        frame_body.pack(fill="both", expand=True)
        frame_body.grid_columnconfigure(0, weight=3)
        frame_body.grid_columnconfigure(1, weight=2)
        frame_body.grid_rowconfigure(0, weight=1)

        frame_list = standard_ttk.LabelFrame(frame_body, text=" Lançamentos ", padding=10)
        frame_list.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame_list.grid_rowconfigure(0, weight=1)
        frame_list.grid_columnconfigure(0, weight=1)

        cols = ("tipo", "valor")
        self.tree = ttk.Treeview(frame_list, columns=cols, show="headings", height=12, bootstyle="secondary")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("valor", text="Valor")
        self.tree.column("tipo", width=120, anchor="w")
        self.tree.column("valor", width=140, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        frame_list_actions = ttk.Frame(frame_list)
        frame_list_actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(
            frame_list_actions,
            text="Apagar selecionado",
            style="danger.TButton",
            command=self._delete_selected,
            width=22,
        ).pack(side="left")
        ttk.Label(
            frame_list_actions,
            text="Dica: Enter adiciona. Preview mostra o valor. Ex: 3590→35,90 | para 100,00 digite 100,00",
            style="secondary.TLabel",
        ).pack(side="right")

        frame_totals = standard_ttk.LabelFrame(frame_body, text=" Totais (tempo real) ", padding=10)
        frame_totals.grid(row=0, column=1, sticky="nsew")

        self.lbl_credito_qtd = ttk.Label(frame_totals, text="Crédito: 0 itens", font=self.app.FONT_BOLD)
        self.lbl_credito_qtd.pack(anchor="w", pady=(0, 4))
        self.lbl_credito_soma = ttk.Label(frame_totals, text="Crédito: R$ 0,00", font=self.app.FONT_MAIN)
        self.lbl_credito_soma.pack(anchor="w", pady=(0, 10))

        self.lbl_debito_qtd = ttk.Label(frame_totals, text="Débito: 0 itens", font=self.app.FONT_BOLD)
        self.lbl_debito_qtd.pack(anchor="w", pady=(0, 4))
        self.lbl_debito_soma = ttk.Label(frame_totals, text="Débito: R$ 0,00", font=self.app.FONT_MAIN)
        self.lbl_debito_soma.pack(anchor="w", pady=(0, 10))

        ttk.Separator(frame_totals).pack(fill="x", pady=10)

        self.lbl_total_qtd = ttk.Label(frame_totals, text="Total: 0 itens", font=self.app.FONT_BOLD)
        self.lbl_total_qtd.pack(anchor="w", pady=(0, 4))
        self.lbl_total_soma = ttk.Label(frame_totals, text="Total: R$ 0,00", font=self.app.FONT_BOLD)
        self.lbl_total_soma.pack(anchor="w")

        # Foco inicial
        self.entry_valor.focus_set()

        # Inicializa preview
        self._update_preview_from_entry()

        # Reidrata lançamentos persistidos
        self._load_state_into_ui()
        self._update_totals()

    def _on_tipo_change(self):
        self._persist_state()
        self._update_totals()

    def _persist_state(self):
        try:
            self.app.notinhas_state["tipo"] = self.tipo_var.get() or "Crédito"
            self.app.notinhas_state["lancamentos"] = [
                {"tipo": l.tipo, "valor": str(l.valor)} for l in self.lancamentos
            ]
        except Exception:
            pass

    def _update_preview_from_entry(self):
        raw = self.entry_valor.get() or ""
        if not raw.strip():
            self.lbl_preview.config(text="Interpretado: R$ 0,00")
            return
        try:
            valor = _parse_money_ptbr(raw)
        except Exception:
            self.lbl_preview.config(text="Interpretado: —")
            return
        self.lbl_preview.config(text=f"Interpretado: R$ {_format_money_ptbr(valor)}")

    def _on_valor_typing(self, event=None):
        self._update_preview_from_entry()

    def _load_state_into_ui(self):
        # Limpa UI
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self.lancamentos.clear()
        raw_list = self.app.notinhas_state.get("lancamentos", [])
        if not isinstance(raw_list, list):
            return

        for item in raw_list:
            if not isinstance(item, dict):
                continue
            tipo = item.get("tipo")
            valor_raw = item.get("valor")
            if tipo not in {"Crédito", "Débito"}:
                continue
            try:
                valor = Decimal(str(valor_raw)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
            except Exception:
                continue
            lanc = Lancamento(tipo=tipo, valor=valor)
            self.lancamentos.append(lanc)
            self.tree.insert("", "end", values=(lanc.tipo, f"R$ {_format_money_ptbr(lanc.valor)}"))

    def _on_enter_add(self, event=None):
        self._add_value()

    def _add_value(self):
        raw = self.entry_valor.get()
        try:
            valor = _parse_money_ptbr(raw)
        except ValueError:
            messagebox.showwarning(
                "Valor inválido",
                "Digite um valor válido (ex: 35, 3590 para 35,90; 10,20; 1.234,56).",
            )
            self.entry_valor.focus_set()
            self.entry_valor.selection_range(0, "end")
            return

        tipo = self.tipo_var.get() or "Crédito"
        lanc = Lancamento(tipo=tipo, valor=valor)
        self.lancamentos.append(lanc)

        self.tree.insert("", "end", values=(lanc.tipo, f"R$ {_format_money_ptbr(lanc.valor)}"))
        self.entry_valor.delete(0, "end")
        self.entry_valor.focus_set()
        self._update_preview_from_entry()
        self._persist_state()
        self._update_totals()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecionar", "Selecione um lançamento para apagar.")
            return

        # Remove do fim para o começo para manter índices
        indices = []
        for iid in sel:
            idx = self.tree.index(iid)
            indices.append((iid, idx))

        for iid, idx in sorted(indices, key=lambda x: x[1], reverse=True):
            try:
                self.tree.delete(iid)
            except Exception:
                pass
            if 0 <= idx < len(self.lancamentos):
                self.lancamentos.pop(idx)

        self._update_totals()
        self._persist_state()

    def _undo_last(self):
        if not self.lancamentos:
            return
        self.lancamentos.pop()
        children = self.tree.get_children()
        if children:
            try:
                self.tree.delete(children[-1])
            except Exception:
                pass
        self._update_totals()
        self._persist_state()

    def _clear_all(self):
        if not self.lancamentos:
            return
        if not messagebox.askyesno("Confirmar", "Limpar todos os lançamentos desta sessão?"):
            return
        self.lancamentos.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._update_totals()
        self._persist_state()
        self.entry_valor.focus_set()

    def _update_totals(self):
        credito = [l for l in self.lancamentos if l.tipo == "Crédito"]
        debito = [l for l in self.lancamentos if l.tipo == "Débito"]

        credito_qtd = len(credito)
        debito_qtd = len(debito)

        credito_sum = sum((l.valor for l in credito), Decimal("0"))
        debito_sum = sum((l.valor for l in debito), Decimal("0"))

        total_qtd = credito_qtd + debito_qtd
        total_sum = (credito_sum + debito_sum).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

        self.lbl_credito_qtd.config(text=f"Crédito: {credito_qtd} notinhas")
        self.lbl_credito_soma.config(text=f"Crédito: R$ {_format_money_ptbr(credito_sum)}")
        self.lbl_debito_qtd.config(text=f"Débito: {debito_qtd} notinhas")
        self.lbl_debito_soma.config(text=f"Débito: R$ {_format_money_ptbr(debito_sum)}")
        self.lbl_total_qtd.config(text=f"Total: {total_qtd} notinhas")
        self.lbl_total_soma.config(text=f"Total: R$ {_format_money_ptbr(total_sum)}")
