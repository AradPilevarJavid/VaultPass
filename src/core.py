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


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()


def generate_passwd(length):
    chars = string.ascii_letters + string.digits + string.punctuation
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



# def check_passwd_strength(passwd: str) -> int:
#     """
#     Return a score from 0 (very weak) to 100 (excellent).
#     Rewards length and character class variety.
#     """
#     if len(passwd) < 4:
#         raise ValueError("length must be at least 4")

#     length = len(passwd)
#     length_score = min(length / 20, 1.0) * 50

#     classes = 0
#     if any(c.islower() for c in passwd):
#         classes += 1
#     if any(c.isupper() for c in passwd):
#         classes += 1
#     if any(c.isdigit() for c in passwd):
#         classes += 1
#     if any(c in string.punctuation for c in passwd):
#         classes += 1
#     variety_score = {0: 0, 1: 10, 2: 25, 3: 35, 4: 40}.get(classes, 40)

#     from collections import Counter
#     most_common_count = Counter(passwd).most_common(1)[0][1]
#     repeat_ratio = most_common_count / length
#     penalty = max(0, (repeat_ratio - 0.5) * 20)  

#     score = length_score + variety_score - penalty
#     return max(0, min(100, round(score)))




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
        data = fernet.decrypt(token)
        return json.loads(data.decode())

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
