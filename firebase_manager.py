# -*- coding: utf-8 -*-

"""
Arquivo: firebase_manager.py
Descrição: Gerencia toda a comunicação com o Firebase (RTDB) e ImageKit.io.
(v5.7.1 - Corrige crash silencioso na inicialização)
"""

import firebase_admin
from firebase_admin import credentials, db 
from tkinter import messagebox
import os
import sys
import traceback # <-- Importado para mostrar o erro completo
import io
import json
import tempfile
from PIL import Image

import paths

# --- IMPORTAÇÃO CORRETA ---
# Só precisamos do ImageKit, nada mais
from imagekitio import ImageKit

# --- Variáveis Globais de Conexão ---
db_ref = None # Para o Realtime Database
imagekit = None # Para o ImageKit
FIREBASE_CONECTADO = False
OFFLINE_MODE = False
LAST_INIT_ERROR = None

APP_BASE_DIR = paths.get_exe_dir()

# Dados mutáveis (modo offline) devem ficar em pasta do usuário.
DATA_FOLDER_PATH = paths.get_user_data_dir()

# Credencial deve ser fornecida fora do pacote (não embutir no instalador).
DEFAULT_KEY_FILE_PATH = os.path.join(DATA_FOLDER_PATH, "firebase-key.json")
TEMP_UPLOAD_PATH = os.path.join(tempfile.gettempdir(), "veritas_temp_upload.jpg")


def _local_json_read(filename, default_value):
    # Preferir arquivo do usuário; se não existir, tenta o empacotado (somente leitura).
    path = os.path.join(DATA_FOLDER_PATH, filename)
    if not os.path.exists(path):
        bundled_path = paths.get_resource_path('data', filename)
        if os.path.exists(bundled_path):
            path = bundled_path
        else:
            return default_value
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"AVISO: Falha ao ler JSON local {path}: {e}")
        return default_value


def _local_json_write(filename, value):
    try:
        os.makedirs(DATA_FOLDER_PATH, exist_ok=True)
        path = os.path.join(DATA_FOLDER_PATH, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"AVISO: Falha ao salvar JSON local {filename}: {e}")
        return False

# --- URL DO SEU RTDB ---
DATABASE_URL = "https://sistema-veritas-default-rtdb.firebaseio.com/" 

# --- SUAS CHAVES DO IMAGEKIT ---
IMAGEKIT_PUBLIC_KEY = "public_XBK11UgP67lvAoT5ECT+uH3V7Vo="
IMAGEKIT_PRIVATE_KEY = "private_TfSk2SKzt+spb7ankn77WybmUlg="
IMAGEKIT_URL_ENDPOINT = "https://ik.imagekit.io/2ewjhonqc"


