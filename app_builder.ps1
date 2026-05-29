# Change to the script's directory
cd (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Debug: Show working directory
Write-Host "Current Directory: $(Get-Location)"

# Build with PyInstaller spec file
pyinstaller PasswordVault.spec

# Copy the output to exported_app folder
if (Test-Path "dist\PasswordVault.exe") {
    New-Item -ItemType Directory -Force -Path "exported_app" | Out-Null
    Copy-Item "dist\PasswordVault.exe" "exported_app\PasswordVault.exe" -Force
    Write-Host "✅ Built: exported_app\PasswordVault.exe"
}
