from pathlib import Path

project_root = Path.cwd()
data_dir = project_root / "data"
docs_dir = project_root / "docs"
recipes_dir = project_root / "recipes"
frontend_dir = project_root / "frontend"
api_dir = project_root / "api"
scripts_dir = project_root / "scripts"
solutions_dir = project_root / "solutions"
readme_file = project_root / "README.md"
requirements_file = project_root / "requirements.txt"
pyproject_file = project_root / "pyproject.toml"

block_cipher = None

a = Analysis(
    [str(project_root / "src" / "horticalc" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(data_dir), "data"),
        (str(docs_dir), "docs"),
        (str(recipes_dir), "recipes"),
        (str(frontend_dir), "frontend"),
        (str(api_dir), "api"),
        (str(scripts_dir), "scripts"),
        (str(solutions_dir), "solutions"),
        (str(readme_file), "."),
        (str(requirements_file), "."),
        (str(pyproject_file), "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="horticalc",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="horticalc",
)
