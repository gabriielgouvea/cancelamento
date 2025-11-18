# -*- coding: utf-8 -*-

"""
Arquivo: main.py
Descrição: Este é o arquivo principal que executa o aplicativo.
(v5.0.0 - Versão Oficial. Aba 'Achados' desabilitada)
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
# Correção v5.1.15: Importa ToastNotification do local correto
from ttkbootstrap.widgets import DateEntry, ToastNotification
# Importa o ScrolledFrame (ainda é usado pela ComissaoView e FolgasView)
from ttkbootstrap.widgets.scrolled import ScrolledFrame 
from tkinter import messagebox, Toplevel, Entry, Button, StringVar, \
    PhotoImage, Listbox, filedialog, END, ANCHOR
# --- NOVA IMPORTAÇÃO ---
from tkinter import ttk as standard_ttk 
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import os
import sys # <-- IMPORTADO SYS
import requests
import webbrowser
import platform
import csv
import traceback
import multiprocessing as mp # <-- Importado para a câmera

# --- CORREÇÃO DE PATH ---
# Adiciona o diretório atual ao path do Python
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(SCRIPT_PATH)
# --- FIM DA CORREÇÃO ---

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
# Importamos mas não vamos usar:
from view_achados import AchadosView 
from view_developer import DeveloperView

# --- Importa as Funções de Utilidade ---
from app_utils import formatar_data

import shutil

# --- Variáveis Globais e Constantes ---
APP_VERSION = "5.0.0" # <-- MUDANÇA 1: Versão alterada
VERSION_URL = "https://raw.githubusercontent.com/gabriielgouvea/veritas/main/version.json"

# O SCRIPT_PATH já foi definido lá em cima
DATA_FOLDER_PATH = os.path.join(SCRIPT_PATH, "data") # Pasta para todos os dados

PROFILE_PIC_SIZE = (96, 96)
ICON_SIZE = (22, 22)
LOGO_MARCA_SIZE = (150, 150) # Tamanho para logos de marcas

# --- FUNÇÕES AUXILIARES (APENAS as que o App usa) ---
def check_for_updates():
    try:
        response = requests.get(VERSION_URL, timeout=10); response.raise_for_status()
        online_data = response.json(); online_version = online_data["version"]; download_url = online_data["download_url"]
        if online_version > APP_VERSION:
            msg = f"Uma nova versão ({online_version}) está disponível!\n\nA sua versão atual é {APP_VERSION}.\n\nDeseja ir para a página de download?"
            if messagebox.askyesno("Atualização Disponível", msg): webbrowser.open(download_url)
        else: messagebox.showinfo("Verificar Atualizações", "Você já está com a versão mais recente do programa.")
    except Exception as e: messagebox.showerror("Erro de Conexão", f"Não foi possível verificar as atualizações.\nVerifique sua conexão com a internet.\n\nErro: {e}")


# --- CLASSE PRINCIPAL DA APLICAÇÃO ---

class App(ttk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- Conectar ao Firebase ---
        self.firebase_connected = fm.init_firebase()
        if not self.firebase_connected:
            self.destroy()
            return

        # --- Variáveis de Estilo ---
        self.FONT_MAIN = ("Helvetica", 11)
        self.FONT_BOLD = ("Helvetica", 11, "bold")
        self.FONT_TITLE = ("Helvetica", 18, "bold")
        self.FONT_TITLE_LOGIN = ("Helvetica", 32, "bold")
        self.FONT_SMALL = ("Helvetica", 9)

        self.COLOR_SIDEBAR_LIGHT = "#ffffff"
        self.COLOR_BTN_HOVER_LIGHT = "#f0f0f0"
        self.COLOR_BTN_SELECTED_LIGHT = "#e0eafb"
        self.COLOR_TEXT_LIGHT = "#212529"

        # --- Configuração da Janela ---
        self.title(f"Veritas | Sistema de Gestão v{APP_VERSION}") # <-- Versão atualizada aqui
        self.state('zoomed')
        self.resizable(True, True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Disponibiliza as constantes para as views
        self.PROFILE_PIC_SIZE = PROFILE_PIC_SIZE
        self.LOGO_MARCA_SIZE = LOGO_MARCA_SIZE 
        self.DATA_FOLDER_PATH = DATA_FOLDER_PATH

        # --- Carregar Dados dos Consultores ---
        self.lista_completa_consultores = fm.carregar_consultores()
        self.nomes_consultores = [c['nome'] for c in self.lista_completa_consultores]
        
        self.consultor_logado_data = {}
        
        # Readicionando a lista que "Comissão" e "Folgas" usam
        self.tracked_scrolled_frames = []

        # --- Carregar Imagens ---
        self.load_images()

        # --- Criar Estilos Customizados ---
        self.create_custom_styles()

        # --- SIDEBAR (Menu) ---
        self.sidebar_frame = ttk.Frame(self, style='Sidebar.TFrame', width=300)
        self.sidebar_frame.grid(row=0, column=0, sticky="ns")
        self.sidebar_frame.grid_propagate(False)

        # --- ÁREA DE CONTEÚDO PRINCIPAL ---
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # --- WIDGETS DA SIDEBAR ---
        self.create_sidebar_widgets() 

        # --- FOOTER ---
        footer_frame = ttk.Frame(self)
        footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.footer_label = ttk.Label(footer_frame, text="     Desenvolvido por Gabriel Gouvêa com seus parceiros GPT & Gemini 🤖", style='secondary.TLabel')
        self.footer_label.pack(fill='x')

        # --- Iniciar na Tela de Login ---
        self.show_login_view() 
        self.style.theme_use('flatly')


    def load_images(self):
        """Carrega todas as imagens e ícones."""
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

        try:
            self.icon_simulador = ImageTk.PhotoImage(Image.open(os.path.join(DATA_FOLDER_PATH, "calculator.png")).resize(ICON_SIZE))
            self.icon_comissao = ImageTk.PhotoImage(Image.open(os.path.join(DATA_FOLDER_PATH, "commission.png")).resize(ICON_SIZE))
            self.icon_folgas = ImageTk.PhotoImage(Image.open(os.path.join(DATA_FOLDER_PATH, "days_off.png")).resize(ICON_SIZE))
            self.icon_updates = ImageTk.PhotoImage(Image.open(os.path.join(DATA_FOLDER_PATH, "updates.png")).resize(ICON_SIZE))
            self.icon_developer = ImageTk.PhotoImage(Image.open(os.path.join(DATA_FOLDER_PATH, "developer.png")).resize(ICON_SIZE))
            self.icon_liberacoes = ImageTk.PhotoImage(Image.open(os.path.join(DATA_FOLDER_PATH, "entries.png")).resize(ICON_SIZE))
            self.icon_lostfound = ImageTk.PhotoImage(Image.open(os.path.join(DATA_FOLDER_PATH, "lost_found.png")).resize(ICON_SIZE))
        except Exception as e:
            messagebox.showerror("Erro ao Carregar Ícones", f"Não foi possível carregar alguns ícones da pasta 'data'.\n\nErro: {e}")
            self.icon_simulador = self.icon_comissao = self.icon_folgas = self.default_icon
            self.icon_updates = self.icon_developer = self.icon_liberacoes = self.default_icon
            self.icon_lostfound = self.default_icon

        try:
            img_logo_original = Image.open(os.path.join(DATA_FOLDER_PATH, "logo_completa.png"))
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
        """Carrega e aplica a foto de perfil do consultor, agora circular."""
        try:
            path_completo = os.path.join(DATA_FOLDER_PATH, foto_path)
            if not os.path.exists(path_completo) or not foto_path:
                placeholder_path = os.path.join(DATA_FOLDER_PATH, "default_profile.png")
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

        if is_dev_preview:
            self.dev_preview_photo_tk = loaded_photo
        else:
            self.profile_photo = loaded_photo
            if hasattr(self, 'profile_pic_label') and self.profile_pic_label.winfo_exists():
                self.profile_pic_label.config(image=self.profile_photo)
    
    def load_image_no_circular(self, foto_path, size=LOGO_MARCA_SIZE, is_dev_preview=False, is_marca_logo=False):
        """Carrega uma imagem (logo) sem a máscara circular, apenas redimensiona."""
        
        if not foto_path:
            loaded_photo = self.default_logo_photo
        else: 
            try:
                path_completo = os.path.join(DATA_FOLDER_PATH, foto_path)
                if not os.path.exists(path_completo):
                    raise FileNotFoundError

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

        if is_dev_preview: 
            self.dev_preview_logo_tk = loaded_photo
        elif is_marca_logo: 
            self.marca_logo_tk = loaded_photo

    def fix_image_rotation(self, img):
        """Lê os dados EXIF de uma imagem e a rotaciona corretamente."""
        try:
            exif = piexif.load(img.info['exif'])
            orientation = exif['0th'][piexif.ImageIFD.Orientation]
        except (KeyError, AttributeError, TypeError, ValueError):
            orientation = 1
        if orientation == 3: img = img.rotate(180, expand=True)
        elif orientation == 6: img = img.rotate(270, expand=True)
        elif orientation == 8: img = img.rotate(90, expand=True)
        return img


    def create_custom_styles(self):
        """Cria os estilos customizados para os botões da sidebar."""
        style = self.style
        style.configure('Sidebar.TFrame', background=self.COLOR_SIDEBAR_LIGHT)
        style.configure('Sidebar.TLabel', background=self.COLOR_SIDEBAR_LIGHT, foreground=self.COLOR_TEXT_LIGHT, font=self.FONT_BOLD)
        style.configure('Nav.Toolbutton',
                            background=self.COLOR_SIDEBAR_LIGHT,
                            foreground=self.COLOR_TEXT_LIGHT,
                            anchor='w', compound='left', padding=(15, 10),
                            font=self.FONT_MAIN, borderwidth=0)
        style.map('Nav.Toolbutton',
                  background=[('active', self.COLOR_BTN_HOVER_LIGHT),
                              ('selected', self.COLOR_BTN_SELECTED_LIGHT)],
                  foreground=[('selected', self.COLOR_TEXT_LIGHT)])

    def create_nav_button(self, parent, row, text, value, icon, cmd):
        """Função helper para criar um botão de navegação da sidebar."""
        btn = ttk.Radiobutton(parent,
                                text=text,
                                image=icon,
                                variable=self.nav_var,
                                value=value,
                                command=cmd,
                                style='Nav.Toolbutton')
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        self.nav_buttons[value] = btn

    def create_sidebar_widgets(self):
        """Cria todos os widgets dentro da sidebar."""
        self.profile_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        self.profile_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.profile_frame.grid_columnconfigure(0, weight=1)

        self.profile_pic_label = ttk.Label(self.profile_frame, image=self.profile_photo, background=self.COLOR_SIDEBAR_LIGHT)
        self.profile_pic_label.grid(row=0, column=0, pady=(0, 10))

        self.consultant_label = ttk.Label(self.profile_frame, text="Bem-vindo", style='Sidebar.TLabel', font=self.FONT_BOLD)
        self.consultant_label.grid(row=1, column=0, pady=(0, 5))

        self.trocar_consultor_button = ttk.Button(self.profile_frame, text="Fazer Login",
                                                 command=lambda: self.show_login_view(force_dev_login=False),
                                                 style='Link.TButton')
        self.trocar_consultor_button.grid(row=2, column=0, pady=(0, 10))

        ttk.Separator(self.sidebar_frame).grid(row=1, column=0, sticky='ew', padx=10, pady=10)

        self.nav_var = StringVar()
        self.nav_buttons = {}

        self.create_nav_button(self.sidebar_frame, 2, "Simulador", "simulador", self.icon_simulador, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 3, "Calculadora Comissão", "comissao", self.icon_comissao, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 4, "Folgas", "folgas", self.icon_folgas, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 5, "Liberações", "liberacoes", self.icon_liberacoes, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 6, "Achados e Perdidos", "achados", self.icon_lostfound, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 7, "Área do Desenvolvedor", "developer", self.icon_developer, self.on_nav_select)
        self.create_nav_button(self.sidebar_frame, 8, "Verificar Atualizações", "updates", self.icon_updates, self.on_nav_select)
        
        self.sidebar_frame.grid_rowconfigure(9, weight=1) 
        ttk.Separator(self.sidebar_frame).grid(row=10, column=0, sticky='sew', padx=10, pady=10) 

    def on_nav_select(self):
        """Chamado quando um botão de navegação é clicado."""
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
            self._last_selected_nav = view_name # Guarda a última seleção válida

    def show_toast(self, title, message, bootstyle='success'):
        """Mostra uma notificação Toast."""
        toast = ToastNotification(title=title, message=message, duration=3000, bootstyle=bootstyle, position=(20, 20, 'se'))
        toast.show_toast()

    def show_view(self, view_name):
        """
        Limpa o frame principal e carrega a nova 'tela'.
        """
        
        # 1. Destrói todos os widgets
        for widget in self.main_frame.winfo_children():
            try:
                # Tenta desligar a câmera se for a AchadosView
                if hasattr(widget, 'view_instance') and hasattr(widget.view_instance, 'on_close'):
                    widget.view_instance.on_close()
                widget.destroy()
            except Exception as e:
                pass 
        
        # 2. Cria a nova tela (View)
        view = None # Inicializa
        if view_name == "simulador":
            view = SimuladorView(self, self.main_frame)
        
        elif view_name == "comissao":
            view = ComissaoView(self, self.main_frame)
        
        elif view_name == "folgas":
            view = FolgasView(self, self.main_frame)
            
        elif view_name == "liberacoes":
            view = LiberacoesView(self, self.main_frame)
        
        # --- ***** MUDANÇA 2: Aba "Achados" ***** ---
        elif view_name == "achados":
            # Em vez de carregar a View, mostra a mensagem
            frame_placeholder = ttk.Frame(self.main_frame)
            frame_placeholder.pack(expand=True)
            ttk.Label(frame_placeholder, text="Em Desenvolvimento", 
                      font=self.FONT_TITLE, style="secondary.TLabel").pack()
            # view = AchadosView(self, self.main_frame) # Linha original comentada
        # --- ***** FIM DA MUDANÇA 2 ***** ---
            
        elif view_name == "developer_area":
            view = DeveloperView(self, self.main_frame)
        
        # Armazena a instância da view no próprio frame
        if view is not None and self.main_frame.winfo_children():
             self.main_frame.winfo_children()[-1].view_instance = view


    def show_login_view(self, force_dev_login=False):
        """Mostra a tela de login, escondendo a sidebar."""
        self.sidebar_frame.grid_remove()
        
        # 1. Agora destrói todos os widgets
        for widget in self.main_frame.winfo_children():
            try:
                # Tenta desligar a câmera se for a AchadosView
                if hasattr(widget, 'view_instance') and hasattr(widget.view_instance, 'on_close'):
                    widget.view_instance.on_close()
                widget.destroy()
            except Exception:
                pass
            
        login_container = ttk.Frame(self.main_frame)
        login_container.pack(expand=True)

        if hasattr(self, 'logo_login') and self.logo_login:
            ttk.Label(login_container, image=self.logo_login).pack(pady=(0, 25))
        else:
            ttk.Label(login_container, text="Sistema Veritas", font=self.FONT_TITLE_LOGIN).pack(pady=(0, 25))

        # Recarrega os consultores para garantir
        self.lista_completa_consultores = fm.carregar_consultores()
        self.nomes_consultores = [c['nome'] for c in self.lista_completa_consultores]
        
        if not self.lista_completa_consultores or force_dev_login:
            ttk.Label(login_container, text="Nenhum consultor cadastrado.", font=self.FONT_MAIN).pack(pady=(0, 10))
            ttk.Label(login_container, text="Acesse a Área do Desenvolvedor para começar.", font=self.FONT_MAIN).pack(pady=(0, 15))
            
            def on_dev_login_forced():
                pin_ok = self.show_developer_login(force_pin=True, pin_correto="8274")
                if pin_ok:
                    self.sidebar_frame.grid()
                    self.nav_var.set("developer")
                    self._last_selected_nav = "developer_area"
                    self.show_view("developer_area")
            
            ttk.Button(login_container, text="Acessar Área do Desenvolvedor", 
                       command=on_dev_login_forced, 
                       style='primary.TButton', width=35).pack(pady=10, ipady=5)
            return
            
        # Login normal
        form_frame = ttk.Frame(login_container)
        form_frame.pack(pady=10)

        ttk.Label(form_frame, text="Selecione ou digite seu nome:", font=self.FONT_MAIN).pack(anchor='w')

        self.combo_consultor_login = ttk.Combobox(form_frame, values=self.nomes_consultores, width=35, font=self.FONT_MAIN, state="readonly")
        self.combo_consultor_login.pack(pady=(5, 15))
        self.combo_consultor_login.set("") 
        
        def on_login():
            consultor_selecionado = self.combo_consultor_login.get()
            if not consultor_selecionado:
                messagebox.showwarning("Atenção", "Por favor, selecione um consultor para continuar."); return

            if consultor_selecionado not in self.nomes_consultores:
                 messagebox.showwarning("Consultor Inválido", "O nome digitado não está na lista de consultores.")
                 return

            self.consultor_logado_data = next((c for c in self.lista_completa_consultores if c['nome'] == consultor_selecionado), None)

            if not self.consultor_logado_data:
                messagebox.showerror("Erro", "Não foi possível encontrar os dados do consultor.")
                return

            self.consultant_label.config(text=self.consultor_logado_data['nome'])
            self.load_profile_picture(self.consultor_logado_data['foto_path'])
            self.trocar_consultor_button.config(text="Trocar Consultor")

            self.sidebar_frame.grid()
            self.nav_var.set("simulador")
            self._last_selected_nav = "simulador"
            self.show_view("simulador")

        ttk.Button(form_frame, text="Entrar", command=on_login, style='success.TButton', width=35, bootstyle="success-solid").pack(pady=10, ipady=5)

    def _center_popup(self, popup, width, height):
        """Função utilitária para centralizar popups."""
        self.update_idletasks()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        pos_x = main_x + (main_width // 2) - (width // 2)
        pos_y = main_y + (main_height // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()

    def show_developer_login(self, force_pin=False, pin_correto="8274"):
        """
        Mostra um popup para o login na área do desenvolvedor.
        O 'pin_correto' agora é um parâmetro.
        """
        
        self.pin_success = False

        popup = Toplevel(self)
        popup.title("Área do Desenvolvedor - Login")
        popup_width = 350
        popup_height = 180
        self._center_popup(popup, popup_width, popup_height)

        container = ttk.Frame(popup, padding=20)
        container.pack(fill='both', expand=True)

        if force_pin:
             ttk.Label(container, text="Digite o PIN de Administrador:", font=self.FONT_MAIN).pack(pady=(0, 10))
        else:
             ttk.Label(container, text="Digite o PIN para acessar a Área do Desenvolvedor:", font=self.FONT_MAIN).pack(pady=(0, 10))

        pin_entry_var = StringVar()
        pin_entry = ttk.Entry(container, width=20, show="*", textvariable=pin_entry_var)
        pin_entry.pack(pady=5)
        pin_entry.focus_set()

        def verify_pin():
            if pin_entry_var.get() == pin_correto:
                self.pin_success = True
                popup.destroy()
            else:
                messagebox.showerror("PIN Inválido", "PIN incorreto. Acesso negado.", parent=popup)
                pin_entry_var.set("")
                pin_entry.focus_set()

        ttk.Button(container, text="Acessar", command=verify_pin, style='success.TButton').pack(pady=10)
        popup.bind("<Return>", lambda event: verify_pin())
        self.wait_window(popup)

        return self.pin_success

# --- Bloco Principal ---
if __name__ == "__main__":
    # --- Adiciona suporte a multiprocessing no PyInstaller ---
    try:
        mp.freeze_support()
    except:
        pass
    # --- Fim da adição ---
    
    app = App(themename="flatly")
    
    # Se a conexão falhou, o __init__ terá retornado
    if getattr(app, 'firebase_connected', False):
        app.mainloop()
    else:
        print("Falha ao iniciar o app (provável erro de Firebase). Fechando.")