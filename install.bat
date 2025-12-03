@echo off
SETLOCAL EnableDelayedExpansion

title Anay's Password Vault - Installer
color 0A

echo.
echo ============================================================
echo     Anay's Password Vault - Dependency Installer
echo     Face Recognition + Password Protection
echo ============================================================
echo.

:: ============================================================
:: Detect ALL Python Installations
:: ============================================================
echo [INFO] Scanning for Python installations...
echo.

set PYTHON_COUNT=0

:: Array to store found Python commands and versions
set "PYTHON_LIST="

:: List of possible Python commands/aliases to check
set PYTHON_ALIASES=python python3 python3.7 python3.8 python3.9 python3.10 python3.11 python3.12 python37 python38 python39 python310 python311 python312

:: Check each alias
for %%P in (%PYTHON_ALIASES%) do (
    %%P --version >nul 2>&1
    if !errorLevel! equ 0 (
        for /f "tokens=2" %%V in ('%%P --version 2^>^&1') do (
            set /a PYTHON_COUNT+=1
            set "PYTHON_CMD_!PYTHON_COUNT!=%%P"
            set "PYTHON_VER_!PYTHON_COUNT!=%%V"
            echo   [!PYTHON_COUNT!] %%P --^> Python %%V
        )
    )
)

:: Check 'py' launcher with different versions
for %%V in (3 3.7 3.8 3.9 3.10 3.11 3.12) do (
    py -%%V --version >nul 2>&1
    if !errorLevel! equ 0 (
        for /f "tokens=2" %%X in ('py -%%V --version 2^>^&1') do (
            set /a PYTHON_COUNT+=1
            set "PYTHON_CMD_!PYTHON_COUNT!=py -%%V"
            set "PYTHON_VER_!PYTHON_COUNT!=%%X"
            echo   [!PYTHON_COUNT!] py -%%V --^> Python %%X
        )
    )
)

:: Check if any Python was found
if %PYTHON_COUNT% equ 0 (
    echo.
    echo [ERROR] No Python installation found!
    echo.
    echo         Please install Python from: https://www.python.org/downloads/
    echo         Supported versions: Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
    echo.
    echo         Make sure to check "Add Python to PATH" during installation!
    echo.
    set /p MANUAL_PYTHON="Or enter Python command manually (press Enter to exit): "
    
    if "!MANUAL_PYTHON!"=="" (
        pause
        exit /b 1
    )
    
    :: Validate manual input
    !MANUAL_PYTHON! --version >nul 2>&1
    if !errorLevel! neq 0 (
        echo [ERROR] Invalid Python command: !MANUAL_PYTHON!
        pause
        exit /b 1
    )
    
    for /f "tokens=2" %%V in ('!MANUAL_PYTHON! --version 2^>^&1') do (
        set PYTHON_CMD=!MANUAL_PYTHON!
        set PYTHON_VERSION=%%V
    )
    goto :python_selected
)

:: ============================================================
:: Let User Select Python Version
:: ============================================================
echo.
echo ============================================================
echo     Select Python Version
echo ============================================================
echo.

