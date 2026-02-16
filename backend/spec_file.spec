# -*- mode: python ; coding: utf-8 -*-

# 定义应用的分析配置
a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 包含 app 目录下的所有 Python 文件
        ('app', 'app'),
        # 包含 .env 文件
        ('.env', '.'),
        # 包含 public 目录下的模板文件
        ('public', 'public'),
    ],
    hiddenimports=[
        # FastAPI 相关
        'uvicorn',
        'uvicorn.lifespan.auto',
        'uvicorn.workers',
        # 数据库相关
        'sqlalchemy',
        'alembic',
        # 其他可能的依赖
        'pydantic',
        'pydantic_settings',
        'python-dotenv',
        'httpx',
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
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 设置为 True 以查看控制台输出，发布时可改为 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)
