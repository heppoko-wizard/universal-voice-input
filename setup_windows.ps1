# STT Tool - Windows Setup Script
# Run this once as Administrator to set up the environment

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=== STT Tool Setup (Windows) ===" -ForegroundColor Cyan

# 1. Check Python
Write-Host "[1/5] Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion"
} catch {
    Write-Host "Python not found. Please install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

# 2. Create venv
if (-not (Test-Path "venv")) {
    Write-Host "[2/5] Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "[2/5] Virtual environment already exists."
}

# 3. Activate and install dependencies
Write-Host "[3/5] Installing Python dependencies..."
& "$ScriptDir\venv\Scripts\Activate.ps1"
pip install --upgrade pip
pip install sounddevice numpy scipy pynput pyperclip flet groq openai python-dotenv faster-whisper

# 4. Create startup shortcut
Write-Host "[4/5] Creating startup shortcut..."
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "STT-Tool.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "$ScriptDir\venv\Scripts\pythonw.exe"
$Shortcut.Arguments = "$ScriptDir\core.py"
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Save()

# 5. Create start/stop scripts
Write-Host "[5/5] Creating helper scripts..."

@"
@echo off
cd /d "$ScriptDir"
start /min "" "$ScriptDir\venv\Scripts\pythonw.exe" "$ScriptDir\core.py"
echo STT Tool started in background.
"@ | Out-File -FilePath "$ScriptDir\start_stt.bat" -Encoding ASCII

@"
@echo off
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq *core.py*" 2>nul
echo STT Tool stopped.
"@ | Out-File -FilePath "$ScriptDir\stop_stt.bat" -Encoding ASCII

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "To start now:    .\start_stt.bat"
Write-Host "To stop:         .\stop_stt.bat"
Write-Host ""
Write-Host "The tool will auto-start on Windows login."
