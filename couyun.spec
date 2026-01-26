# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

is_win = sys.platform.startswith("win")
is_mac = sys.platform == "darwin"
is_linux = sys.platform.startswith("linux")

a = Analysis(
    ['couyun/ui/rhythm.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('couyun/ui/assets/font', 'couyun/ui/assets/font'),
        ('couyun/ui/assets/picture', 'couyun/ui/assets/picture'),
        ('couyun/ui/assets/state', 'couyun/ui/assets/state'),
        ('couyun/ci_pu/ci_list', 'couyun/ci_pu/ci_list'),
        ('couyun/ci_pu/ci_long', 'couyun/ci_pu/ci_long'),
        ('couyun/ci_pu/ci_long_origin', 'couyun/ci_pu/ci_long_origin'),
        ('couyun/ci_pu/ci_long_trad', 'couyun/ci_pu/ci_long_trad'),
        ('couyun/ci_pu/ci_origin', 'couyun/ci_pu/ci_origin'),
        ('couyun/ci_pu/ci_trad', 'couyun/ci_pu/ci_trad'),
        ('couyun/ci_pu/ci_index.json', 'couyun/ci_pu'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas', 'PyQt5', 'email',
        'unittest', 'pydoc', 'pygments', 'asyncio', 'turtle', 'pytz',
        'dateutil', 'tzdata',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ---- 平台差异处理 ----
icon = None
version = None

if is_win:
    icon = ['couyun/ui/assets/picture/ei.ico']
    version = 'file_version.txt'
elif is_mac:
    icon = ['couyun/ui/assets/picture/ei.icns']
elif is_linux:
    icon = None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='couyun',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,   # CI 环境关闭 UPX 更稳
    console=False,
    icon=icon,
    version=version,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='couyun',
)

# ---- 可选：拷贝 README.pdf（若存在）----
import shutil
build_dir = os.path.join('dist', 'couyun')
if os.path.exists('README.pdf'):
    os.makedirs(build_dir, exist_ok=True)
    shutil.copy2('README.pdf', build_dir)
