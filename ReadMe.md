# Password Vault

[![CI](https://github.com/anayghatpande/password_manager/actions/workflows/ci.yml/badge.svg)](https://github.com/anayghatpande/password_manager/actions/workflows/ci.yml)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An offline password manager with **AES-256 encryption**, **face recognition unlock**, and **recovery codes** — built with Python & Tkinter.

---

## Features

- **AES-256 encryption** — all passwords encrypted with `cryptography`'s Fernet (PBKDF2-derived keys)
- **Face recognition unlock** — 3-tier authentication using OpenCV LBPH + Haar cascades
  - **Full confidence** (< 60 distance) → auto-unlock without master password
  - **Partial confidence** (60–70) → master password still required
  - **Failed** (≥ 70) → fallback to master password or recovery code
- **Recovery codes** — 5 one-time codes generated at setup; each code PBKDF2-hashed and one-time-use
- **Password generator** — cryptographically secure (`secrets` module), customizable length
- **Search & filter** — instant vault search
- **Fully offline** — no internet connection required; all data stays local

---

## Quick Start

### Prerequisites

- **Python 3.7 – 3.11**
- **Webcam** (for face recognition)

### Installation

```bash
git clone https://github.com/anayghatpande/password_manager.git
cd password_manager
pip install -r requirements.txt
```

### Run

```bash
python gui_app.py
```

### Build Executable

```powershell
.\app_builder.ps1
```

The compiled `.exe` will be placed in the `exported_app/` directory.

---

## First-Time Setup

1. Launch the application
2. Enroll your face (50 samples captured with liveness checks)
3. Set a master password
4. Save your **recovery codes** — they are the only way to reset a forgotten password

---

## Authentication Modes

| Mode | Condition | Result |
|------|-----------|--------|
| Face only | Confidence < 60 | Unlock vault directly |
| Face + password | 60 ≤ confidence < 70 | Unlock after master password |
| Master password | Face fails or unavailable | Unlock with password |
| Recovery code | Password forgotten | 5 one-time codes available |

---

## Files Created

| File | Purpose |
|------|---------|
| `password_vault.enc` | Encrypted vault (AES-256) |
| `master.hash` | PBKDF2-hashed master password |
| `vault.salt` | Salt for key derivation |
| `recovery_codes.json` | Hashed one-time recovery codes |
| `face_vault_key.enc` | Encrypted vault key (face-linked) |
| `face_data/` | OpenCV LBPH training data |

---

## Security

- **Passwords**: encrypted with `cryptography.fernet` (AES-256-CBC + HMAC-SHA256)
- **Key derivation**: PBKDF2-HMAC-SHA256 with 600,000 iterations
- **Face data**: processed locally, never transmitted
- **Recovery codes**: PBKDF2-hashed with per-code salt; one-time-use
- **No telemetry**: fully offline, no network calls

---

## Development

```bash
# Install dev dependencies
pip install pytest

# Run tests
python -m pytest tests/ -v
```

Pull requests are welcome. The CI pipeline (`main` branch) runs tests on Python 3.9–3.11.

---

## License

MIT