if %PYTHON_COUNT% equ 1 (
    echo [INFO] Only one Python found. Using it automatically.
    set PYTHON_CMD=!PYTHON_CMD_1!
    set PYTHON_VERSION=!PYTHON_VER_1!
) else (
    echo Found %PYTHON_COUNT% Python installation(s).
    echo.
    echo Available options:
    echo.
    
    for /L %%i in (1,1,%PYTHON_COUNT%) do (
        echo   [%%i] !PYTHON_CMD_%%i! --^> Python !PYTHON_VER_%%i!
    )
    
    echo.
    echo   [0] Enter custom Python command
    echo.
    
    set /p SELECTION="Select Python version [1-%PYTHON_COUNT%]: "
    
    :: Validate selection
    if "!SELECTION!"=="0" (
        set /p CUSTOM_PYTHON="Enter Python command: "
        !CUSTOM_PYTHON! --version >nul 2>&1
        if !errorLevel! neq 0 (
            echo [ERROR] Invalid command: !CUSTOM_PYTHON!
            pause
            exit /b 1
        )
        for /f "tokens=2" %%V in ('!CUSTOM_PYTHON! --version 2^>^&1') do (
            set PYTHON_CMD=!CUSTOM_PYTHON!
            set PYTHON_VERSION=%%V
        )
    ) else if !SELECTION! geq 1 if !SELECTION! leq %PYTHON_COUNT% (
        set PYTHON_CMD=!PYTHON_CMD_%SELECTION%!
        set PYTHON_VERSION=!PYTHON_VER_%SELECTION%!
    ) else (
        echo [WARNING] Invalid selection. Using first option.
        set PYTHON_CMD=!PYTHON_CMD_1!
        set PYTHON_VERSION=!PYTHON_VER_1!
    )
)

:python_selected

:: Extract major and minor version
for /f "tokens=1,2,3 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
    set PY_PATCH=%%c
)

echo.
echo ============================================================
echo     Selected Python Configuration
echo ============================================================
echo.
echo     Command  : %PYTHON_CMD%
echo     Version  : %PYTHON_VERSION%
echo     Major    : %PY_MAJOR%
echo     Minor    : %PY_MINOR%
echo.
echo ============================================================

:: Version compatibility check
if %PY_MAJOR% LSS 3 (
    echo.
    echo [ERROR] Python 3.7 or higher is required!
    echo         You selected Python %PY_MAJOR%.%PY_MINOR%
    pause
    exit /b 1
)

if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 7 (
    echo.
    echo [ERROR] Python 3.7 or higher is required!
    echo         You selected Python %PY_MAJOR%.%PY_MINOR%
    pause
    exit /b 1
)

echo.
echo [OK] Python version is compatible!

:: ============================================================
:: Set dlib wheel URL based on Python version
:: ============================================================
set WHEEL_URL=
set WHEEL_FILE=

if "%PY_MINOR%"=="7" (
    set WHEEL_FILE=dlib-19.22.99-cp37-cp37m-win_amd64.whl
    set WHEEL_URL=https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp37-cp37m-win_amd64.whl
)
if "%PY_MINOR%"=="8" (
    set WHEEL_FILE=dlib-19.22.99-cp38-cp38-win_amd64.whl
    set WHEEL_URL=https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp38-cp38-win_amd64.whl
)
if "%PY_MINOR%"=="9" (
    set WHEEL_FILE=dlib-19.22.99-cp39-cp39-win_amd64.whl
    set WHEEL_URL=https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp39-cp39-win_amd64.whl
)
if "%PY_MINOR%"=="10" (
    set WHEEL_FILE=dlib-19.22.99-cp310-cp310-win_amd64.whl
    set WHEEL_URL=https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp310-cp310-win_amd64.whl
)
if "%PY_MINOR%"=="11" (
    set WHEEL_FILE=dlib-19.24.1-cp311-cp311-win_amd64.whl
    set WHEEL_URL=https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.1-cp311-cp311-win_amd64.whl
)
if "%PY_MINOR%"=="12" (
    set WHEEL_FILE=dlib-19.24.99-cp312-cp312-win_amd64.whl
    set WHEEL_URL=https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.99-cp312-cp312-win_amd64.whl
)

echo.
if defined WHEEL_URL (
    echo [OK] Pre-built dlib wheel available for Python 3.%PY_MINOR%
    echo     File: %WHEEL_FILE%
) else (
    echo [WARNING] No pre-built dlib wheel for Python 3.%PY_MINOR%
    echo          You may need Visual Studio Build Tools and CMake.
)

:: ============================================================
:: Upgrade pip
:: ============================================================
echo.
echo [INFO] Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] pip upgraded successfully!
) else (
    echo [WARNING] Could not upgrade pip, continuing...
)

