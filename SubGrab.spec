# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path('c:/Users/me/Desktop/Projects/SubGrab-main'))],
    binaries=[],
    datas=[
        # Bundle scanner .py files as data so disk-based dynamic loading works
        ('modules/*.py',      'modules'),
        ('ai_engine/*.py',    'ai_engine'),
        ('ai_engine/config.ini', 'ai_engine'),
    ],
    hiddenimports=[
        # DNS
        'dns', 'dns.resolver', 'dns.zone', 'dns.query', 'dns.reversename',
        'dns.rdatatype', 'dns.rdataclass', 'dns.name', 'dns.rdata',
        # Requests / networking
        'requests', 'requests.adapters', 'urllib3', 'charset_normalizer',
        'certifi', 'idna',
        # Parsing
        'bs4', 'lxml', 'lxml.etree', 'lxml._elementpath',
        # Output
        'colorama', 'tqdm',
        # Optional API
        'shodan',
        # Stdlib extras
        'configparser', 'importlib.util', 'importlib.machinery',
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog',
        'tkinter.messagebox', 'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PIL', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SubGrab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,      # True = CLI works from terminal; GUI hides console via ctypes
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
