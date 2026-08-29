# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AI Desktop Automation Agent.

Build command:
    pyinstaller agent.spec

Output will be in the 'dist' folder.
"""

block_cipher = None

a = Analysis(
    ['agent.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include templates folder if it exists
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'keyboard',
        'pyautogui',
        'PIL',
        'PIL.Image',
        'cv2',
        'numpy',
        'psutil',
        'requests',
        'pyscreeze',
        'pytweening',
        'pymsgbox',
        'pygetwindow',
        'pyrect',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'xml',
        'pydoc',
        'doctest',
        'argparse',
        'difflib',
        'inspect',
        'calendar',
        'pickle',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutomationAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True to show console window (useful for debugging)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have one: icon='icon.ico'
)
