
# 🔐 VaultPass

VaultPass is a simple, offline password manager with a graphical interface built in Python.  
It stores your passwords locally in an encrypted file, protected by a master password.

## ✨ Features

- **Master password protection** – Unlock your vault with a single strong password.
- **AES‑256 encryption** – All stored passwords are encrypted using Fernet (AES‑128 in CBC mode with HMAC) with a key derived via PBKDF2‑SHA256.
- **Atomic file writes** – Data is never left in a broken state after crashes or power loss.
- **Password generator** – Create strong, random passwords with customisable length and character sets.
- **Strength meter** – Visual and numerical feedback on how strong a generated password is.
- **Clipboard integration** – Copy passwords with one click (clears automatically on exit).
- **Service management** – Add, delete, and search through your saved passwords.
- **Cross‑platform** – Works on Windows, macOS and Linux (uses system‑appropriate directories).

## 🚀 Installation

1. **Clone the repository**
   ```bash
    git clone https://github.com/AradPilevarJavid/VaultPass
    cd vaultpass
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   The required packages are:
   - `pygame` – GUI
   - `pyperclip` – clipboard access
   - `cryptography` – encryption and key derivation

3. **Run the application**
   ```bash
   python src/ui.py
   ```

> **Note**: On Linux you may need to install `xclip` or `xsel` for clipboard support (`sudo apt install xclip`).

## 📖 Usage

### First launch
The first time you launch VaultPass no vault exists. 
Click **Create Vault** and choose a strong master password(at least 4 chars).

### Main menu
After unlocking, you’ll see four options:
- **Add Password** – Manually save a service + password pair.
- **Manage Saved Passwords** – View, search, copy or delete entries.
- **Generate Password** – personalize your random password.Configure length and character sets, then copy or save the result.
- **Quit**

### Adding a password
1. Enter the service name (e.g. “guilan.ac.ir”).
2. Type or paste the password (hidden by default; click **Show** to view it).
3. Press **Save**.

### Generating a password
- Adjust the length with the slider (4–32 characters).
- Toggle character sets (uppercase, lowercase, digits, punctuation).
- Click **Generate** – the result and a strength meter appear.
- Use **Copy** to copy to clipboard or **Save to Vault** to jump to the Add screen with the generated password filled in.

### Managing saved passwords
- Use the search bar to filter entries.
- Select an entry and click **Delete** or **Copy**.
- Scroll through the list with the mouse wheel or the scrollbar.

## 🔒 Security

- The master password is hashed with **PBKDF2‑SHA256** (100,000 iterations) and a random salt stored in `master.json`.
- Passwords are encrypted with a **separate key** derived from the master password using PBKDF2‑SHA256 (200,000 iterations) and a second random salt.
- Encryption is performed with the **Fernet** recipe (AES‑128‑CBC + HMAC‑SHA256) which provides both confidentiality and integrity.
- All writes to disk are **atomic** (write to a temp file, then replace the original) to avoid corruption.
- Passwords **never** appear in plain text on disk and are only decrypted in memory when the vault is unlocked.

> ⚠️ **Keep your master password safe!** If you lose it, your stored passwords cannot be recovered.

## 📁 File locations

| Platform | Vault data directory |
|----------|----------------------|
| Windows  | `%APPDATA%\VaultPass` |
| Linux / macOS | `~/.vaultpass` |

The vault consists of two files:
- `master.json` – contains the master password hash and encryption salts.
- `passwords.json` – the encrypted password store.

## 🛠️ Project structure

```
VaultPass/
├── src/
│   ├── core.py       # encryption, storage, password generation, vault logic
│   ├── ui.py         # pygame GUI (the whole application interface)
├── requirements.txt
└── README.md
```

## 🧪 Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
---
Enjoy safe and simple password management! 🔐

*Made with ❤️ by Arad Pilevar Javid*
