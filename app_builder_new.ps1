# ============================================================
# Anay's Password Vault - Complete App Builder
# With Python Selection, venv, Face Auth, dlib, Camera Tests
# ============================================================

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Building Anay's Password Vault"

# ============================================================
# Configuration
# ============================================================

$AppName = "PasswordVault"
$MainScript = "gui_app.py"
$IconFile = "icon.ico"
$OutputFolder = "exported_app"
$VenvPath = "venv"

$RequiredFiles = @(
    "gui_app.py",
    "face_auth.py",
    "vault_core.py",
    "password_generator.py"
)

$DataFiles = @(
    "vault_core.py",
    "password_generator.py",
    "face_auth.py"
)

$OptionalDataFiles = @(
    "master.hash",
    "face_data"
)

$HiddenImports = @(
    "face_recognition",
    "face_recognition_models",
    "dlib",
    "cv2",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "numpy",
    "cryptography",
    "cryptography.fernet",
    "cryptography.hazmat.primitives",
    "cryptography.hazmat.primitives.kdf.pbkdf2",
    "cryptography.hazmat.primitives.hashes",
    "cryptography.hazmat.backends",
    "pyperclip",
    "tkinter",
    "tkinter.ttk",
    "tkinter.simpledialog",
    "tkinter.messagebox",
    "tempfile",
    "pickle",
    "hashlib",
    "pathlib",
    "datetime"
)

$CollectAll = @(
    "face_recognition",
    "face_recognition_models",
    "dlib"
)

# dlib wheel URLs
$DlibWheels = @{
    "7"  = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp37-cp37m-win_amd64.whl"
    "8"  = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp38-cp38-win_amd64.whl"
    "9"  = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp39-cp39-win_amd64.whl"
    "10" = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp310-cp310-win_amd64.whl"
    "11" = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.1-cp311-cp311-win_amd64.whl"
    "12" = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.99-cp312-cp312-win_amd64.whl"
}

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

function Write-Log {
    param([string]$Level, [string]$Message)
    $color = switch ($Level) {
        "OK"      { "Green" }
        "ERROR"   { "Red" }
        "WARNING" { "Yellow" }
        "INFO"    { "White" }
        "FOUND"   { "Green" }
        default   { "Gray" }
    }
    Write-Host "[$Level] $Message" -ForegroundColor $color
}

function Test-PythonModule {
    param([string]$Module)
    $result = python -c "import $Module" 2>&1
    return $LASTEXITCODE -eq 0
}

function Find-AllPythonInstallations {
    <#
    .SYNOPSIS
    Finds all Python installations on the system
    .DESCRIPTION
    Scans for various Python aliases and py launcher versions
    #>
    
    Write-Header "Step 1: Detecting Python Installations"
    
    $PythonAliases = @(
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
    
    $PyLauncherVersions = @("3", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12")
    
    $FoundPythons = @()
    $CheckedVersions = @{}
    
    Write-Log "INFO" "Scanning for Python installations..."
    Write-Host ""
    
    # Check standard aliases
    foreach ($alias in $PythonAliases) {
        try {
            $result = & $alias --version 2>&1
            if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
                $version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                
                # Skip duplicates and Python 2.x
                if ($major -ge 3 -and -not $CheckedVersions.ContainsKey($version)) {
                    $CheckedVersions[$version] = $true
                    
                    # Get full path
                    try {
                        $fullPath = (Get-Command $alias -ErrorAction SilentlyContinue).Source
                    }
                    catch {
                        $fullPath = "Unknown"
                    }
                    
                    $FoundPythons += @{
                        Command = $alias
                        Version = $version
                        Major   = $major
                        Minor   = $minor
                        Path    = $fullPath
                        Display = "$alias --> Python $version"
                    }
                    
                    Write-Host "  [FOUND] $alias --> Python $version" -ForegroundColor Green
                    Write-Host "          Path: $fullPath" -ForegroundColor Gray
                }
            }
        }
        catch { }
    }
    
    # Check py launcher
    foreach ($ver in $PyLauncherVersions) {
        try {
            $result = & py -$ver --version 2>&1
            if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
                $version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                $cmd = "py -$ver"
                
                if (-not $CheckedVersions.ContainsKey($version)) {
                    $CheckedVersions[$version] = $true
                    
                    $FoundPythons += @{
                        Command = $cmd
                        Version = $version
                        Major   = $major
                        Minor   = $minor
                        Path    = "py launcher"
                        Display = "$cmd --> Python $version"
                    }
                    
                    Write-Host "  [FOUND] $cmd --> Python $version" -ForegroundColor Green
                }
            }
        }
        catch { }
    }
    
    return $FoundPythons
}

