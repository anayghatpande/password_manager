# Change to the script's directory
cd (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Debug: Show working directory
Write-Host "Current Directory: $(Get-Location)"

# Run PyInstaller
pyinstaller --onefile --windowed `
  --distpath "exported_app" `
  --add-data "master.hash;." `
  --add-data "vault_core.py;." `
  --add-data "password_generator.py;." `
  gui_app.py
