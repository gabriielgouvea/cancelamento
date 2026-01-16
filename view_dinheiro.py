# -*- coding: utf-8 -*-

"""
Arquivo: view_dinheiro.py
Descrição: Tela de Contagem de Dinheiro (Caixa 01/02) com totais em tempo real.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

import ttkbootstrap as ttk
from tkinter import messagebox
from tkinter import ttk as standard_ttk


_TWO_PLACES = Decimal("0.01")


def _format_money_ptbr(value: Decimal) -> str:
    q = value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    s = f"{q:.2f}"  # 1234.56
    inteiro, dec = s.split(".")
    inteiro_rev = inteiro[::-1]
    grupos = [inteiro_rev[i : i + 3] for i in range(0, len(inteiro_rev), 3)]
    inteiro_pt = ".".join(g[::-1] for g in grupos[::-1])
    return f"{inteiro_pt},{dec}"


@dataclass(frozen=True)
class Denominacao:
    label: str
    valor: Decimal


DENOMS: list[Denominacao] = [
    Denominacao("Moeda R$ 0,05", Decimal("0.05")),
    Denominacao("Moeda R$ 0,10", Decimal("0.10")),
    Denominacao("Moeda R$ 0,25", Decimal("0.25")),
    Denominacao("Moeda R$ 0,50", Decimal("0.50")),
    Denominacao("Moeda R$ 1,00", Decimal("1.00")),
    Denominacao("Nota R$ 2,00", Decimal("2.00")),
    Denominacao("Nota R$ 5,00", Decimal("5.00")),
    Denominacao("Nota R$ 10,00", Decimal("10.00")),
    Denominacao("Nota R$ 20,00", Decimal("20.00")),
    Denominacao("Nota R$ 50,00", Decimal("50.00")),
    Denominacao("Nota R$ 100,00", Decimal("100.00")),
    Denominacao("Nota R$ 200,00", Decimal("200.00")),
]


class DinheiroView:
    def __init__(self, app, main_frame):
        self.app = app
        self.main_frame = main_frame

        # Estado persistido no App (não some ao trocar de tela)
        if not hasattr(self.app, "dinheiro_state") or not isinstance(getattr(self.app, "dinheiro_state"), dict):
            self.app.dinheiro_state = {
                "caixa_atual": "01",
                "caixas": {"01": {}, "02": {}},
            }

        self.caixa_var = ttk.StringVar(value=str(self.app.dinheiro_state.get("caixa_atual", "01")))

        # vars por denom (qtd) + labels subtotal
        self.qtd_vars: dict[str, ttk.StringVar] = {}
        self.subtotal_labels: dict[str, ttk.Label] = {}
        self.qty_entries: list[ttk.Entry] = []

        ttk.Label(self.main_frame, text="Contagem de Dinheiro", font=self.app.FONT_TITLE).pack(
            pady=(0, 10), anchor="w"
        )

        frame_top = ttk.Frame(self.main_frame)
        frame_top.pack(fill="x", pady=(0, 10))
        frame_top.grid_columnconfigure(5, weight=1)

        ttk.Label(frame_top, text="Caixa:", font=self.app.FONT_BOLD).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            frame_top,
            text="Caixa 01",
            variable=self.caixa_var,
            value="01",
            bootstyle="primary-toolbutton",
            command=self._on_caixa_change,
        ).grid(row=0, column=1, sticky="w", padx=(10, 10))
        ttk.Radiobutton(
            frame_top,
            text="Caixa 02",
            variable=self.caixa_var,
            value="02",
            bootstyle="secondary-toolbutton",
            command=self._on_caixa_change,
        ).grid(row=0, column=2, sticky="w")

        ttk.Button(
            frame_top,
            text="Limpar caixa",
            style="danger.Outline.TButton",
            command=self._clear_current_caixa,
            width=16,
        ).grid(row=0, column=3, sticky="e", padx=(10, 8))
        ttk.Button(
            frame_top,
            text="Limpar tudo",
            style="danger.TButton",
            command=self._clear_all,
            width=14,
        ).grid(row=0, column=4, sticky="e")

        # Corpo
        frame_body = ttk.Frame(self.main_frame)
        frame_body.pack(fill="both", expand=True)
        frame_body.grid_columnconfigure(0, weight=3)
        frame_body.grid_columnconfigure(1, weight=2)
        frame_body.grid_rowconfigure(0, weight=1)

        frame_form = standard_ttk.LabelFrame(frame_body, text=" Quantidades ", padding=10)
        frame_form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame_form.grid_columnconfigure(1, weight=0)
        frame_form.grid_columnconfigure(2, weight=1)

        ttk.Label(frame_form, text="Denominação", font=self.app.FONT_BOLD).grid(row=0, column=0, sticky="w")
        ttk.Label(frame_form, text="Qtd", font=self.app.FONT_BOLD).grid(row=0, column=1, sticky="w")
        ttk.Label(frame_form, text="Subtotal", font=self.app.FONT_BOLD).grid(row=0, column=2, sticky="e")

        for r, d in enumerate(DENOMS, start=1):
            key = str(d.valor)
            ttk.Label(frame_form, text=d.label, font=self.app.FONT_MAIN).grid(row=r, column=0, sticky="w", pady=3)

            v = ttk.StringVar(value="0")
            self.qtd_vars[key] = v

            entry = ttk.Entry(frame_form, textvariable=v, width=8, font=(self.app.FONT_MAIN[0], 12))
            entry.grid(row=r, column=1, sticky="w", padx=(0, 10), pady=3)
            entry.bind("<KeyRelease>", lambda e, k=key: self._on_qtd_change(k))
            entry.bind("<FocusIn>", lambda e, w=entry: w.selection_range(0, "end"))
            entry.bind("<Return>", self._focus_next_qty)
            entry.bind("<Down>", self._focus_next_qty)
            entry.bind("<Up>", self._focus_prev_qty)
            self.qty_entries.append(entry)

            lbl_sub = ttk.Label(frame_form, text="R$ 0,00", font=self.app.FONT_MAIN)
            lbl_sub.grid(row=r, column=2, sticky="e", pady=3)
            self.subtotal_labels[key] = lbl_sub

        frame_totals = standard_ttk.LabelFrame(frame_body, text=" Totais ", padding=10)
        frame_totals.grid(row=0, column=1, sticky="nsew")

        self.lbl_caixa_total = ttk.Label(frame_totals, text="Caixa atual: R$ 0,00", font=self.app.FONT_BOLD)
        self.lbl_caixa_total.pack(anchor="w", pady=(0, 10))

        self.lbl_caixa01_total = ttk.Label(frame_totals, text="Caixa 01: R$ 0,00", font=self.app.FONT_MAIN)
        self.lbl_caixa01_total.pack(anchor="w", pady=(0, 4))

        self.lbl_caixa02_total = ttk.Label(frame_totals, text="Caixa 02: R$ 0,00", font=self.app.FONT_MAIN)
        self.lbl_caixa02_total.pack(anchor="w", pady=(0, 10))

        ttk.Separator(frame_totals).pack(fill="x", pady=10)

        self.lbl_total_geral = ttk.Label(frame_totals, text="Total geral: R$ 0,00", font=self.app.FONT_BOLD)
        self.lbl_total_geral.pack(anchor="w")

        ttk.Label(
            frame_totals,
            text="Dica: digite a quantidade de cada nota/moeda.",
            style="secondary.TLabel",
        ).pack(anchor="w", pady=(10, 0))

        # Carrega estado para UI
        self._load_caixa_into_ui(self.caixa_var.get())
        self._recompute_all()

    def _focus_next_qty(self, event):
        try:
            idx = self.qty_entries.index(event.widget)
        except ValueError:
            return

        if idx < len(self.qty_entries) - 1:
            nxt = self.qty_entries[idx + 1]
            nxt.focus_set()
            nxt.selection_range(0, "end")
        return "break"

    def _focus_prev_qty(self, event):
        try:
            idx = self.qty_entries.index(event.widget)
        except ValueError:
            return

        if idx > 0:
            prev = self.qty_entries[idx - 1]
            prev.focus_set()
            prev.selection_range(0, "end")
        return "break"

    def _persist_caixa(self, caixa: str):
        data = {}
        for k, v in self.qtd_vars.items():
            raw = (v.get() or "0").strip()
            raw = raw.replace(" ", "")
            if raw == "":
                raw = "0"
            if not raw.isdigit():
                # não persiste inválido
                continue
            data[k] = int(raw)

        self.app.dinheiro_state["caixa_atual"] = caixa
        self.app.dinheiro_state.setdefault("caixas", {}).setdefault(caixa, {})
        self.app.dinheiro_state["caixas"][caixa] = data

    def _load_caixa_into_ui(self, caixa: str):
        caixas = self.app.dinheiro_state.get("caixas", {})
        data = caixas.get(caixa, {}) if isinstance(caixas, dict) else {}

        for d in DENOMS:
            key = str(d.valor)
            qtd = 0
            if isinstance(data, dict):
                qtd = int(data.get(key, 0) or 0)
            self.qtd_vars[key].set(str(qtd))

    def _on_caixa_change(self):
        # salva o caixa atual, troca UI para outro
        current = self.app.dinheiro_state.get("caixa_atual", "01")
        self._persist_caixa(str(current))

        novo = self.caixa_var.get() or "01"
        self._load_caixa_into_ui(novo)
        self._persist_caixa(novo)
        self._recompute_all()

    def _on_qtd_change(self, denom_key: str):
        v = self.qtd_vars[denom_key]
        raw = (v.get() or "").strip()
        raw = raw.replace(" ", "")

        # Permite vazio temporariamente
        if raw == "":
            self._recompute_all()
            return

        if not raw.isdigit():
            # remove caracteres inválidos mantendo só dígitos
            cleaned = "".join(ch for ch in raw if ch.isdigit())
            v.set(cleaned)

        self._persist_caixa(self.caixa_var.get() or "01")
        self._recompute_all()

    def _sum_caixa(self, caixa: str) -> Decimal:
        caixas = self.app.dinheiro_state.get("caixas", {})
        data = caixas.get(caixa, {}) if isinstance(caixas, dict) else {}
        total = Decimal("0")
        for d in DENOMS:
            key = str(d.valor)
            qtd = 0
            if isinstance(data, dict):
                qtd = int(data.get(key, 0) or 0)
            total += d.valor * Decimal(qtd)
        return total.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    def _recompute_all(self):
        caixa_atual = self.caixa_var.get() or "01"

        # Atualiza subtotais da UI com base no que está nos entries
        for d in DENOMS:
            key = str(d.valor)
            raw = (self.qtd_vars[key].get() or "0").strip()
            qtd = int(raw) if raw.isdigit() else 0
            sub = (d.valor * Decimal(qtd)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
            self.subtotal_labels[key].config(text=f"R$ {_format_money_ptbr(sub)}")

        total_atual = self._sum_caixa(caixa_atual)
        total_01 = self._sum_caixa("01")
        total_02 = self._sum_caixa("02")
        total_geral = (total_01 + total_02).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

        self.lbl_caixa_total.config(text=f"Caixa atual: R$ {_format_money_ptbr(total_atual)}")
        self.lbl_caixa01_total.config(text=f"Caixa 01: R$ {_format_money_ptbr(total_01)}")
        self.lbl_caixa02_total.config(text=f"Caixa 02: R$ {_format_money_ptbr(total_02)}")
        self.lbl_total_geral.config(text=f"Total geral: R$ {_format_money_ptbr(total_geral)}")

    def _clear_current_caixa(self):
        caixa = self.caixa_var.get() or "01"
        if not messagebox.askyesno("Confirmar", f"Limpar todas as quantidades do Caixa {caixa}?"):
            return

        for d in DENOMS:
            key = str(d.valor)
            self.qtd_vars[key].set("0")

        self._persist_caixa(caixa)
        self._recompute_all()

    def _clear_all(self):
        if not messagebox.askyesno("Confirmar", "Limpar Caixa 01 e Caixa 02?"):
            return

        self.app.dinheiro_state = {"caixa_atual": "01", "caixas": {"01": {}, "02": {}}}
        self.caixa_var.set("01")
        self._load_caixa_into_ui("01")
        self._persist_caixa("01")
        self._recompute_all()