function Select-PythonVersion {
    param([array]$FoundPythons)
    
    <#
    .SYNOPSIS
    Allows user to select which Python version to use for building
    #>
    
    if ($FoundPythons.Count -eq 0) {
        return $null
    }
    
    if ($FoundPythons.Count -eq 1) {
        $selected = $FoundPythons[0]
        Write-Host ""
        Write-Log "INFO" "Only one Python found. Using automatically:"
        Write-Host "       $($selected.Display)" -ForegroundColor Cyan
        return $selected
    }
    
    # Multiple Python versions found - let user choose
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "    Multiple Python Versions Found!" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please select which Python to use for building:" -ForegroundColor White
    Write-Host ""
    
    # Sort by version (newest first)
    $sorted = $FoundPythons | Sort-Object { [version]$_.Version } -Descending
    
    for ($i = 0; $i -lt $sorted.Count; $i++) {
        $p = $sorted[$i]
        $recommended = ""
        
        # Mark recommended versions
        if ($p.Minor -in @(9, 10, 11)) {
            $recommended = " (Recommended)" 
        }
        
        Write-Host "  [$($i + 1)] $($p.Display)$recommended" -ForegroundColor Yellow
        Write-Host "      Path: $($p.Path)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "  [0] Enter custom Python command" -ForegroundColor Gray
    Write-Host ""
    
    do {
        $selection = Read-Host "Select Python version [1-$($sorted.Count)]"
        
        if ($selection -eq "0") {
            # Custom command
            $customCmd = Read-Host "Enter Python command (e.g., C:\Python39\python.exe)"
            
            try {
                $result = & $customCmd --version 2>&1
                if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
                    return @{
                        Command = $customCmd
                        Version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                        Major   = [int]$Matches[1]
                        Minor   = [int]$Matches[2]
                        Path    = $customCmd
                        Display = "$customCmd --> Python $($Matches[1]).$($Matches[2]).$($Matches[3])"
                    }
                }
            }
            catch {
                Write-Log "ERROR" "Invalid Python command: $customCmd"
            }
        }
        elseif ($selection -match "^\d+$") {
            $idx = [int]$selection - 1
            if ($idx -ge 0 -and $idx -lt $sorted.Count) {
                return $sorted[$idx]
            }
        }
        
        Write-Log "WARNING" "Invalid selection. Please try again."
        
    } while ($true)
}

function Invoke-PythonCommand {
    param(
        [string]$PythonCmd,
        [string[]]$Arguments
    )
    
    <#
    .SYNOPSIS
    Executes a Python command, handling aliases with spaces (like "py -3.9")
    #>
    
    if ($PythonCmd -match " ") {
        $parts = $PythonCmd -split " ", 2
        $allArgs = @($parts[1]) + $Arguments
        & $parts[0] $allArgs
    }
    else {
        & $PythonCmd $Arguments
    }
}

# ============================================================
# Main Script
# ============================================================

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($ScriptDir) {
    Set-Location $ScriptDir
}

Clear-Host
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "    Anay's Password Vault - App Builder" -ForegroundColor Magenta
Write-Host "    With Face Recognition & Liveness Detection" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# ============================================================
# Step 1: Find and Select Python
# ============================================================

$FoundPythons = Find-AllPythonInstallations

if ($FoundPythons.Count -eq 0) {
    Write-Host ""
    Write-Log "ERROR" "No Python installation found!"
    Write-Host ""
    Write-Host "Please install Python from: https://python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Recommended versions: Python 3.9, 3.10, or 3.11" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Make sure to check 'Add Python to PATH' during installation!" -ForegroundColor Yellow
    Write-Host ""
    
    # Allow manual entry
    $manualPython = Read-Host "Or enter Python path manually (press Enter to exit)"
    
    if ([string]::IsNullOrWhiteSpace($manualPython)) {
        exit 1
    }
    
    try {
        $result = & $manualPython --version 2>&1
        if ($result -match "Python (\d+)\.(\d+)\.(\d+)") {
            $SelectedPython = @{
                Command = $manualPython
                Version = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
                Major   = [int]$Matches[1]
                Minor   = [int]$Matches[2]
                Path    = $manualPython
                Display = "$manualPython --> Python $($Matches[1]).$($Matches[2]).$($Matches[3])"
            }
        }
        else {
            Write-Log "ERROR" "Invalid Python: $manualPython"
            exit 1
        }
    }
    catch {
        Write-Log "ERROR" "Cannot run: $manualPython"
        exit 1
    }
}
else {
    $SelectedPython = Select-PythonVersion -FoundPythons $FoundPythons
}

