import os
import json
import hashlib
import secrets
import base64
import string
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

PASSWORD_FILE = "passwords.json"
MASTER_FILE = "master.json"


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()


# def generate_passwd(length):
#     chars = string.ascii_letters + string.digits + string.punctuation
#     return "".join(secrets.choice(chars) for _ in range(length))


def generate_passwd(length, use_upper=True, use_lower=True,
                    use_digits=True, use_punctuation=True):
    """Generate a password of given length from selected character sets."""
    chars = ''
    if use_upper:
        chars += string.ascii_uppercase
    if use_lower:
        chars += string.ascii_lowercase
    if use_digits:
        chars += string.digits
    if use_punctuation:
        chars += string.punctuation

    if not chars:
        chars = string.ascii_letters + string.digits

    return "".join(secrets.choice(chars) for _ in range(length))


def check_passwd_strength(passwd):
    if len(passwd) < 4:
        raise ValueError("length must be at least 4")
    points = 100
    if len(passwd) < 8:
        points -= (8 - len(passwd)) * 10
    if len(passwd) > 16:
        return 100
    seen = {}
    repetition = 0
    for ch in passwd:
        if ch in seen:
            repetition += 1
        seen[ch] = True
    points -= 5 * repetition
    return max(points, 0)


class Vault:
    def __init__(self, master_password):
        self._master_password = master_password

    @classmethod
    def create(cls, master_password):
        salt = secrets.token_bytes(16)
        file_salt = secrets.token_bytes(16)
        record = {
            "salt": salt.hex(),
            "hash": hash_password(master_password, salt),
            "file_salt": file_salt.hex(),
        }
        with open(MASTER_FILE, "w") as f:
            json.dump(record, f)
        return cls(master_password)

    @classmethod
    def login(cls, master_password):
        if not os.path.exists(MASTER_FILE):
            return None
        with open(MASTER_FILE) as f:
            record = json.load(f)
        salt = bytes.fromhex(record["salt"])
        if hash_password(master_password, salt) == record["hash"]:
            return cls(master_password)
        return None

    @staticmethod
    def is_master_created():
        return os.path.exists(MASTER_FILE)

    @staticmethod
    def _derive_key(master_password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

    def _get_file_salt(self):
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
                    self._encrypt_passwords(plain, bytes.fromhex(record["file_salt"]))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
        return bytes.fromhex(record["file_salt"])

    def _encrypt_passwords(self, passwords, salt):
        key = self._derive_key(self._master_password, salt)
        fernet = Fernet(key)
        data = json.dumps(passwords).encode()
        token = fernet.encrypt(data)
        with open(PASSWORD_FILE, "wb") as f:
            f.write(token)

    def _decrypt_passwords(self, salt):
        try:
            with open(PASSWORD_FILE, "rb") as f:
                token = f.read()
        except FileNotFoundError:
            return {}
        if not token:
            return {}
        key = self._derive_key(self._master_password, salt)
        fernet = Fernet(key)
        try:
            data = fernet.decrypt(token)
            return json.loads(data.decode())
        except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def load_passwords(self):
        salt = self._get_file_salt()
        return self._decrypt_passwords(salt)

    def save_password(self, service, password):
        passwords = self.load_passwords()
        passwords[service] = password
        salt = self._get_file_salt()
        self._encrypt_passwords(passwords, salt)

    def delete_password(self, service):
        passwords = self.load_passwords()
        if service not in passwords:
            return False
        del passwords[service]
        salt = self._get_file_salt()
        self._encrypt_passwords(passwords, salt)
        return True
