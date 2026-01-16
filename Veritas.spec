# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['main.py'], 
    pathex=[], 
    binaries=[],
    # Empacota assets (ícones/imagens) e JSONs de base.
    # ATENÇÃO: não empacotar credenciais (data/firebase-key.json).
    datas=[
        ('data\\*.png', 'data'),
        ('data\\*.jpg', 'data'),
        ('data\\*.jpeg', 'data'),
        ('data\\*.ico', 'data'),
        ('data\\consultores.json', 'data'),
        ('data\\folgas.json', 'data'),
    ],
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