if (-not $SelectedPython) {
    Write-Log "ERROR" "No Python selected"
    exit 1
}

# Store selected Python info
$PythonCmd = $SelectedPython.Command
$PyMajor = $SelectedPython.Major
$PyMinor = $SelectedPython.Minor
$PyVersion = $SelectedPython.Version

Write-Host ""
Write-Host "============================================================" -ForegroundColor White
Write-Host "    Selected Python Configuration" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor White
Write-Host "    Command : $PythonCmd" -ForegroundColor Gray
Write-Host "    Version : $PyVersion" -ForegroundColor Gray
Write-Host "    Path    : $($SelectedPython.Path)" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor White
Write-Host ""

# Check minimum version
if ($PyMajor -lt 3 -or ($PyMajor -eq 3 -and $PyMinor -lt 7)) {
    Write-Log "ERROR" "Python 3.7 or higher is required. You selected Python $PyMajor.$PyMinor"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check dlib wheel availability
if ($DlibWheels.ContainsKey($PyMinor.ToString())) {
    Write-Log "OK" "Pre-built dlib wheel available for Python 3.$PyMinor"
}
else {
    Write-Log "WARNING" "No pre-built dlib wheel for Python 3.$PyMinor"
    Write-Log "WARNING" "You may need Visual Studio Build Tools to compile dlib"
}

# ============================================================
# Step 2: Setup Virtual Environment
# ============================================================

Write-Header "Step 2: Setting Up Virtual Environment"

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip = Join-Path $VenvPath "Scripts\pip.exe"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"

# Check if venv exists and matches selected Python
$CreateNewVenv = $false

if (Test-Path $VenvActivate) {
    Write-Log "OK" "Virtual environment exists"
    
    # Check if venv Python version matches selected Python
    try {
        $venvVersion = & $VenvPython --version 2>&1
        if ($venvVersion -match "Python (\d+\.\d+\.\d+)") {
            $venvPyVersion = $Matches[1]
            
            if ($venvPyVersion -ne $PyVersion) {
                Write-Log "WARNING" "Existing venv uses Python $venvPyVersion, but you selected Python $PyVersion"
                $recreate = Read-Host "Recreate virtual environment with Python $PyVersion? [Y/N]"
                
                if ($recreate -eq 'Y' -or $recreate -eq 'y') {
                    Write-Log "INFO" "Removing old virtual environment..."
                    Remove-Item -Recurse -Force $VenvPath
                    $CreateNewVenv = $true
                }
                else {
                    Write-Log "INFO" "Using existing venv with Python $venvPyVersion"
                }
            }
            else {
                Write-Log "OK" "Venv Python version matches: $venvPyVersion"
            }
        }
    }
    catch {
        Write-Log "WARNING" "Cannot determine venv Python version"
    }
}
else {
    $CreateNewVenv = $true
}

if ($CreateNewVenv) {
    Write-Log "INFO" "Creating virtual environment with $PythonCmd..."
    
    Invoke-PythonCommand -PythonCmd $PythonCmd -Arguments @("-m", "venv", $VenvPath)
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to create virtual environment"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Log "OK" "Virtual environment created"
}

# Activate venv
Write-Log "INFO" "Activating virtual environment..."

try {
    & $VenvActivate
    Write-Log "OK" "Virtual environment activated"
}
catch {
    Write-Log "ERROR" "Failed to activate virtual environment"
    Read-Host "Press Enter to exit"
    exit 1
}

# Update pip
Write-Log "INFO" "Updating pip..."
python -m pip install --upgrade pip -q 2>$null
Write-Log "OK" "pip updated"

# ============================================================
# Step 3: Check and Install Dependencies
# ============================================================

Write-Header "Step 3: Checking Dependencies"

# Check PyInstaller
Write-Log "INFO" "Checking PyInstaller..."
if (Test-PythonModule "PyInstaller") {
    Write-Log "OK" "PyInstaller is installed"
}
else {
    Write-Log "INFO" "Installing PyInstaller..."
    pip install pyinstaller -q
    Write-Log "OK" "PyInstaller installed"
}

# Define dependencies to check
$Dependencies = @{
    "numpy" = @{ Package = "numpy==1.26.4"; Module = "numpy" }
    "opencv" = @{ Package = "opencv-python==4.8.1.78"; Module = "cv2" }
    "pillow" = @{ Package = "Pillow"; Module = "PIL" }
    "cryptography" = @{ Package = "cryptography"; Module = "cryptography" }
    "pyperclip" = @{ Package = "pyperclip"; Module = "pyperclip" }
    "dlib" = @{ Package = $null; Module = "dlib" }
    "face_recognition" = @{ Package = "face-recognition"; Module = "face_recognition" }
}

$MissingDeps = @()

foreach ($dep in $Dependencies.Keys) {
    $module = $Dependencies[$dep].Module
    
    if (Test-PythonModule $module) {
        try {
            $version = python -c "import $module; print(getattr($module, '__version__', 'OK'))" 2>$null
            Write-Log "OK" "$dep : $version"
        }
        catch {
            Write-Log "OK" $dep
        }
    }
    else {
        Write-Log "WARNING" "$dep - NOT INSTALLED"
        $MissingDeps += $dep
    }
}

# Install missing dependencies
if ($MissingDeps.Count -gt 0) {
    Write-Host ""
    Write-Log "INFO" "Installing missing dependencies..."
    
    # Install numpy first (version locked for dlib compatibility)
    if ($MissingDeps -contains "numpy") {
        Write-Log "INFO" "Installing numpy 1.26.4 (dlib compatible)..."
        pip install numpy==1.26.4 -q
    }
    
    # Install opencv (version locked for numpy compatibility)
    if ($MissingDeps -contains "opencv") {
        Write-Log "INFO" "Installing opencv-python 4.8.1.78..."
        pip install opencv-python==4.8.1.78 -q
    }
    
    # Install dlib from wheel
    if ($MissingDeps -contains "dlib") {
        Write-Log "INFO" "Installing dlib from pre-built wheel..."
        
        if ($DlibWheels.ContainsKey($PyMinor.ToString())) {
            $wheelUrl = $DlibWheels[$PyMinor.ToString()]
            Write-Log "INFO" "Downloading wheel for Python 3.$PyMinor..."
            pip install $wheelUrl -q
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "OK" "dlib installed from wheel"
            }
            else {
                Write-Log "ERROR" "Failed to install dlib from wheel"
                Write-Log "INFO" "Trying to build from source (requires CMake + VS Build Tools)..."
                pip install dlib -q
            }
        }
        else {
            Write-Log "WARNING" "No pre-built dlib wheel for Python 3.$PyMinor"
            Write-Log "INFO" "Trying to build from source..."
            pip install dlib -q
        }
    }
    
    # Install other packages
    foreach ($dep in $MissingDeps) {
        if ($dep -notin @("numpy", "opencv", "dlib", "face_recognition")) {
            $package = $Dependencies[$dep].Package
            if ($package) {
                Write-Log "INFO" "Installing $package..."
                pip install $package -q
            }
        }
    }
    
    # Install face-recognition last (depends on dlib)
    if ($MissingDeps -contains "face_recognition") {
        Write-Log "INFO" "Installing face-recognition..."
        pip install face-recognition -q
    }
    
    Write-Log "OK" "Dependencies installed"
}

