# ============================================================
# Anay's Password Vault - Windows Dependency Installer
# PowerShell Version with Python Selection & Alias Detection
# ============================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Anay's Password Vault - Installer"

# ============================================================
# Helper Functions
# ============================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "    $Text" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-OK { param([string]$Text); Write-Host "[OK] $Text" -ForegroundColor Green }
function Write-Err { param([string]$Text); Write-Host "[ERROR] $Text" -ForegroundColor Red }
function Write-Warn { param([string]$Text); Write-Host "[WARNING] $Text" -ForegroundColor Yellow }
function Write-Info { param([string]$Text); Write-Host "[INFO] $Text" -ForegroundColor White }

# ============================================================
# Find All Python Installations
# ============================================================

function Find-AllPythonInstallations {
    Write-Header "Scanning for Python Installations"
    
    $pythonAliases = @(
        "python",
        "python3",
        "python3.7",
        "python3.8",
        "python3.9",
        "python3.10",
        "python3.11",
        "python3.12",
        "python37",
        "python38",
        "python39",
        "python310",
        "python311",
        "python312"
    )
    
    $pyLauncherVersions = @("3", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12")
    
    $foundPythons = @()
    $checkedVersions = @{}
    
    # Check standard aliases
    foreach ($alias in $pythonAliases) {
        try {
            $result = & $alias --version 2>&1
            if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
                $version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                
                # Avoid duplicates
                if (-not $checkedVersions.ContainsKey($version)) {
                    $checkedVersions[$version] = $true
                    $foundPythons += @{
                        Command = $alias
                        Version = $version
                        Major   = [int]$Matches[1]
                        Minor   = [int]$Matches[2]
                        Display = "$alias --> Python $version"
                    }
                    Write-Host "  [FOUND] $alias --> Python $version" -ForegroundColor Green
                }
            }
        } catch { }
    }
    
    # Check py launcher
    foreach ($ver in $pyLauncherVersions) {
        try {
            $result = & py -$ver --version 2>&1
            if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
                $version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                $cmd = "py -$ver"
                
                if (-not $checkedVersions.ContainsKey($version)) {
                    $checkedVersions[$version] = $true
                    $foundPythons += @{
                        Command = $cmd
                        Version = $version
                        Major   = [int]$Matches[1]
                        Minor   = [int]$Matches[2]
                        Display = "$cmd --> Python $version"
                    }
                    Write-Host "  [FOUND] $cmd --> Python $version" -ForegroundColor Green
                }
            }
        } catch { }
    }
    
    return $foundPythons
}

# ============================================================
# Invoke Python Command (handles aliases with spaces)
# ============================================================

function Invoke-PythonCommand {
    param(
        [string]$PythonCmd,
        [string[]]$Arguments
    )
    
    if ($PythonCmd -match " ") {
        $parts = $PythonCmd -split " ", 2
        $allArgs = @($parts[1]) + $Arguments
        & $parts[0] $allArgs
    } else {
        & $PythonCmd $Arguments
    }
}

# ============================================================
# MAIN SCRIPT
# ============================================================

Clear-Host
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "     Anay's Password Vault - Dependency Installer" -ForegroundColor Magenta
Write-Host "     Face Recognition + Password Protection" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

# ============================================================
# Find Python Installations
# ============================================================

$foundPythons = Find-AllPythonInstallations

if ($foundPythons.Count -eq 0) {
    Write-Host ""
    Write-Err "No Python installation found!"
    Write-Host ""
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Supported versions: Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12" -ForegroundColor Yellow
    Write-Host ""
    
    $manualPython = Read-Host "Or enter Python command manually (press Enter to exit)"
    
    if ([string]::IsNullOrWhiteSpace($manualPython)) {
        exit 1
    }
    
    try {
        $result = Invoke-PythonCommand -PythonCmd $manualPython -Arguments @("--version")
        if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
            $foundPythons += @{
                Command = $manualPython
                Version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                Major   = [int]$Matches[1]
                Minor   = [int]$Matches[2]
                Display = "$manualPython --> Python $($Matches[1]).$($Matches[2]).$($Matches[3])"
            }
        } else {
            Write-Err "Invalid Python command"
            exit 1
        }
    } catch {
        Write-Err "Failed to run: $manualPython"
        exit 1
    }
}

# ============================================================
# Let User Select Python Version
# ============================================================

Write-Header "Select Python Version"

