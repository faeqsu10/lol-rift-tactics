$ErrorActionPreference = "Stop"

$venvPython = ".venv-win\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    python -m venv .venv-win
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements-native.txt

& $venvPython -m PyInstaller `
    --clean `
    --noconfirm `
    --onefile `
    --windowed `
    --name rift-tactics-win `
    --distpath release\windows `
    --workpath build\pyinstaller-windows `
    --paths . `
    --add-data "assets;assets" `
    run_tactics.py

Compress-Archive `
    -Path release\windows\rift-tactics-win.exe `
    -DestinationPath release\windows\rift-tactics-win.zip `
    -Force
