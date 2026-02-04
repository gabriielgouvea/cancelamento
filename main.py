# -*- coding: utf-8 -*-

"""
Arquivo: main.py
Descrição: Este é o arquivo principal que executa o aplicativo.
(v5.0.2 - Com Segurança de PIN no Login + Layout Original)
"""

import ttkbootstrap as ttk
from ttkbootstrap.widgets import DateEntry
from ttkbootstrap.toast import ToastNotification
from tkinter import messagebox, Toplevel, Entry, Button, StringVar, \
    PhotoImage, Listbox, filedialog, END, ANCHOR
from tkinter import ttk as standard_ttk 
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import os
import sys 
import requests
import webbrowser
import platform
import csv
import traceback
import multiprocessing as mp 
import threading
import html
import random

import paths

# --- PATHS (DEV x EXECUTÁVEL) ---
SCRIPT_PATH = paths.get_exe_dir()
sys.path.append(SCRIPT_PATH)

try:
    from PIL import Image, ImageTk, ImageDraw, ImageOps, ImageFont
    import piexif
except ImportError:
    messagebox.showerror("Erro de Dependência", "Pillow e Piexif são necessários. Rode 'pip install Pillow piexif'")

# --- Importa o gerenciador do Firebase ---
try:
    import firebase_manager as fm
except ImportError as e:
    messagebox.showerror("Erro de Arquivo", f"Arquivo 'firebase_manager.py' não encontrado.\n\nDetalhe: {e}")
    sys.exit()

# --- Importa as novas Views (Telas) ---
from view_simulador import SimuladorView
from view_comissao import ComissaoView
from view_folgas import FolgasView
from view_liberacoes import LiberacoesView
from view_achados import AchadosView 
from view_developer import DeveloperView
from view_notinhas import NotinhasView
from view_dinheiro import DinheiroView

from app_utils import formatar_data

import shutil

# --- Variáveis Globais e Constantes ---
APP_VERSION = "5.0.7"
VERSION_URL = "https://raw.githubusercontent.com/gabriielgouvea/veritas/main/version.json"
RESOURCE_DATA_FOLDER_PATH = paths.get_resource_path("data")
USER_DATA_FOLDER_PATH = paths.get_user_data_dir()
DATA_FOLDER_PATH = USER_DATA_FOLDER_PATH
PROFILE_PIC_SIZE = (96, 96)
ICON_SIZE = (22, 22)
LOGO_MARCA_SIZE = (150, 150)

# --- FUNÇÕES AUXILIARES ---
def check_for_updates():
    try:
        response = requests.get(VERSION_URL, timeout=10); response.raise_for_status()

        online_data = response.json(); online_version = str(online_data["version"]); download_url = str(online_data["download_url"])

        def _parse_version(v: str):
            parts = [p for p in (v or "").strip().split('.') if p != ""]
            nums = []
            for p in parts:
                try:
                    nums.append(int(p))
                except ValueError:
                    nums.append(0)
            return tuple(nums)

        if _parse_version(online_version) > _parse_version(APP_VERSION):
            msg = f"Uma nova versão ({online_version}) está disponível!\n\nA sua versão atual é {APP_VERSION}.\n\nDeseja ir para a página de download?"
            if messagebox.askyesno("Atualização Disponível", msg): webbrowser.open(download_url)
        else: messagebox.showinfo("Verificar Atualizações", "Você já está com a versão mais recente do programa.")
    except Exception as e: messagebox.showerror("Erro de Conexão", f"Não foi possível verificar as atualizações.\nVerifique sua conexão com a internet.\n\nErro: {e}")