# ============================================================
# Step 4: Check Required Files
# ============================================================

Write-Header "Step 4: Checking Required Files"

$FilesOK = $true

foreach ($file in $RequiredFiles) {
    if (Test-Path $file) {
        Write-Log "OK" $file
    }
    else {
        Write-Log "ERROR" "$file - NOT FOUND"
        $FilesOK = $false
    }
}

# Check icon
if (Test-Path $IconFile) {
    Write-Log "OK" "Icon: $IconFile"
    $HasIcon = $true
}
else {
    Write-Log "WARNING" "No $IconFile found - using default icon"
    $HasIcon = $false
}

# Check optional files
Write-Host ""
Write-Log "INFO" "Checking optional files..."

foreach ($file in $OptionalDataFiles) {
    if (Test-Path $file) {
        Write-Log "OK" "$file (will be included)"
    }
    else {
        Write-Log "INFO" "$file (not found, skipping)"
    }
}

if (-not $FilesOK) {
    Write-Host ""
    Write-Log "ERROR" "Missing required files. Cannot build."
    Read-Host "Press Enter to exit"
    exit 1
}

# ============================================================
# Step 5: Test Camera and Face Recognition
# ============================================================

Write-Header "Step 5: Testing Camera & Face Recognition"

$TestScript = @"
import sys
print("Testing imports...")

try:
    import cv2
    print(f"[OK] OpenCV: {cv2.__version__}")