:: ============================================================
:: Virtual Environment Setup
:: ============================================================
echo.
echo ============================================================
echo     Virtual Environment Setup
echo ============================================================
echo.
echo     Virtual environments isolate project dependencies.
echo     This is RECOMMENDED for avoiding conflicts.
echo.

set /p CREATE_VENV="Create virtual environment? [Y/N]: "

set USING_VENV=N

if /i "%CREATE_VENV%"=="Y" (
    if exist "venv" (
        echo.
        echo [INFO] Virtual environment 'venv' already exists.
        set /p USE_EXISTING="Use existing venv? [Y/N]: "
        
        if /i "!USE_EXISTING!"=="N" (
            echo [INFO] Removing old virtual environment...
            rmdir /s /q venv 2>nul
            echo [INFO] Creating new virtual environment...
            %PYTHON_CMD% -m venv venv
        )
    ) else (
        echo [INFO] Creating virtual environment...
        %PYTHON_CMD% -m venv venv
    )
    
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    
    if !errorLevel! equ 0 (
        echo [OK] Virtual environment activated!
        set USING_VENV=Y
        
        :: Upgrade pip in venv
        python -m pip install --upgrade pip >nul 2>&1
        
        :: Store original command for run script
        set ORIGINAL_PYTHON_CMD=%PYTHON_CMD%
        set PYTHON_CMD=python
    ) else (
        echo [WARNING] Could not activate virtual environment.
        echo          Continuing with global installation...
        set USING_VENV=N
    )
) else (
    echo [INFO] Skipping virtual environment. Installing globally.
)

:: ============================================================
:: Install Basic Dependencies
:: ============================================================
echo.
echo ============================================================
echo     Installing Basic Dependencies
echo ============================================================
echo.

set BASIC_PACKAGES=numpy pillow pyperclip cryptography opencv-python

for %%P in (%BASIC_PACKAGES%) do (
    echo [INFO] Installing %%P...
    pip install %%P >nul 2>&1
    if !errorLevel! equ 0 (
        echo [OK] %%P installed successfully
    ) else (
        echo [ERROR] Failed to install %%P
    )
)

:: ============================================================
:: Install dlib
:: ============================================================
echo.
echo ============================================================
echo     Installing dlib for Python 3.%PY_MINOR%
echo ============================================================
echo.

set DLIB_INSTALLED=0

if defined WHEEL_URL (
    echo [INFO] Method 1: Installing from pre-built wheel...
    echo [INFO] URL: %WHEEL_URL%
    echo.
    echo        Downloading and installing. Please wait...
    echo.
    
    pip install "%WHEEL_URL%"
    
    if !errorLevel! equ 0 (
        echo.
        echo [OK] dlib installed successfully from pre-built wheel!
        set DLIB_INSTALLED=1
    ) else (
        echo.
        echo [WARNING] Direct URL installation failed.
        echo [INFO] Method 2: Downloading wheel file first...
        echo.
        
        :: Try using curl
        where curl >nul 2>&1
        if !errorLevel! equ 0 (
            echo [INFO] Using curl to download...
            curl -L -o "%WHEEL_FILE%" "%WHEEL_URL%" 2>nul
        )
        
        if not exist "%WHEEL_FILE%" (
            :: Try using PowerShell
            echo [INFO] Using PowerShell to download...
            powershell -Command "try { Invoke-WebRequest -Uri '%WHEEL_URL%' -OutFile '%WHEEL_FILE%' -UseBasicParsing } catch { exit 1 }" 2>nul
        )
        
        if exist "%WHEEL_FILE%" (
            echo [INFO] Download complete. Installing...
            pip install "%WHEEL_FILE%"
            if !errorLevel! equ 0 (
                echo [OK] dlib installed from downloaded wheel!
                set DLIB_INSTALLED=1
            ) else (
                echo [ERROR] Installation from downloaded wheel failed.
            )
            del "%WHEEL_FILE%" 2>nul
        ) else (
            echo [ERROR] Could not download wheel file.
        )
    )
) else (
    echo [WARNING] No pre-built wheel available for Python 3.%PY_MINOR%
)