class App(ttk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.firebase_connected = fm.init_firebase()
        if not self.firebase_connected:
            # Se não conectou, tenta permitir modo offline (sem nuvem)
            try:
                offline = getattr(fm, 'is_offline_mode', lambda: True)()
                if offline:
                    detalhe = (getattr(fm, 'get_last_init_error', lambda: None)() or '').strip()
                    detalhe_msg = f"\n\n{detalhe}" if detalhe else ""
                    msg = (
                        "Não foi possível conectar ao Firebase (chave ausente/erro de conexão).\n\n"
                        "Deseja iniciar em MODO OFFLINE (sem nuvem)?\n\n"
                        "- Login e Folgas usam arquivos locais em 'data/'\n"
                        "- Recursos que dependem da nuvem podem ficar indisponíveis"
                        f"{detalhe_msg}"
                    )
                    if not messagebox.askyesno("Firebase indisponível", msg):
                        self.destroy()
                        return
                else:
                    self.destroy()
                    return
            except Exception:
                self.destroy()
                return

        self.FONT_MAIN = ("Helvetica", 11)
        self.FONT_BOLD = ("Helvetica", 11, "bold")
        self.FONT_TITLE = ("Helvetica", 18, "bold")
        self.FONT_TITLE_LOGIN = ("Helvetica", 32, "bold")
        self.FONT_SMALL = ("Helvetica", 9)

        self.COLOR_SIDEBAR_LIGHT = "#ffffff"
        self.COLOR_BTN_HOVER_LIGHT = "#f0f0f0"
        self.COLOR_BTN_SELECTED_LIGHT = "#e0eafb"
        self.COLOR_TEXT_LIGHT = "#212529"

        self.title(f"Veritas | Sistema de Gestão v{APP_VERSION}") 
        self.state('zoomed')
        self.resizable(True, True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.PROFILE_PIC_SIZE = PROFILE_PIC_SIZE
        self.LOGO_MARCA_SIZE = LOGO_MARCA_SIZE 
        self.DATA_FOLDER_PATH = DATA_FOLDER_PATH
        self.RESOURCE_DATA_FOLDER_PATH = RESOURCE_DATA_FOLDER_PATH

        self.lista_completa_consultores = fm.carregar_consultores()
        self.nomes_consultores = [c['nome'] for c in self.lista_completa_consultores]
        
        self.consultor_logado_data = {}
        self.tracked_scrolled_frames = []
        self.current_view = None
        self.notinhas_state = {"tipo": "Crédito", "lancamentos": []}
        self.dinheiro_state = {"caixa_atual": "01", "caixas": {"01": {}, "02": {}}}

        # Cache do fato inútil (evita múltiplas chamadas no mesmo dia)
        self._piada_cache = None
        self._ultima_piada_texto = self._carregar_ultima_piada_local()

        self.load_images()
        self.create_custom_styles()

        self.sidebar_frame = ttk.Frame(self, style='Sidebar.TFrame', width=300)
        self.sidebar_frame.grid(row=0, column=0, sticky="ns")
        self.sidebar_frame.grid_propagate(False)

        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.create_sidebar_widgets() 
        
        footer_frame = ttk.Frame(self)
        footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.footer_label = ttk.Label(footer_frame, text="     Desenvolvido por Gabriel Gouvêa com seus parceiros GPT & Gemini 🤖", style='secondary.TLabel')
        self.footer_label.pack(fill='x')

        self.show_login_view() 
        self.style.theme_use('flatly')

    def load_images(self):
        placeholder_img = Image.new('RGBA', PROFILE_PIC_SIZE, (0,0,0,0))
        draw = ImageDraw.Draw(placeholder_img)
        draw.ellipse((0, 0, PROFILE_PIC_SIZE[0], PROFILE_PIC_SIZE[1]), fill='#cccccc')
        self.default_profile_photo = ImageTk.PhotoImage(placeholder_img)
        self.dev_preview_photo_tk = self.default_profile_photo
        
        placeholder_logo = Image.new('RGBA', LOGO_MARCA_SIZE, (0,0,0,0))
        draw = ImageDraw.Draw(placeholder_logo)
        draw.rectangle((0, 0, LOGO_MARCA_SIZE[0], LOGO_MARCA_SIZE[1]), fill='#eeeeee')
        self.default_logo_photo = ImageTk.PhotoImage(placeholder_logo)
        self.dev_preview_logo_tk = self.default_logo_photo

        self.default_icon = ImageTk.PhotoImage(Image.new('RGBA', ICON_SIZE, (0,0,0,0)))
        self.profile_photo = self.default_profile_photo

        def _data_file(filename: str) -> str:
            return paths.resolve_data_file(filename)

        try:
            self.icon_simulador = ImageTk.PhotoImage(Image.open(_data_file("calculator.png")).resize(ICON_SIZE))
            self.icon_comissao = ImageTk.PhotoImage(Image.open(_data_file("commission.png")).resize(ICON_SIZE))
            self.icon_folgas = ImageTk.PhotoImage(Image.open(_data_file("days_off.png")).resize(ICON_SIZE))
            self.icon_updates = ImageTk.PhotoImage(Image.open(_data_file("updates.png")).resize(ICON_SIZE))
            self.icon_developer = ImageTk.PhotoImage(Image.open(_data_file("developer.png")).resize(ICON_SIZE))
            self.icon_liberacoes = ImageTk.PhotoImage(Image.open(_data_file("entries.png")).resize(ICON_SIZE))
            self.icon_lostfound = ImageTk.PhotoImage(Image.open(_data_file("lost_found.png")).resize(ICON_SIZE))
            self.icon_notinhas = ImageTk.PhotoImage(Image.open(_data_file("notinhas.png")).resize(ICON_SIZE))
            self.icon_dinheiro = ImageTk.PhotoImage(Image.open(_data_file("money.png")).resize(ICON_SIZE))
        except Exception as e:
            messagebox.showerror("Erro ao Carregar Ícones", f"Não foi possível carregar alguns ícones da pasta 'data'.\n\nErro: {e}")
            self.icon_simulador = self.icon_comissao = self.icon_folgas = self.default_icon
            self.icon_updates = self.icon_developer = self.icon_liberacoes = self.default_icon
            self.icon_lostfound = self.default_icon
            self.icon_notinhas = self.default_icon
            self.icon_dinheiro = self.default_icon

        try:
            img_logo_original = Image.open(_data_file("logo_completa.png"))
            original_width, original_height = img_logo_original.size
            max_width = 500
            ratio = max_width / float(original_width)
            new_height = int(float(original_height) * float(ratio))
            img_logo_resized = img_logo_original.resize((max_width, new_height), Image.Resampling.LANCZOS)
            self.logo_login = ImageTk.PhotoImage(img_logo_resized)
        except Exception as e:
            print(f"AVISO: Não foi possível carregar a logo_completa.png: {e}")
            self.logo_login = None

    def load_profile_picture(self, foto_path, size=PROFILE_PIC_SIZE, is_dev_preview=False):
        try:
            path_completo = paths.resolve_data_file(foto_path) if foto_path else ""
            if not os.path.exists(path_completo) or not foto_path:
                placeholder_path = paths.resolve_data_file("default_profile.png")
                img_profile = Image.open(placeholder_path)
            else:
                img_profile = Image.open(path_completo)

            img_profile = self.fix_image_rotation(img_profile)
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size[0], size[1]), fill=255)
            img_resized = ImageOps.fit(img_profile, size, Image.Resampling.LANCZOS)
            img_circular = Image.new("RGBA", size, (0,0,0,0))
            img_circular.paste(img_resized, (0, 0), mask)
            loaded_photo = ImageTk.PhotoImage(img_circular)
        except Exception as e:
            print(f"Erro ao carregar a foto de perfil {foto_path}: {e}")
            placeholder_img = Image.new('RGBA', PROFILE_PIC_SIZE, (0,0,0,0))
            draw = ImageDraw.Draw(placeholder_img)
            draw.ellipse((0, 0, PROFILE_PIC_SIZE[0], PROFILE_PIC_SIZE[1]), fill='#cccccc')
            loaded_photo = ImageTk.PhotoImage(placeholder_img)

        if is_dev_preview: self.dev_preview_photo_tk = loaded_photo
        else:
            self.profile_photo = loaded_photo
            if hasattr(self, 'profile_pic_label') and self.profile_pic_label.winfo_exists():
                self.profile_pic_label.config(image=self.profile_photo)
    
    def load_image_no_circular(self, foto_path, size=LOGO_MARCA_SIZE, is_dev_preview=False, is_marca_logo=False):
        if not foto_path: loaded_photo = self.default_logo_photo
        else: 
            try:
                path_completo = paths.resolve_data_file(foto_path)
                if not os.path.exists(path_completo): raise FileNotFoundError
                img_logo = Image.open(path_completo)
                img_logo = self.fix_image_rotation(img_logo)
                img_logo.thumbnail(size, Image.Resampling.LANCZOS)
                img_final = Image.new("RGBA", size, (0,0,0,0))
                offset = ((size[0] - img_logo.width) // 2, (size[1] - img_logo.height) // 2)
                img_final.paste(img_logo, offset)
                loaded_photo = ImageTk.PhotoImage(img_final)
            except Exception as e:
                print(f"Erro ao carregar logo {foto_path}: {e}")
                loaded_photo = self.default_logo_photo

        if is_dev_preview: self.dev_preview_logo_tk = loaded_photo
        elif is_marca_logo: self.marca_logo_tk = loaded_photo

    def fix_image_rotation(self, img):
        try:
            exif = piexif.load(img.info['exif'])
            orientation = exif['0th'][piexif.ImageIFD.Orientation]
        except (KeyError, AttributeError, TypeError, ValueError): orientation = 1
        if orientation == 3: img = img.rotate(180, expand=True)
        elif orientation == 6: img = img.rotate(270, expand=True)
        elif orientation == 8: img = img.rotate(90, expand=True)
        return img

    def create_custom_styles(self):
        style = self.style
        style.configure('Sidebar.TFrame', background=self.COLOR_SIDEBAR_LIGHT)
        style.configure('Sidebar.TLabel', background=self.COLOR_SIDEBAR_LIGHT, foreground=self.COLOR_TEXT_LIGHT, font=self.FONT_BOLD)
        style.configure('Nav.Toolbutton', background=self.COLOR_SIDEBAR_LIGHT, foreground=self.COLOR_TEXT_LIGHT, anchor='w', compound='left', padding=(15, 10), font=self.FONT_MAIN, borderwidth=0)
        style.map('Nav.Toolbutton', background=[('active', self.COLOR_BTN_HOVER_LIGHT), ('selected', self.COLOR_BTN_SELECTED_LIGHT)], foreground=[('selected', self.COLOR_TEXT_LIGHT)])

    def create_nav_button(self, parent, row, text, value, icon, cmd):
        btn = ttk.Radiobutton(parent, text=text, image=icon, variable=self.nav_var, value=value, command=cmd, style='Nav.Toolbutton')
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        self.nav_buttons[value] = btn

    def create_sidebar_widgets(self):
        self.profile_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        self.profile_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.profile_frame.grid_columnconfigure(0, weight=1)

        self.profile_pic_label = ttk.Label(self.profile_frame, image=self.profile_photo, background=self.COLOR_SIDEBAR_LIGHT)
        self.profile_pic_label.grid(row=0, column=0, pady=(0, 10))

        self.consultant_label = ttk.Label(self.profile_frame, text="Bem-vindo", style='Sidebar.TLabel', font=self.FONT_BOLD)
        self.consultant_label.grid(row=1, column=0, pady=(0, 5))

        self.trocar_consultor_button = ttk.Button(self.profile_frame, text="Fazer Login", command=lambda: self.show_login_view(force_dev_login=False), style='Link.TButton')
        self.trocar_consultor_button.grid(row=2, column=0, pady=(0, 10))

        ttk.Separator(self.sidebar_frame).grid(row=1, column=0, sticky='ew', padx=10, pady=10)

        self.nav_var = StringVar()
        self.nav_buttons = {}

        self.create_nav_button(self.sidebar_frame, 2, "Simulador", "simulador", self.icon_simulador, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 3, "Contagem Notinhas", "notinhas", self.icon_notinhas, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 4, "Contagem Dinheiro", "dinheiro", self.icon_dinheiro, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 5, "Calculadora Comissão", "comissao", self.icon_comissao, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 6, "Folgas", "folgas", self.icon_folgas, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 7, "Liberações", "liberacoes", self.icon_liberacoes, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 8, "Achados e Perdidos", "achados", self.icon_lostfound, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 9, "Área do Desenvolvedor", "developer", self.icon_developer, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 10, "Verificar Atualizações", "updates", self.icon_updates, self.on_nav_select)
        
        self.sidebar_frame.grid_rowconfigure(11, weight=1) 
        ttk.Separator(self.sidebar_frame).grid(row=12, column=0, sticky='sew', padx=10, pady=10) 

    def on_nav_select(self):
        view_name = self.nav_var.get()
        if view_name == "updates":
            check_for_updates()
            if hasattr(self, '_last_selected_nav'): self.nav_var.set(self._last_selected_nav)
            else: self.nav_var.set("")
        elif view_name == "developer":
            pin_ok = self.show_developer_login(force_pin=False, pin_correto="8274") 
            if pin_ok:
                self.show_view("developer_area")
                self._last_selected_nav = "developer_area"
            else:
                if hasattr(self, '_last_selected_nav'): self.nav_var.set(self._last_selected_nav)
                else: self.nav_var.set("")
        else:
            self.show_view(view_name)
            self._last_selected_nav = view_name 

    def show_toast(self, title, message, bootstyle='success'):
        """Mostra uma notificação Toast."""
        toast = ToastNotification(title=title, message=message, duration=3000, bootstyle=bootstyle, position=(20, 110, 'se'))
        toast.show_toast()

    def show_view(self, view_name):
        try:
            current_view = getattr(self, 'current_view', None)
            on_close = getattr(current_view, 'on_close', None)
            if callable(on_close):
                on_close()
        except Exception:
            pass

        for widget in self.main_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass
        
        view = None 
        if view_name == "simulador": view = SimuladorView(self, self.main_frame)
        elif view_name == "notinhas": view = NotinhasView(self, self.main_frame)
        elif view_name == "dinheiro": view = DinheiroView(self, self.main_frame)
        elif view_name == "comissao": view = ComissaoView(self, self.main_frame)
        elif view_name == "folgas": view = FolgasView(self, self.main_frame)
        elif view_name == "liberacoes": view = LiberacoesView(self, self.main_frame)
        elif view_name == "achados":
            frame = ttk.Frame(self.main_frame); frame.pack(expand=True)
            ttk.Label(frame, text="Em Desenvolvimento", font=self.FONT_TITLE, style="secondary.TLabel").pack()
        elif view_name == "developer_area": view = DeveloperView(self, self.main_frame)

        self.current_view = view

    def show_login_view(self, force_dev_login=False):
        self.sidebar_frame.grid_remove()
        for widget in self.main_frame.winfo_children(): widget.destroy()
        root_container = ttk.Frame(self.main_frame)
        root_container.pack(fill='both', expand=True)

        # Fato inútil do dia (API v2) - topo fixo
        top_info = ttk.Frame(root_container)
        top_info.pack(side='top', fill='x', pady=(6, 0))
        self.lbl_piada_login = ttk.Label(
            top_info,
            text="Piada: carregando...",
            style='secondary.TLabel',
            font=("Segoe UI", 8),
            wraplength=900,
            justify='center'
        )
        self.lbl_piada_login.pack(anchor='center', pady=(2, 0))
        self.lbl_piada_login.bind("<Button-1>", lambda e: self._refresh_piada())
        self._carregar_piada_async()

        # Conteúdo central do login
        login_container = ttk.Frame(root_container)
        login_container.pack(expand=True)

        if self.logo_login: ttk.Label(login_container, image=self.logo_login).pack(pady=(10, 25))
        else: ttk.Label(login_container, text="Sistema Veritas", font=self.FONT_TITLE_LOGIN).pack(pady=(10, 25))

        self.lista_completa_consultores = fm.carregar_consultores()
        self.nomes_consultores = [c['nome'] for c in self.lista_completa_consultores]
        
        if not self.lista_completa_consultores or force_dev_login:
            ttk.Label(login_container, text="Nenhum consultor cadastrado.", font=self.FONT_MAIN).pack(pady=(0, 10))
            ttk.Label(login_container, text="Acesse a Área do Desenvolvedor para começar.", font=self.FONT_MAIN).pack(pady=(0, 15))
            
            def on_dev_login_forced():
                pin_ok = self.show_developer_login(force_pin=True, pin_correto="8274")
                if pin_ok:
                    self.sidebar_frame.grid(); self.nav_var.set("developer"); self._last_selected_nav = "developer_area"; self.show_view("developer_area")
            ttk.Button(login_container, text="Acessar Área do Desenvolvedor", command=on_dev_login_forced, style='primary.TButton', width=35).pack(pady=10, ipady=5)
            return
            
        form_frame = ttk.Frame(login_container); form_frame.pack(pady=10)
        ttk.Label(form_frame, text="Selecione ou digite seu nome:", font=self.FONT_MAIN).pack(anchor='w')
        self.combo_consultor_login = ttk.Combobox(form_frame, values=self.nomes_consultores, width=35, font=self.FONT_MAIN, state="readonly")
        self.combo_consultor_login.pack(pady=(5, 15)); self.combo_consultor_login.set("") 
        
        def on_login():
            nome = self.combo_consultor_login.get()
            if not nome: messagebox.showwarning("Atenção", "Selecione um consultor."); return
            if nome not in self.nomes_consultores: messagebox.showwarning("Inválido", "Consultor não listado."); return

            # --- SEGURANÇA: PEDIR PIN NO LOGIN ---
            pins_raw = fm.carregar_pins_consultores()
            pins = pins_raw if isinstance(pins_raw, dict) else {}
            pin_correto = str(pins.get(nome, "0000"))
            
            # Se PIN for 0000, deixa passar (primeiro acesso), senão, pede
            if pin_correto != "0000":
                pin_digitado = self._popup_pedir_pin_login(nome)
                if not pin_digitado or pin_digitado != pin_correto:
                    messagebox.showerror("Acesso Negado", "PIN incorreto."); return

            self.consultor_logado_data = next((c for c in self.lista_completa_consultores if c['nome'] == nome), None)
            if not self.consultor_logado_data: messagebox.showerror("Erro", "Erro ao carregar dados."); return

            self.consultant_label.config(text=self.consultor_logado_data['nome'])
            self.load_profile_picture(self.consultor_logado_data['foto_path'])
            self.trocar_consultor_button.config(text="Trocar Consultor")
            self.sidebar_frame.grid()
            self.nav_var.set("simulador"); self._last_selected_nav = "simulador"; self.show_view("simulador")

        ttk.Button(form_frame, text="Entrar", command=on_login, style='success.TButton', width=35, bootstyle="success-solid").pack(pady=10, ipady=5)


    def _carregar_piada_async(self):
        """Busca uma piada sem travar a UI (API: https://v2.jokeapi.dev/)."""
        try:
            lbl = getattr(self, 'lbl_piada_login', None)
            if not lbl:
                return

            # Cache só para evitar chamadas repetidas durante a execução atual.
            cache = getattr(self, '_piada_cache', None)
            if isinstance(cache, dict) and cache.get('texto'):
                lbl.config(text=cache['texto'])
                return

            # Fallback imediato: mostra uma piada offline diferente enquanto tenta buscar uma nova.
            # (Evita ficar repetindo a mesma quando não há internet.)
            ultima_para_excluir = (getattr(self, '_ultima_piada_texto', None) or '').strip() or None

            def escolher_piada_offline(excluir: str | None) -> str:
                piadas = [
                    "Por que o computador foi ao médico? Porque estava com vírus.",
                    "Qual é o café mais perigoso? O ex-presso.",
                    "O que o zero disse pro oito? Belo cinto!",
                    "Por que o livro foi ao hospital? Porque tinha muitas páginas em branco.",
                    "O que a lâmpada disse para a outra? Você me ilumina.",
                    "Por que o relógio foi expulso da escola? Porque vivia atrasado.",
                    "O que a nuvem falou quando caiu? Chuva de emoção.",
                    "Por que o teclado não conta segredo? Porque tem muitas teclas.",
                    "O que o Wi‑Fi disse pro cabo? Você vive preso.",
                    "Por que a bateria estava feliz? Porque tinha energia de sobra.",
                    "Qual é o cúmulo da organização? Guardar a bagunça por ordem alfabética.",
                    "O que o mouse disse? Cliquei, logo existo.",
                    "Por que a impressora dormiu cedo? Para não dar pane amanhã.",
                    "O que a senha falou? Não me esquece.",
                    "Por que o programador levou uma escada? Para acessar níveis mais altos.",
                    "O que o calendário disse? Meu dia está contado.",
                    "Por que o celular tirou férias? Estava sem sinal.",
                    "Qual é o animal mais conectado? O bug.",
                    "O que o pendrive falou? Tô cheio de memória.",
                    "Por que a internet foi ao psicólogo? Tinha muitos nós.",
                ]

                candidatos = [p for p in piadas if p and (excluir is None or p.strip() != excluir.strip())]
                if not candidatos:
                    candidatos = piadas
                return random.choice(candidatos).strip()

            piada_offline_sugerida = escolher_piada_offline(ultima_para_excluir)
            try:
                if piada_offline_sugerida:
                    lbl.config(text=f"Piada: {piada_offline_sugerida}")
            except Exception:
                pass

            def worker():
                texto_final = "Piada: (sem conexão)"
                piada_raw = None

                def truncar(s: str, max_len: int = 220) -> str:
                    s = (s or "").strip()
                    if len(s) <= max_len:
                        return s
                    return s[: max_len - 3].rstrip() + "..."

                def parse_joke(j: dict) -> str | None:
                    if not isinstance(j, dict):
                        return None
                    if j.get('error') is True:
                        return None
                    if j.get('type') == 'single':
                        return j.get('joke')
                    if j.get('type') == 'twopart':
                        setup = j.get('setup')
                        delivery = j.get('delivery')
                        if setup and delivery:
                            return f"{setup} — {delivery}"
                    return None

                def fetch_joke(lang: str) -> str | None:
                    params = {
                        'lang': lang,
                        'safe-mode': '',
                        'blacklistFlags': 'nsfw,religious,political,racist,sexist,explicit'
                    }
                    resp = requests.get("https://v2.jokeapi.dev/joke/Any", params=params, timeout=6)
                    resp.raise_for_status()
                    data = resp.json() if resp.headers.get('Content-Type', '').startswith('application/json') else {}
                    piada = parse_joke(data)
                    if not piada:
                        return None
                    return html.unescape(str(piada).strip())

                def traduzir_en_para_pt(texto_en: str) -> str | None:
                    try:
                        tr = requests.get(
                            "https://api.mymemory.translated.net/get",
                            params={"q": texto_en, "langpair": "en|pt-br"},
                            timeout=4
                        )
                        tr.raise_for_status()
                        trj = tr.json() if tr.headers.get('Content-Type', '').startswith('application/json') else {}
                        rd = (trj or {}).get('responseData') or {}
                        traduzido = rd.get('translatedText')
                        match = rd.get('match')
                        if traduzido:
                            traduzido = html.unescape(str(traduzido).strip())
                        try:
                            if match is not None and float(match) < 0.60:
                                return None
                        except Exception:
                            pass
                        return traduzido or None
                    except Exception:
                        return None

                try:
                    # Evita repetir exatamente a última piada entre aberturas do sistema
                    ultima = (self._ultima_piada_texto or "").strip()

                    for _ in range(4):
                        piada = fetch_joke('pt')
                        original_en = None

                        if not piada:
                            piada = fetch_joke('en')
                            original_en = piada

                        if not piada:
                            continue

                        if ultima and piada.strip() == ultima:
                            continue

                        piada_raw = piada.strip()

                        if original_en:
                            traduzido = traduzir_en_para_pt(original_en)
                            if traduzido:
                                texto_final = f"Piada: {truncar(traduzido)} (orig: {truncar(original_en)})"
                            else:
                                texto_final = f"Piada (EN): {truncar(original_en)}"
                        else:
                            texto_final = f"Piada: {truncar(piada_raw)}"

                        break
                except Exception:
                    pass

                if not piada_raw:
                    try:
                        # Sem internet: usa o fallback offline (diferente do último, quando possível)
                        piada_raw = (piada_offline_sugerida or '').strip() or None
                        if piada_raw:
                            texto_final = f"Piada: {piada_raw}"
                        else:
                            texto_final = "Piada: sem conexão (clique para tentar novamente)"
                    except Exception:
                        texto_final = "Piada: sem conexão (clique para tentar novamente)"

                def apply():
                    lbl2 = getattr(self, 'lbl_piada_login', None)
                    if lbl2:
                        lbl2.config(text=texto_final)
                    self._piada_cache = {'texto': texto_final}
                    if piada_raw:
                        try:
                            self._ultima_piada_texto = piada_raw
                            self._salvar_ultima_piada_local(piada_raw)
                        except Exception:
                            pass

                try:
                    self.after(0, apply)
                except Exception:
                    pass

            threading.Thread(target=worker, daemon=True).start()
        except Exception:
            pass

    def _ultima_piada_path(self):
        try:
            base = getattr(self, 'DATA_FOLDER_PATH', None) or DATA_FOLDER_PATH
            return os.path.join(base, "ultima_piada.txt")
        except Exception:
            return os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "ultima_piada.txt")

    def _carregar_ultima_piada_local(self):
        try:
            p = self._ultima_piada_path()
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    txt = (f.read() or "").strip()
                    # Compatibilidade com versões antigas que salvavam o texto completo ("Piada: ...")
                    if txt.lower().startswith("piada:"):
                        txt = txt.split(":", 1)[1].strip()
                    if txt.lower().startswith("piada (en):"):
                        txt = txt.split(":", 1)[1].strip()
                    return txt or None
        except Exception:
            pass
        return None

    def _salvar_ultima_piada_local(self, texto: str):
        try:
            p = self._ultima_piada_path()
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(str(texto).strip())
        except Exception:
            pass

    def _refresh_piada(self):
        """Força atualizar a piada (clique no texto do topo)."""
        try:
            self._piada_cache = None
            lbl = getattr(self, 'lbl_piada_login', None)
            if lbl:
                lbl.config(text="Piada: carregando...")
            self._carregar_piada_async()
        except Exception:
            pass

    def _center_popup(self, popup, width, height):
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.resizable(False, False); popup.transient(self); popup.grab_set()

    def show_developer_login(self, force_pin=False, pin_correto="8274"):
        self.pin_success = False
        popup = Toplevel(self); popup.title("Admin"); self._center_popup(popup, 350, 180)
        container = ttk.Frame(popup, padding=20); container.pack(fill='both', expand=True)
        ttk.Label(container, text="Digite o PIN de Administrador:" if force_pin else "PIN do Desenvolvedor:", font=self.FONT_MAIN).pack(pady=(0, 10))
        pin_var = StringVar(); entry = ttk.Entry(container, width=20, show="*", textvariable=pin_var); entry.pack(pady=5); entry.focus_set()
        def verify():
            if pin_var.get() == pin_correto: self.pin_success = True; popup.destroy()
            else: messagebox.showerror("Erro", "PIN incorreto.", parent=popup); pin_var.set("")
        ttk.Button(container, text="Acessar", command=verify, style='success.TButton').pack(pady=10)
        popup.bind("<Return>", lambda e: verify()); self.wait_window(popup); return self.pin_success

    def _popup_pedir_pin_login(self, nome_usuario):
        """Pede PIN específico para login."""
        pop = Toplevel(self); pop.title("Autenticação"); self._center_popup(pop, 300, 180)
        ttk.Label(pop, text=f"Olá, {nome_usuario}", font=("Segoe UI", 10, "bold")).pack(pady=5)
        ttk.Label(pop, text="Confirme sua identidade:", font=("Segoe UI", 9)).pack()
        v = StringVar(); e = ttk.Entry(pop, textvariable=v, show="*", font=("Arial", 14), width=10); e.pack(pady=10); e.focus()
        r = None
        def ok(): nonlocal r; r=v.get(); pop.destroy()
        ttk.Button(pop, text="Confirmar", command=ok, style="success.TButton").pack(pady=5)
        pop.bind("<Return>", lambda e: ok()); self.wait_window(pop); return r

if __name__ == "__main__":
    try: mp.freeze_support()
    except: pass
    app = App(themename="flatly")
    if getattr(app, 'firebase_connected', False): app.mainloop()
    else: print("Erro Firebase.")