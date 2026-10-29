# Construye dist\FutbolSilueta.exe con PyInstaller.
# Uso: powershell -ExecutionPolicy Bypass -File .\build_exe.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "FutbolSilueta" `
    --add-data "imagenes;imagenes" `
    main.py

Write-Host ""
Write-Host "Ejecutable creado en dist\FutbolSilueta.exe"