:: Try building from source if wheel installation failed
if %DLIB_INSTALLED% equ 0 (
    echo.
    echo [INFO] Method 3: Attempting to build dlib from source...
    echo.
    
    :: Check if CMake is installed
    cmake --version >nul 2>&1
    if !errorLevel! equ 0 (
        echo [OK] CMake found. Building dlib from source...
        echo     This may take 10-15 minutes. Please be patient.
        echo.
        pip install dlib
        if !errorLevel! equ 0 (
            echo [OK] dlib built from source successfully!
            set DLIB_INSTALLED=1
        ) else (
            echo [ERROR] Failed to build dlib from source.
        )
    ) else (
        echo [WARNING] CMake not found. Cannot build from source.
    )
)

:: Show manual instructions if all methods failed
if %DLIB_INSTALLED% equ 0 (
    echo.
    echo ============================================================
    echo     DLIB INSTALLATION FAILED
    echo ============================================================
    echo.
    echo     All automatic installation methods failed.
    echo.
    echo     MANUAL INSTALLATION OPTIONS:
    echo.
    echo     Option A - Download wheel manually:
    echo       1. Visit: https://github.com/z-mahmud22/Dlib_Windows_Python3.x
    echo       2. Download: %WHEEL_FILE%
    echo       3. Run: pip install "path\to\%WHEEL_FILE%"
    echo.
    echo     Option B - Install build tools:
    echo       1. Install CMake: https://cmake.org/download/
    echo          (Check "Add CMake to PATH")
    echo       2. Install Visual Studio Build Tools:
    echo          https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo          (Select "Desktop development with C++")
    echo       3. Restart computer
    echo       4. Run: pip install dlib
    echo.
    echo ============================================================
    echo.
    set /p CONTINUE_WITHOUT_DLIB="Continue without dlib? [Y/N]: "
    if /i "!CONTINUE_WITHOUT_DLIB!"=="N" (
        echo.
        echo Installation cancelled.
        pause
        exit /b 1
    )
)

:: ============================================================
:: Install face-recognition
:: ============================================================
echo.
echo ============================================================
echo     Installing face-recognition
echo ============================================================
echo.

if %DLIB_INSTALLED% equ 1 (
    echo [INFO] Installing face-recognition...
    pip install face-recognition
    
    if !errorLevel! equ 0 (
        echo [OK] face-recognition installed successfully!
    ) else (
        echo [ERROR] Failed to install face-recognition
    )
) else (
    echo [WARNING] Skipping face-recognition (requires dlib)
    echo          Face authentication will not be available.
)

:: ============================================================
:: Install from requirements.txt
:: ============================================================
if exist "requirements.txt" (
    echo.
    echo ============================================================
    echo     Processing requirements.txt
    echo ============================================================
    echo.
    echo [INFO] Installing additional dependencies...
    pip install -r requirements.txt >nul 2>&1
    echo [OK] requirements.txt processed
)

:: ============================================================
:: Create run_app.bat
:: ============================================================
echo.
echo ============================================================
echo     Creating Launch Script
echo ============================================================
echo.

if /i "%USING_VENV%"=="Y" (
    (
        echo @echo off
        echo echo ============================================================
        echo echo     Starting Anay's Password Vault...
        echo echo ============================================================
        echo call venv\Scripts\activate.bat
        echo python gui_app.py
        echo pause
    ) > run_app.bat
    echo [OK] Created run_app.bat (with venv activation)
) else (
    (
        echo @echo off
        echo echo ============================================================
        echo echo     Starting Anay's Password Vault...
        echo echo ============================================================
        echo %PYTHON_CMD% gui_app.py
        echo pause
    ) > run_app.bat
    echo [OK] Created run_app.bat (using %PYTHON_CMD%)
)

