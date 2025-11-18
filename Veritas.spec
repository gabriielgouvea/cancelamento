# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['main.py'], # <-- CORRIGIDO
    pathex=[], 
    binaries=[],
    datas=[ ('data', 'data') ],
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
        # --- NOVAS ADIÇÕES (Câmera e Upload) ---
        'cv2',
        'numpy',
        'imagekitio',
        'multiprocessing',
        'queue'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
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
    console=False, # Modo Janela (sem console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='renuncia.ico', # <-- ADICIONADO
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