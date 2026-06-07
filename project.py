import os
import string
import json
import hashlib
import secrets
import getpass
import time
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


PASSWORD_FILE = "passwords.json"
MASTER_FILE = "master.json"

_session_password = None


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# similar to the sha256sum in linux.
# salt is the random data we add to the password to make it harder to be decryoted
# we iterate(hash once and once again) 100,000 in the following function.
def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100*1000).hex()


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
    with open(PASSWORD_FILE, "wb") as file:
        file.write(token)


def decrypt_passwords(master_password, salt):
    """ This function reads the binaries of the password file and returns the resulting json as a dictionairy."""
    try:
        with open(PASSWORD_FILE, "rb") as file:
            token = file.read()
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


def authenticate_user():
    global _session_password

    if not os.path.exists(MASTER_FILE):
        print("First time setup. Create a master password.")
        password = getpass.getpass("New master password: ")
        salt = secrets.token_bytes(16)
        file_salt = secrets.token_bytes(16)
        record = {
            "salt": salt.hex(),
            "hash": hash_password(password, salt),
            "file_salt": file_salt.hex(),
        }
        with open(MASTER_FILE, "w") as file:
            json.dump(record, file)
        print("Master password set.")
        _session_password = password
        return True

    with open(MASTER_FILE) as file:
        record = json.load(file)
    salt = bytes.fromhex(record["salt"])
    attempt = getpass.getpass("Master password: ")
    if hash_password(attempt, salt) == record["hash"]:
        _session_password = attempt
        return True
    return False


def load_passwords():
    global _session_password
    salt = _get_file_salt()
    return decrypt_passwords(_session_password, salt)


def save_password(service, password):
    global _session_password
    passwords = load_passwords()
    passwords[service] = password
    salt = _get_file_salt()
    encrypt_passwords(passwords, _session_password, salt)


def delete_password(service):
    global _session_password
    passwords = load_passwords()
    if service not in passwords:
        return False
    del passwords[service]
    salt = _get_file_salt()
    encrypt_passwords(passwords, _session_password, salt)
    return True


def generate_passwd(passwd_len):
    eligible_chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(eligible_chars) for _ in range(passwd_len))


def check_passwd_strength(passwd: str):
    """ This function decreases the passwd strength level based on a particular logic I implemented."""
    points = 100
    if len(passwd) < 4:
        raise ValueError("length must be at least 4")
    if len(passwd) < 8:
        points -= (8 - len(passwd)) * 10

    repetition = 0
    for i in range(len(passwd)):
        for j in range(i):
            if passwd[i] == passwd[j]:
                repetition += 1
    points -= 5 * repetition

    return max(points, 0)


def menu():
    if not authenticate_user():
        print("Authentication failed.")
        return

    while True:
        print("\n1. Add password")
        print("2. View passwords")
        print("3. Delete password")
        print("4. Generate password")
        print("5. Quit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            clear_screen()
            service = input("Service: ").strip()
            if not service:
                print("Service cannot be empty.")
                time.sleep(2)
                continue
            password = getpass.getpass("Password: ").strip()
            if not password:
                print("Password cannot be empty.")
                time.sleep(2)
                continue
            save_password(service, password)
            clear_screen()
            print("Saved.")
        elif choice == "2":
            clear_screen()
            try:
                passwords = load_passwords()
            except Exception as e:
                print(f"Error loading passwords: {e}")
                time.sleep(2)
                continue
            else:
                for service, password in passwords.items():
                    print(f"{service}: {password}")
                time.sleep(2)
        elif choice == "3":
            clear_screen()
            try:
                passwords = load_passwords()
            except Exception as e:
                print(f"Error loading passwords: {e}")
                time.sleep(2)
                continue
            service = input("Service to delete: ").strip()
            if delete_password(service):
                print("Deleted.")
            else:
                print("Service not found.")
        elif choice == "4":
            clear_screen()
            try:
                length = int(input("Length: ").strip())
            except ValueError:
                print("Please enter a valid number.")
                time.sleep(2)
                continue
            new_password = generate_passwd(length)
            try:
                print(f"Generated(Copy it): {new_password}")
                print(f"Strength: {check_passwd_strength(new_password)}%")
            except ValueError:
                print("Password must be at least 4 chars long")
        elif choice == "5":
            clear_screen()
            break
        else:
            print("❌ Invalid option.\n")
            time.sleep(2)
            clear_screen()


    global _session_password
    _session_password = None


def main():
    clear_screen()
    menu()


if __name__ == "__main__":
    main()
