# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for SubVigil (Windows one-file GUI/CLI binary).

Build on Windows with:
    pip install -r requirements.txt pyinstaller
    pyinstaller --noconfirm SubVigil.spec

Output: dist\\SubVigil.exe

Notes
-----
- `modules/` and `ai_engine/` are loaded at runtime via importlib (the plugin
  system), so they are shipped as DATA, not analysed as code. Their third-party
  dependencies are therefore invisible to PyInstaller's static analysis and must
  be declared as hidden imports below.
- `--windowed` suppresses the console window for the GUI; `main.py` still routes
  to the CLI when argv is passed.
"""

from PyInstaller.utils.hooks import collect_submodules

# Third-party deps used inside plugins (not statically discoverable).
hidden = [
    "requests",
    "dns", "dns.resolver", "dns.zone", "dns.query", "dns.rdatatype",
    "colorama",
    "bs4",
    "tqdm",
    "shodan",
    "aiohttp",
    "urllib3",
    "certifi",
]
hidden += collect_submodules("dns")
hidden += collect_submodules("shodan")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("modules", "modules"),
        ("ai_engine", "ai_engine"),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SubVigil",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # --windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="subvigil.ico",
)