except Exception as e:
    print(f"[ERROR] OpenCV: {e}")
    sys.exit(1)

try:
    import numpy as np
    print(f"[OK] NumPy: {np.__version__}")
except Exception as e:
    print(f"[ERROR] NumPy: {e}")
    sys.exit(1)

try:
    import dlib
    print(f"[OK] dlib: {dlib.__version__}")
except Exception as e:
    print(f"[ERROR] dlib: {e}")
    sys.exit(1)

try:
    import face_recognition
    print("[OK] face_recognition")
except Exception as e:
    print(f"[ERROR] face_recognition: {e}")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
    print("[OK] cryptography")
except Exception as e:
    print(f"[ERROR] cryptography: {e}")
    sys.exit(1)

try:
    import pyperclip
    print("[OK] pyperclip")
except Exception as e:
    print(f"[ERROR] pyperclip: {e}")

# Test camera
print("\nTesting camera...")
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    cap.release()
    if ret:
        print(f"[OK] Camera working - Frame: {frame.shape}")
        
        # Test face detection
        print("\nTesting face detection...")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb)
        print(f"[OK] Face detection works - Faces found: {len(faces)}")
    else:
        print("[WARNING] Camera opened but cannot read frames")
else:
    print("[WARNING] Cannot open camera - face auth may not work in built app")

print("\n[OK] All tests passed!")
"@

$TestScript | Out-File -FilePath "test_build.py" -Encoding UTF8

Write-Log "INFO" "Running camera and face recognition tests..."
python test_build.py

$TestResult = $LASTEXITCODE

Remove-Item "test_build.py" -ErrorAction SilentlyContinue

if ($TestResult -ne 0) {
    Write-Host ""
    Write-Log "WARNING" "Some tests failed, but build will continue."
    Write-Log "INFO" "The app may have limited functionality."
    Write-Host ""
    
    $continue = Read-Host "Continue with build? [Y/N]"
    if ($continue -ne 'Y' -and $continue -ne 'y') {
        exit 1
    }
}

# ============================================================
# Step 6: Clean Previous Builds
# ============================================================

Write-Header "Step 6: Cleaning Previous Builds"

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Log "OK" "Removed build folder"
}

if (Test-Path $OutputFolder) {
    Remove-Item -Recurse -Force $OutputFolder
    Write-Log "OK" "Removed $OutputFolder folder"
}

Get-ChildItem -Filter "*.spec" | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Log "OK" "Removed $($_.Name)"
}

# ============================================================
# Step 7: Build Application
# ============================================================

Write-Header "Step 7: Building Application"

Write-Host "Building with Python $PyVersion..." -ForegroundColor Cyan
Write-Host "This may take 5-10 minutes. Please be patient..." -ForegroundColor Yellow
Write-Host ""

# Build the command
$BuildArgs = @(
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", $AppName,
    "--distpath", $OutputFolder
)

# Add icon
if ($HasIcon) {
    $BuildArgs += "--icon"
    $BuildArgs += $IconFile
}

# Add data files
foreach ($file in $DataFiles) {
    if (Test-Path $file) {
        $BuildArgs += "--add-data"
        $BuildArgs += "$file;."
    }
}

# Add optional data files
foreach ($file in $OptionalDataFiles) {
    if (Test-Path $file) {
        if (Test-Path $file -PathType Container) {
            $BuildArgs += "--add-data"
            $BuildArgs += "$file;$file"
        }
        else {
            $BuildArgs += "--add-data"
            $BuildArgs += "$file;."
        }
    }
}

# Add hidden imports
foreach ($import in $HiddenImports) {
    $BuildArgs += "--hidden-import"
    $BuildArgs += $import
}

# Add collect-all
foreach ($pkg in $CollectAll) {
    $BuildArgs += "--collect-all"
    $BuildArgs += $pkg
}

# Add main script
$BuildArgs += $MainScript

# Show build info
Write-Host "PyInstaller Arguments:" -ForegroundColor Gray
Write-Host "  --name $AppName" -ForegroundColor Gray
Write-Host "  --distpath $OutputFolder" -ForegroundColor Gray
if ($HasIcon) { Write-Host "  --icon $IconFile" -ForegroundColor Gray }
Write-Host "  + $($HiddenImports.Count) hidden imports" -ForegroundColor Gray
Write-Host "  + $($CollectAll.Count) collect-all packages" -ForegroundColor Gray
Write-Host ""

