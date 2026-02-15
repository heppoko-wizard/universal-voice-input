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
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
} else {
    Write-Host "WARNING: requirements.txt not found. Installing base packages..." -ForegroundColor Yellow
    pip install sounddevice numpy scipy pynput pyperclip flet groq openai python-dotenv faster-whisper litellm
}

# 4. Create startup shortcut
Write-Host "[4/5] Creating Desktop shortcut..."
$DesktopFolder = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopFolder "Open-STT-Tool.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
# Create a runner script first to handle environment
@"
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
start /min "" pythonw.exe stt_daemon.py
"@ | Out-File -FilePath "$ScriptDir\start_stt_gui.bat" -Encoding ASCII

$Shortcut.TargetPath = "$ScriptDir\start_stt_gui.bat"
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.IconLocation = "$ScriptDir\venv\Scripts\python.exe,0"
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Save()

# 5. Create start/stop scripts
Write-Host "[5/5] Creating helper scripts..."

# start_stt_gui.bat is already created above

@"
@echo off
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq *stt_daemon.py*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq *stt_daemon.py*" 2>nul
echo STT Tool stopped.
pause
"@ | Out-File -FilePath "$ScriptDir\stop_stt.bat" -Encoding ASCII

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Desktop shortcut 'Open-STT-Tool' created."
Write-Host "To start manually: .\start_stt_gui.bat"
Write-Host "To stop:           .\stop_stt.bat"
Write-Host ""

