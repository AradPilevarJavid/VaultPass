import os
import json
import hashlib
import secrets
import base64
import string
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


PASSWORD_FILE = "passwords.json"
MASTER_FILE = "master.json"

_session_password = None   # holds the master password during the session



# similar to the sha256sum in linux.
# salt is the random data we add to the password to make it harder to be decryoted
# we iterate(hash once and once again) 100,000 in the following function.
def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()


def derive_key(master_password, salt):
    """ This function converts a human password into a real encryption key. """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))


def encrypt_passwords(passwords, master_password, salt):
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    data = json.dumps(passwords).encode()
    token = fernet.encrypt(data)
    with open(PASSWORD_FILE, "wb") as f:
        f.write(token)


def decrypt_passwords(master_password, salt):
    """ This function reads the binaries of the password file and returns the resulting json as a dictionairy."""
    try:
        with open(PASSWORD_FILE, "rb") as f:
            token = f.read()
    except FileNotFoundError:
        return {}
    if not token:
        return {}
    key = derive_key(master_password, salt) # make a real encryption key out of a human password
    fernet = Fernet(key)
    data = fernet.decrypt(token)
    return json.loads(data.decode())


def _get_file_salt():
    with open(MASTER_FILE) as f:
        record = json.load(f)
    if "file_salt" not in record:
        record["file_salt"] = secrets.token_bytes(16).hex()
        with open(MASTER_FILE, "w") as f:
            json.dump(record, f)
        if os.path.exists(PASSWORD_FILE):
            try:
                with open(PASSWORD_FILE, "r") as pf:
                    plain = json.load(pf)
                encrypt_passwords(plain, _session_password, bytes.fromhex(record["file_salt"]))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    return bytes.fromhex(record["file_salt"])


def load_passwords():
    salt = _get_file_salt()
    return decrypt_passwords(_session_password, salt)


def save_password(service, password):
    passwords = load_passwords()
    passwords[service] = password
    salt = _get_file_salt()
    encrypt_passwords(passwords, _session_password, salt)


def delete_password(service):
    passwords = load_passwords()
    if service not in passwords:
        return False
    del passwords[service]
    salt = _get_file_salt()
    encrypt_passwords(passwords, _session_password, salt)
    return True


def generate_passwd(length):
    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))


def check_passwd_strength(passwd):
    if len(passwd) < 4:
        raise ValueError("length must be at least 4")
    points = 100
    if len(passwd) < 8:
        points -= (8 - len(passwd)) * 10
    repetition = 0
    for i in range(len(passwd)):
        for j in range(i):
            if passwd[i] == passwd[j]:
                repetition += 1
    points -= 5 * repetition
    return max(points, 0)


def is_master_created():
    """Return True if master.json exists (i.e. first-time setup already done)."""
    return os.path.exists(MASTER_FILE)


def authenticate_user(password):
    """
    Verify master password and set _session_password globally.
    If master.json does not exist, create it with the given password.
    Returns True on success, False on failure.
    """
    global _session_password
    try:
        if not is_master_created():
            # First-time setup
            salt = secrets.token_bytes(16)
            file_salt = secrets.token_bytes(16)
            record = {
                "salt": salt.hex(),
                "hash": hash_password(password, salt),
                "file_salt": file_salt.hex(),
            }
            with open(MASTER_FILE, "w") as f:
                json.dump(record, f)
            _session_password = password
            return True
        else:
            # Existing master – verify password
            with open(MASTER_FILE) as f:
                record = json.load(f)
            salt = bytes.fromhex(record["salt"])
            if hash_password(password, salt) == record["hash"]:
                _session_password = password
                return True
            return False
    except Exception:
        return False