# Run PyInstaller
$process = Start-Process -FilePath "pyinstaller" -ArgumentList $BuildArgs -NoNewWindow -Wait -PassThru

if ($process.ExitCode -ne 0) {
    Write-Host ""
    Write-Header "BUILD FAILED!"
    Write-Log "ERROR" "PyInstaller returned exit code: $($process.ExitCode)"
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Missing dependencies" -ForegroundColor Gray
    Write-Host "  - Syntax errors in Python files" -ForegroundColor Gray
    Write-Host "  - Antivirus blocking the build" -ForegroundColor Gray
    Write-Host "  - Insufficient disk space" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# ============================================================
# Step 8: Post-Build Setup
# ============================================================

Write-Header "Step 8: Post-Build Setup"

# Create README
$ReadmeContent = @"
============================================================
    Anay's Password Vault v1.0
============================================================

Built with Python $PyVersion

INSTALLATION:
  No installation required! Just run $AppName.exe

FIRST TIME SETUP:
  1. Run the application
  2. Register your face (5 photos required)
  3. Set up your master password
  4. Optionally set up a Quick PIN for faster login

FEATURES:
  * Secure password storage (AES-256 encryption)
  * Face recognition authentication
  * Liveness detection (blink detection - anti-spoofing)
  * Quick PIN unlock (when face confidence >= 80%)
  * Master password fallback
  * Search and filter passwords
  * Password generator

AUTHENTICATION MODES:
  1. Face Only (80%+ confidence) -> Quick PIN -> Unlock
  2. Face (60-80% confidence) -> Master Password -> Unlock  
  3. Master Password Only -> Unlock

FILES CREATED:
  The app creates a 'face_data' folder containing:
  - face_encodings.pkl (your face data)
  - settings.pkl (app settings)
  - quick_pin.pkl (encrypted PIN)
  - auth_log.txt (login history)

REQUIREMENTS:
  - Windows 10/11
  - Webcam (for face recognition)

SECURITY:
  - All passwords encrypted with AES-256
  - Face data stored locally only
  - No internet connection required
  - Liveness detection prevents photo attacks

TROUBLESHOOTING:
  - App doesn't start: Try running as Administrator
  - Camera not working: Check webcam connection
  - Face not detected: Ensure good lighting
  - Antivirus blocking: Add exception for the app

============================================================
    Created by Anay Ghatpande
============================================================
"@

$ReadmeContent | Out-File -FilePath "$OutputFolder\README.txt" -Encoding UTF8
Write-Log "OK" "Created README.txt"

# Copy face_data if exists and has data
if (Test-Path "face_data\face_encodings.pkl") {
    Copy-Item -Recurse -Force "face_data" "$OutputFolder\face_data"
    Write-Log "OK" "Copied face_data folder (with registered faces)"
}
elseif (Test-Path "face_data") {
    New-Item -ItemType Directory -Path "$OutputFolder\face_data" -Force | Out-Null
    Write-Log "OK" "Created empty face_data folder"
}

# Get file size
$ExePath = Join-Path $OutputFolder "$AppName.exe"
if (Test-Path $ExePath) {
    $FileSize = (Get-Item $ExePath).Length
    $SizeMB = [math]::Round($FileSize / 1MB, 1)
}
else {
    $SizeMB = 0
}

# ============================================================
# Build Complete
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    BUILD SUCCESSFUL!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "    Python Used : $PythonCmd (v$PyVersion)" -ForegroundColor White
Write-Host "    Application : $OutputFolder\$AppName.exe" -ForegroundColor White
Write-Host "    Size        : $SizeMB MB" -ForegroundColor White
Write-Host ""
Write-Host "    Output folder contents:" -ForegroundColor Gray

Get-ChildItem $OutputFolder | ForEach-Object {
    $size = if ($_.PSIsContainer) { "<DIR>" } else { "$([math]::Round($_.Length / 1KB, 1)) KB" }
    Write-Host "      - $($_.Name) ($size)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Ask to run
$RunApp = Read-Host "Run the app now? [Y/N]"
if ($RunApp -eq 'Y' -or $RunApp -eq 'y') {
    Write-Log "INFO" "Starting application..."
    Start-Process $ExePath
}

# Ask to open folder
$OpenFolder = Read-Host "Open output folder? [Y/N]"
if ($OpenFolder -eq 'Y' -or $OpenFolder -eq 'y') {
    Start-Process "explorer.exe" -ArgumentList $OutputFolder
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    Build completed successfully!" -ForegroundColor Cyan
Write-Host "    You can now share the '$OutputFolder' folder." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"