$selectedPython = $null

if ($foundPythons.Count -eq 1) {
    $selectedPython = $foundPythons[0]
    Write-Info "Only one Python found. Using it automatically."
    Write-Host "  Selected: $($selectedPython.Display)" -ForegroundColor Cyan
} else {
    Write-Host "Found $($foundPythons.Count) Python installation(s):" -ForegroundColor White
    Write-Host ""
    
    for ($i = 0; $i -lt $foundPythons.Count; $i++) {
        $p = $foundPythons[$i]
        Write-Host "  [$($i + 1)] $($p.Display)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "  [0] Enter custom Python command" -ForegroundColor Gray
    Write-Host ""
    
    $selection = Read-Host "Select Python version [1-$($foundPythons.Count)]"
    
    if ($selection -eq "0") {
        $customPython = Read-Host "Enter Python command"
        try {
            $result = Invoke-PythonCommand -PythonCmd $customPython -Arguments @("--version")
            if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
                $selectedPython = @{
                    Command = $customPython
                    Version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                    Major   = [int]$Matches[1]
                    Minor   = [int]$Matches[2]
                }
            }
        } catch {
            Write-Err "Invalid command. Using first available Python."
            $selectedPython = $foundPythons[0]
        }
    } else {
        $selIndex = [int]$selection - 1
        if ($selIndex -ge 0 -and $selIndex -lt $foundPythons.Count) {
            $selectedPython = $foundPythons[$selIndex]
        } else {
            Write-Warn "Invalid selection. Using first available Python."
            $selectedPython = $foundPythons[0]
        }
    }
}

$pythonCmd = $selectedPython.Command
$pyMajor = $selectedPython.Major
$pyMinor = $selectedPython.Minor
$pyVersion = $selectedPython.Version

Write-Host ""
Write-Host "============================================================" -ForegroundColor White
Write-Host "    Selected Python Configuration" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor White
Write-Host "    Command  : $pythonCmd" -ForegroundColor Gray
Write-Host "    Version  : $pyVersion" -ForegroundColor Gray
Write-Host "    Major    : $pyMajor" -ForegroundColor Gray
Write-Host "    Minor    : $pyMinor" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor White