:: ============================================================
:: Verify Installation
:: ============================================================
echo.
echo ============================================================
echo     Verifying Installation
echo ============================================================
echo.

set VERIFY_ERRORS=0
set VERIFY_WARNINGS=0

:: Test OpenCV
%PYTHON_CMD% -c "import cv2; print('[OK] OpenCV:', cv2.__version__)" 2>nul
if !errorLevel! neq 0 (
    echo [ERROR] OpenCV - NOT INSTALLED
    set /a VERIFY_ERRORS+=1
)

:: Test dlib
%PYTHON_CMD% -c "import dlib; print('[OK] dlib:', dlib.__version__)" 2>nul
if !errorLevel! neq 0 (
    echo [WARNING] dlib - NOT INSTALLED (face auth unavailable)
    set /a VERIFY_WARNINGS+=1
)

:: Test face-recognition
%PYTHON_CMD% -c "import face_recognition; print('[OK] face-recognition: installed')" 2>nul
if !errorLevel! neq 0 (
    echo [WARNING] face-recognition - NOT INSTALLED (face auth unavailable)
    set /a VERIFY_WARNINGS+=1
)

:: Test Pillow
%PYTHON_CMD% -c "from PIL import Image; print('[OK] Pillow: installed')" 2>nul
if !errorLevel! neq 0 (
    echo [ERROR] Pillow - NOT INSTALLED
    set /a VERIFY_ERRORS+=1
)

:: Test pyperclip
%PYTHON_CMD% -c "import pyperclip; print('[OK] pyperclip: installed')" 2>nul
if !errorLevel! neq 0 (
    echo [ERROR] pyperclip - NOT INSTALLED
    set /a VERIFY_ERRORS+=1
)

:: Test cryptography
%PYTHON_CMD% -c "from cryptography.fernet import Fernet; print('[OK] cryptography: installed')" 2>nul
if !errorLevel! neq 0 (
    echo [ERROR] cryptography - NOT INSTALLED
    set /a VERIFY_ERRORS+=1
)

:: ============================================================
:: Final Summary
:: ============================================================
echo.
echo ============================================================

if %VERIFY_ERRORS% equ 0 (
    if %VERIFY_WARNINGS% equ 0 (
        color 0A
        echo     INSTALLATION COMPLETE!
        echo ============================================================
        echo.
        echo     All packages installed successfully!
        echo.
        echo     Python: %PYTHON_CMD% (v%PYTHON_VERSION%)
    ) else (
        color 0E
        echo     INSTALLATION COMPLETE WITH WARNINGS
        echo ============================================================
        echo.
        echo     Core packages installed. %VERIFY_WARNINGS% optional package(s) missing.
        echo     Face authentication may not be available.
        echo.
        echo     Python: %PYTHON_CMD% (v%PYTHON_VERSION%)
    )
    
    echo.
    echo     To run the application:
    echo.
    echo       Option 1: Double-click run_app.bat
    echo.
    if /i "%USING_VENV%"=="Y" (
        echo       Option 2: Run these commands:
        echo                  venv\Scripts\activate
        echo                  python gui_app.py
    ) else (
        echo       Option 2: Run: %PYTHON_CMD% gui_app.py
    )
) else (
    color 0C
    echo     INSTALLATION FAILED
    echo ============================================================
    echo.
    echo     %VERIFY_ERRORS% required package(s) failed to install.
    echo     %VERIFY_WARNINGS% optional package(s) missing.
    echo.
    echo     Please check the error messages above and try:
    echo       1. Running the script as Administrator
    echo       2. Checking your internet connection
    echo       3. Installing packages manually with pip
)

echo.
echo ============================================================
echo.

pause
ENDLOCAL