def init_firebase():
    """Conecta-se ao Realtime Database E ao ImageKit."""
    global db_ref, imagekit, FIREBASE_CONECTADO, OFFLINE_MODE, LAST_INIT_ERROR
    
    if FIREBASE_CONECTADO:
        return True

    # Permite rodar em modo offline sem Firebase via variável de ambiente.
    offline_env = (os.getenv('VERITAS_OFFLINE') or '').strip().lower()
    if offline_env in {"1", "true", "yes", "sim"}:
        OFFLINE_MODE = True
        return False

    # Ordem: variável de ambiente > pasta do usuário > (fallback) pasta ao lado do exe
    key_file_path = os.getenv('FIREBASE_KEY_PATH') or DEFAULT_KEY_FILE_PATH
    if not os.path.exists(key_file_path):
        exe_fallback = os.path.join(APP_BASE_DIR, 'data', 'firebase-key.json')
        if os.path.exists(exe_fallback):
            key_file_path = exe_fallback

    try:
        # 1. Conecta ao Firebase (RTDB)
        cred = credentials.Certificate(key_file_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': DATABASE_URL
        })
        db_ref = db.reference() # Pega a referência do Realtime Database
        
        # Testa a conexão
        db_ref.child('consultores').order_by_key().limit_to_first(1).get() 
        
        # 2. Conecta ao ImageKit
        global imagekit
        imagekit = ImageKit(
            public_key=IMAGEKIT_PUBLIC_KEY,
            private_key=IMAGEKIT_PRIVATE_KEY,
            url_endpoint=IMAGEKIT_URL_ENDPOINT
        )
        
        print("Conexão com Firebase (RTDB) e ImageKit estabelecida com sucesso!")
        FIREBASE_CONECTADO = True
        LAST_INIT_ERROR = None
        return True
        
    except ValueError:
         # Se já foi inicializado (erro comum)
        print("Firebase já foi inicializado.")
        db_ref = db.reference()
        FIREBASE_CONECTADO = True
        return True
    except FileNotFoundError:
        LAST_INIT_ERROR = (
            "Arquivo de credencial do Firebase não encontrado.\n\n"
            f"Caminho tentado:\n{key_file_path}\n\n"
            "Dica: coloque o arquivo em '%APPDATA%\\Veritas\\data\\firebase-key.json'\n"
            "(recomendado) ou em 'data/firebase-key.json' ao lado do executável\n"
            "ou defina a variável de ambiente FIREBASE_KEY_PATH."
        )
        # --- ***** CORREÇÃO ***** ---
        # MUDADO DE MESSAGEBOX PARA PRINT
        print("="*50)
        print("ERRO CRÍTICO DE FIREBASE")
        print(f"O arquivo-chave do Firebase não foi encontrado em:\n{key_file_path}")
        print("O aplicativo não pode se conectar à nuvem.")
        print("="*50)
        OFFLINE_MODE = True
        # --- ***** FIM DA CORREÇÃO ***** ---
        return False
    except Exception as e:
        LAST_INIT_ERROR = (
            "Não foi possível conectar ao Firebase.\n\n"
            f"Detalhe: {e}"
        )
        # --- ***** CORREÇÃO ***** ---
        # MUDADO DE MESSAGEBOX PARA PRINT
        print("="*50)
        print("ERRO DE CONEXÃO FIREBASE")
        print(f"Não foi possível conectar ao Firebase:\n{e}")
        print("="*50)
        traceback.print_exc() # Imprime o traceback completo
        # --- ***** FIM DA CORREÇÃO ***** ---
        OFFLINE_MODE = True
        return False


def get_last_init_error():
    return LAST_INIT_ERROR


def is_offline_mode():
    return bool(OFFLINE_MODE)

# --- Funções de Consultores (RTDB) ---
def carregar_consultores():
    if not db_ref:
        return _local_json_read('consultores.json', [])
    try:
        ref = db_ref.child('consultores')
        data = ref.get()
        return data if data else []
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao carregar consultores: {e}")
        return []

def salvar_consultores(lista_consultores):
    if not db_ref:
        return _local_json_write('consultores.json', lista_consultores)
    try:
        ref = db_ref.child('consultores')
        ref.set(lista_consultores)
        return True
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao salvar consultores: {e}")
        return False

# --- Funções de Folgas (RTDB) ---
def carregar_folgas():
    if not db_ref:
        return _local_json_read('folgas.json', {})
    try:
        ref = db_ref.child('folgas')
        data = ref.get()
        return data if data else {}
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao carregar folgas: {e}")
        return {}

def salvar_folgas(dados_folgas):
    if not db_ref:
        return _local_json_write('folgas.json', dados_folgas)
    try:
        ref = db_ref.child('folgas')
        ref.set(dados_folgas)
        return True
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao salvar folgas: {e}")
        return False

# --- Funções de Marcas (RTDB) ---
def carregar_marcas():
    if not db_ref: return {}
    try:
        ref = db_ref.child('marcas_liberadas') 
        data = ref.get()
        return data if data else {} 
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao carregar marcas: {e}")
        return {} 

def salvar_marcas(dados_marcas):
    if not db_ref: return False
    try:
        ref = db_ref.child('marcas_liberadas')
        ref.set(dados_marcas) 
        return True
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao salvar marcas: {e}")
        return False

# --- Funções de Achados e Perdidos ---