# Version check
if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 7)) {
    Write-Err "Python 3.7 or higher is required. You selected Python $pyMajor.$pyMinor"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-OK "Python version is compatible!"

# ============================================================
# Set dlib wheel URL
# ============================================================

$wheelUrls = @{
    7  = @{ File = "dlib-19.22.99-cp37-cp37m-win_amd64.whl"; Url = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp37-cp37m-win_amd64.whl" }
    8  = @{ File = "dlib-19.22.99-cp38-cp38-win_amd64.whl"; Url = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp38-cp38-win_amd64.whl" }
    9  = @{ File = "dlib-19.22.99-cp39-cp39-win_amd64.whl"; Url = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp39-cp39-win_amd64.whl" }
    10 = @{ File = "dlib-19.22.99-cp310-cp310-win_amd64.whl"; Url = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp310-cp310-win_amd64.whl" }
    11 = @{ File = "dlib-19.24.1-cp311-cp311-win_amd64.whl"; Url = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.1-cp311-cp311-win_amd64.whl" }
    12 = @{ File = "dlib-19.24.99-cp312-cp312-win_amd64.whl"; Url = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.99-cp312-cp312-win_amd64.whl" }
}

$wheelInfo = $wheelUrls[$pyMinor]

Write-Host ""
if ($wheelInfo) {
    Write-OK "Pre-built dlib wheel available for Python 3.$pyMinor"
    Write-Host "    File: $($wheelInfo.File)" -ForegroundColor Gray
} else {
    Write-Warn "No pre-built dlib wheel for Python 3.$pyMinor"
}

# ============================================================
# Upgrade pip
# ============================================================

Write-Header "Upgrading pip"

Write-Info "Upgrading pip..."
Invoke-PythonCommand -PythonCmd $pythonCmd -Arguments @("-m", "pip", "install", "--upgrade", "pip", "--quiet") 2>$null
Write-OK "pip ready!"

# ============================================================
# Virtual Environment
# ============================================================

Write-Header "Virtual Environment Setup"

Write-Host "Virtual environments isolate project dependencies." -ForegroundColor Gray
Write-Host "This is RECOMMENDED for avoiding conflicts." -ForegroundColor Gray
Write-Host ""

$createVenv = Read-Host "Create virtual environment? [Y/N]"
$usingVenv = $false

if ($createVenv -eq 'Y' -or $createVenv -eq 'y') {
    if (Test-Path "venv") {
        Write-Warn "Virtual environment 'venv' already exists."
        $useExisting = Read-Host "Use existing venv? [Y/N]"
        
        if ($useExisting -ne 'Y' -and $useExisting -ne 'y') {
            Write-Info "Removing old virtual environment..."
            Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
            Write-Info "Creating new virtual environment..."
            Invoke-PythonCommand -PythonCmd $pythonCmd -Arguments @("-m", "venv", "venv")
        }
    } else {
        Write-Info "Creating virtual environment..."
        Invoke-PythonCommand -PythonCmd $pythonCmd -Arguments @("-m", "venv", "venv")
    }
    
    Write-Info "Activating virtual environment..."
    
    $activateScript = ".\venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-OK "Virtual environment activated!"
        $usingVenv = $true
        $pythonCmd = "python"
        
        python -m pip install --upgrade pip --quiet 2>$null
    } else {
        Write-Err "Could not find activation script!"
        Write-Warn "Continuing without virtual environment..."
    }
} else {
    Write-Warn "Skipping virtual environment. Installing globally."
}

# ============================================================
# Install Basic Dependencies
# ============================================================

Write-Header "Installing Basic Dependencies"

$basicPackages = @("numpy", "pillow", "pyperclip", "cryptography", "opencv-python")

foreach ($pkg in $basicPackages) {
    Write-Info "Installing $pkg..."
    pip install $pkg --quiet 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-OK "$pkg installed"
    } else {
        Write-Err "Failed to install $pkg"
    }
}

# ============================================================
# Install dlib
# ============================================================

Write-Header "Installing dlib for Python 3.$pyMinor"

$dlibInstalled = $false

if ($wheelInfo) {
    Write-Info "Method 1: Installing from pre-built wheel..."
    Write-Host "URL: $($wheelInfo.Url)" -ForegroundColor Gray
    Write-Host ""
    
    pip install $wheelInfo.Url 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-OK "dlib installed successfully from pre-built wheel!"
        $dlibInstalled = $true
    } else {
        Write-Warn "Direct URL installation failed."
        Write-Info "Method 2: Downloading wheel file first..."
        
        $wheelFile = $wheelInfo.File
        try {
            Invoke-WebRequest -Uri $wheelInfo.Url -OutFile $wheelFile -UseBasicParsing -ErrorAction Stop
            
            if (Test-Path $wheelFile) {
                Write-Info "Download complete. Installing..."
                pip install $wheelFile 2>$null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-OK "dlib installed from downloaded wheel!"
                    $dlibInstalled = $true
                }
                Remove-Item $wheelFile -ErrorAction SilentlyContinue
            }
        } catch {
            Write-Err "Download failed: $_"
        }
    }
}

# Try building from source if wheel failed
if (-not $dlibInstalled) {
    Write-Info "Method 3: Attempting to build from source..."
    
    $cmakeExists = Get-Command cmake -ErrorAction SilentlyContinue
    if ($cmakeExists) {
        Write-OK "CMake found. Building dlib (this may take 10-15 minutes)..."
        pip install dlib 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-OK "dlib built from source successfully!"
            $dlibInstalled = $true
        }
    } else {
        Write-Warn "CMake not found. Cannot build from source."
    }
}

# Show manual instructions if failed
if (-not $dlibInstalled) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "     DLIB INSTALLATION FAILED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual installation options:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option A - Download wheel manually:" -ForegroundColor White
    Write-Host "  1. Visit: https://github.com/z-mahmud22/Dlib_Windows_Python3.x" -ForegroundColor Gray
    Write-Host "  2. Download: $($wheelInfo.File)" -ForegroundColor Gray
    Write-Host "  3. Run: pip install `"path\to\$($wheelInfo.File)`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option B - Install build tools:" -ForegroundColor White
    Write-Host "  1. Install CMake: https://cmake.org/download/" -ForegroundColor Gray
    Write-Host "  2. Install VS Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Gray
    Write-Host "  3. Restart computer and run: pip install dlib" -ForegroundColor Gray
    Write-Host ""
    
    $continue = Read-Host "Continue without dlib? [Y/N]"
    if ($continue -ne 'Y' -and $continue -ne 'y') {
        exit 1
    }
}

# ============================================================
# Install face-recognition
# ============================================================

Write-Header "Installing face-recognition"

if ($dlibInstalled) {
    Write-Info "Installing face-recognition..."
    pip install face-recognition 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-OK "face-recognition installed successfully!"
    } else {
        Write-Err "Failed to install face-recognition"
    }
} else {
    Write-Warn "Skipping face-recognition (requires dlib)"
    Write-Warn "Face authentication will not be available."
}

# ============================================================
# requirements.txt
# ============================================================

if (Test-Path "requirements.txt") {
    Write-Header "Processing requirements.txt"
    Write-Info "Installing additional dependencies..."
    pip install -r requirements.txt --quiet 2>$null
    Write-OK "requirements.txt processed"
}

# ============================================================
# Create Launch Scripts
# ============================================================

Write-Header "Creating Launch Scripts"

# Create run_app.bat
if ($usingVenv) {
    $batContent = @"
@echo off
echo ============================================================
echo     Starting Anay's Password Vault...
echo ============================================================
call venv\Scripts\activate.bat
python gui_app.py
pause
"@
} else {
    $batContent = @"
@echo off
echo ============================================================
echo     Starting Anay's Password Vault...
echo ============================================================
$pythonCmd gui_app.py
pause
"@
}

$batContent | Out-File -FilePath "run_app.bat" -Encoding ASCII
Write-OK "Created run_app.bat"

# Create run_app.ps1
if ($usingVenv) {
    $ps1Content = @'
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    Starting Anay's Password Vault..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"
python gui_app.py
Read-Host "Press Enter to exit"
'@
} else {
    $ps1Content = @"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    Starting Anay's Password Vault..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
$pythonCmd gui_app.py
Read-Host "Press Enter to exit"
"@
}

$ps1Content | Out-File -FilePath "run_app.ps1" -Encoding UTF8
Write-OK "Created run_app.ps1"

# ============================================================
# Verify Installation
# ============================================================

Write-Header "Verifying Installation"

$errors = 0
$warnings = 0

# Test packages
$tests = @(
    @{ Module = "cv2"; Name = "OpenCV"; Required = $true },
    @{ Module = "dlib"; Name = "dlib"; Required = $false },
    @{ Module = "face_recognition"; Name = "face-recognition"; Required = $false },
    @{ Module = "PIL"; Name = "Pillow"; Required = $true; Import = "from PIL import Image" },
    @{ Module = "pyperclip"; Name = "pyperclip"; Required = $true },
    @{ Module = "cryptography"; Name = "cryptography"; Required = $true; Import = "from cryptography.fernet import Fernet" }
)

foreach ($test in $tests) {
    $importCmd = if ($test.Import) { $test.Import } else { "import $($test.Module)" }
    
    try {
        $result = python -c "$importCmd; print('OK')" 2>&1
        if ($result -eq "OK") {
            Write-OK "$($test.Name)"
        } else {
            throw "Import failed"
        }
    } catch {
        if ($test.Required) {
            Write-Err "$($test.Name) - NOT INSTALLED"
            $errors++
        } else {
            Write-Warn "$($test.Name) - NOT INSTALLED (optional)"
            $warnings++
        }
    }
}

# ============================================================
# Final Summary
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

if ($errors -eq 0) {
    if ($warnings -eq 0) {
        Write-Host "     INSTALLATION COMPLETE!" -ForegroundColor Green
    } else {
        Write-Host "     INSTALLATION COMPLETE WITH WARNINGS" -ForegroundColor Yellow
    }
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Python: $pythonCmd (v$pyVersion)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To run the application:" -ForegroundColor White
    Write-Host ""
    Write-Host "  Option 1: Double-click run_app.bat" -ForegroundColor Yellow
    Write-Host "  Option 2: Run .\run_app.ps1 in PowerShell" -ForegroundColor Yellow
    
    if ($usingVenv) {
        Write-Host ""
        Write-Host "  Manual method:" -ForegroundColor White
        Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
        Write-Host "    python gui_app.py" -ForegroundColor Gray
    }
    
    if ($warnings -gt 0) {
        Write-Host ""
        Write-Host "Note: $warnings optional package(s) not installed." -ForegroundColor Yellow
        Write-Host "      Face authentication may not be available." -ForegroundColor Yellow
    }
} else {
    Write-Host "     INSTALLATION FAILED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "$errors required package(s) failed to install." -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"