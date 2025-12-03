# Build the password manager in exe file
- Make sure you have installed python 3.7.9 on your system.
- Before running the app run ```pip install -r requirements.txt```
- Run ```.\app_builder.ps1 ``` to export the app into .exe

Enjoy the offline password manager! :D


## Password Vault v1.0


Built with Python 3.9.13

INSTALLATION:
  No installation required! Just run PasswordVault.exe

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