def upload_foto_item_imagekit(imagem_pil, n_controle):
    """
    (ImageKit) Faz o upload de uma imagem (PIL) para o ImageKit.io.
    RETORNA: (url_da_imagem, file_id_da_imagem)
    MÉTODO: Salva em disco e faz upload do arquivo (Plano B).
    """
    if not imagekit:
        messagebox.showerror("Erro de Upload", "ImageKit não inicializado.")
        return None, None
        
    try:
        # 1. Salva a imagem PIL em um arquivo temporário
        imagem_pil.save(TEMP_UPLOAD_PATH, format='JPEG', quality=85)

        # 2. Prepara as opções como um OBJETO
        class OpcoesDeUpload:
            pass
            
        options = OpcoesDeUpload()
        options.folder = "achados_e_perdidos/"
        options.is_private_file = False
        
        # 3. Faz o upload abrindo o ARQUIVO salvo
        with open(TEMP_UPLOAD_PATH, "rb") as f:
            upload_response = imagekit.upload(
                file=f, # Passa o arquivo aberto
                file_name=f"item_{n_controle}.jpg",
                options=options
            )
        
        # 4. Pega a URL e o FILE_ID
        url_da_imagem = upload_response.url
        file_id_da_imagem = upload_response.file_id
        
        return url_da_imagem, file_id_da_imagem # <-- RETORNA OS DOIS

    except Exception as e:
        messagebox.showerror("Erro de Upload (ImageKit)", f"Não foi possível salvar a foto no ImageKit.\n\nTraceback: {e}\n\n{traceback.format_exc()}")
        return None, None
        
    finally:
        # 5. SEMPRE apaga o arquivo temporário, mesmo se falhar
        if os.path.exists(TEMP_UPLOAD_PATH):
            try:
                os.remove(TEMP_UPLOAD_PATH)
            except Exception as e:
                print(f"AVISO: Não foi possível apagar o arquivo temporário: {e}")


def salvar_novo_item_achado(item_data):
    """
    (RTDB) Salva os dados do novo item na coleção 'achados_e_perdidos'.
    Usa o 'id_controle' como o ID do documento.
    """
    if not db_ref: return False
    try:
        id_documento = item_data['id_controle']
        # Salva os dados no Realtime Database
        ref = db_ref.child(f'achados_e_perdidos/{id_documento}')
        ref.set(item_data)
        return True
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados do item no RTDB.\n\nErro: {e}")
        return False

def carregar_itens_achados():
    """
    (RTDB) Carrega TODOS os itens da coleção 'achados_e_perdidos'.
    """
    if not db_ref: return {}
    try:
        ref = db_ref.child('achados_e_perdidos')
        data = ref.get()
        return data if data else {}
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao carregar itens de Achados e Perdidos: {e}")
        return {}

def excluir_item_achado(item_id):
    """
    (RTDB) Exclui um item da coleção 'achados_e_perdidos'
    """
    if not db_ref: return False
    try:
        ref = db_ref.child(f'achados_e_perdidos/{item_id}')
        ref.delete()
        return True
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao excluir item do RTDB: {e}")
        return False

def excluir_foto_item_imagekit(file_id):
    """
    (ImageKit) Exclui um arquivo de foto do ImageKit usando seu file_id.
    """
    if not imagekit: return False
    try:
        imagekit.delete_file(file_id)
        return True
    except Exception as e:
        # Não mostra um erro, só avisa no console
        print(f"AVISO: Falha ao excluir foto do ImageKit (ID: {file_id}). Erro: {e}")
        return False
        
# --- ***** NOVAS FUNÇÕES: CAIXA DE COMISSÃO ***** ---

def carregar_caixa_comissao():
    """
    (RTDB) Carrega TODOS os registros do caixa de comissão.
    """
    if not db_ref:
        return _local_json_read('caixa_comissao.json', {})
    try:
        ref = db_ref.child('caixa_comissao') 
        data = ref.get()
        return data if data else {} 
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao carregar o caixa de comissão: {e}")
        return {} 

def salvar_caixa_comissao(dados_caixa):
    """
    (RTDB) Salva os dados completos do caixa de comissão.
    """
    if not db_ref:
        return _local_json_write('caixa_comissao.json', dados_caixa)
    try:
        ref = db_ref.child('caixa_comissao')
        ref.set(dados_caixa)
        return True
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao salvar o caixa de comissão: {e}")
        return False

def carregar_pins_consultores():
    """
    (RTDB) Carrega a lista de PINs dos consultores.
    """
    if not db_ref:
        return _local_json_read('pins_consultores.json', {})
    try:
        ref = db_ref.child('pins_consultores') 
        data = ref.get()
        return data if data else {} 
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao carregar PINs: {e}")
        return {} 

def salvar_pins_consultores(dados_pins):
    """
    (RTDB) Salva a lista de PINs dos consultores.
    """
    if not db_ref:
        return _local_json_write('pins_consultores.json', dados_pins)
    try:
        ref = db_ref.child('pins_consultores')
        ref.set(dados_pins)
        return True
    except Exception as e:
        messagebox.showerror("Erro Firebase", f"Erro ao salvar PINs: {e}")
        return False