Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    Starting Anay's Password Vault..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"
python gui_app.py
Read-Host "Press Enter to exit"
