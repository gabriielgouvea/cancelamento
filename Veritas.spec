# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.building.datastruct import Tree

def _find_spec_dir() -> str:
    # No PyInstaller >= 6.16, __file__ pode não estar definido no escopo do .spec.
    # Então inferimos o caminho do .spec via sys.argv.
    for arg in reversed(sys.argv):
        if isinstance(arg, str) and arg.lower().endswith('.spec') and os.path.exists(arg):
            return os.path.abspath(os.path.dirname(arg))
    return os.path.abspath(os.getcwd())

SPEC_DIR = _find_spec_dir()
DATA_DIR = os.path.join(SPEC_DIR, 'data')

a = Analysis(
    ['main.py'], 
    pathex=[], 
    binaries=[],
    # Empacota assets (ícones/imagens) e JSONs de base.
    # ATENÇÃO: não empacotar credenciais (data/firebase-key.json).
    datas=[],
    hiddenimports=[
        'ttkbootstrap',
        'piexif',
        'PIL', 
        'dateutil.relativedelta',
        # --- Dependências da Calculadora de Comissão ---
        'pdfplumber',
        'pdfminer',
        'pdfminer.six',
        'chardet',
        'Crypto',
        'PyCryptodome',
        'firebase_admin',
        # --- NOVAS ADIÇÕES (Câmera, Upload e PDF) ---
        'cv2',
        'numpy',
        'imagekitio',
        'multiprocessing',
        'queue',
        'reportlab',  # <--- ADICIONADO: Para gerar o Holerite
        'reportlab.lib',
        'reportlab.pdfgen'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Inclui a pasta data inteira no build (recursivo).
a.datas += Tree(
    DATA_DIR,
    prefix='data',
    excludes=[],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Veritas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Modo Janela (sem console preto)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='renuncia.ico', 
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Veritas',
)