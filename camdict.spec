a = Analysis(
    ["camdict/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        # lxml C extensions not always auto-detected
        "lxml.etree",
        "lxml._elementpath",
        # lazy import inside main() — static analysis misses it
        "camdict.parsers.qianyix",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI
        "tkinter",
        "_tkinter",
        # build/packaging
        "distutils",
        "setuptools",
        "pip",
        "lib2to3",
        # testing
        "unittest",
        "doctest",
        "test",
        # rich extras we don't use
        "markdown_it",
        "mdurl",
        "pygments",
        # network protocols we don't use
        "ftplib",
        "imaplib",
        "smtplib",
        "poplib",
        "telnetlib",
        "xmlrpc",
        # misc stdlib we don't use
        "turtle",
        "curses",
        "sqlite3",
        "multiprocessing",
        "concurrent",
        "asyncio",
        # stdlib xml — we use lxml, not stdlib
        "xml.etree",
        "xml.dom",
        "xml.sax",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="camdict",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
