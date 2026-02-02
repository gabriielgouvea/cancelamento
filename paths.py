# -*- coding: utf-8 -*-

"""paths.py

Helpers de caminho para rodar em DEV e no executável (PyInstaller).

- Recursos empacotados (imagens/ícones) devem ser lidos de `sys._MEIPASS` quando frozen.
- Dados mutáveis (JSONs offline, cache, etc.) devem ir para uma pasta do usuário
  (Windows: %APPDATA%\\Veritas\\data) para evitar problemas de permissão.
"""

from __future__ import annotations

import os
import sys
from typing import Optional


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_exe_dir() -> str:
    """Pasta do executável (frozen) ou do projeto (dev)."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.realpath(__file__))


def get_resource_base_dir() -> str:
    """Pasta base onde recursos empacotados ficam disponíveis.

    No PyInstaller, `sys._MEIPASS` aponta para o diretório interno (ex.: dist/.../_internal).
    """
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return str(getattr(sys, "_MEIPASS"))
    return get_exe_dir()


def get_resource_path(*parts: str) -> str:
    return os.path.join(get_resource_base_dir(), *parts)


def get_user_data_base_dir(app_name: str = "Veritas") -> str:
    base = (
        os.getenv("APPDATA")
        or os.getenv("LOCALAPPDATA")
        or os.path.expanduser("~")
    )
    return os.path.join(base, app_name)


def get_user_data_dir(app_name: str = "Veritas") -> str:
    return os.path.join(get_user_data_base_dir(app_name), "data")


def resolve_data_file(filename: str, *, app_name: str = "Veritas") -> str:
    """Resolve um arquivo de data preferindo a pasta do usuário.

    - Se existir em %APPDATA%\\Veritas\\data, usa.
    - Caso contrário, usa o empacotado em resources/data.
    """
    user_path = os.path.join(get_user_data_dir(app_name), filename)
    if os.path.exists(user_path):
        return user_path

    return get_resource_path("data", filename)
