#!/usr/bin/env python3
import sys
import getpass
import time
import os
from core import (
    load_passwords,
    save_password,
    delete_password,
    generate_passwd,
    check_passwd_strength,
    authenticate_user,
    is_master_created,
    _session_password,
)

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def terminal_menu():
    if _session_password is None:
        print("Not authenticated.")
        return
    while True:
        print("\n1️⃣  Add password ➕")
        print("2️⃣  View passwords 👁️")
        print("3️⃣  Delete password 🗑️")
        print("4️⃣  Generate password 🔑")
        print("5️⃣  Quit 🚪")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            clear_screen()
            service = input("Service: ").strip()
            if not service:
                print("❌ Service cannot be empty.")
                time.sleep(2)
                continue
            password = getpass.getpass("Password: 🔒 ").strip()
            if not password:
                print("❌ Password cannot be empty.")
                time.sleep(2)
                continue
            save_password(service, password)
            clear_screen()
            print("✅ Saved.")
        elif choice == "2":
            clear_screen()
            try:
                passwords = load_passwords()
            except Exception as e:
                print(f"⚠️ Error loading: {e}")
                time.sleep(2)
                continue
            if not passwords:
                print("No passwords stored.")
            else:
                for s, p in passwords.items():
                    print(f"🔐 {s}: {p}")
            input("\nPress Enter...")
            clear_screen()
        elif choice == "3":
            clear_screen()
            service = input("Service to delete: 🗑️ ").strip()
            if delete_password(service):
                print("✅ Deleted.")
            else:
                print("❌ Not found.")
            time.sleep(2)
            clear_screen()
        elif choice == "4":
            clear_screen()
            try:
                length = int(input("Length: 📏 ").strip())
            except ValueError:
                print("❌ Invalid number.")
                time.sleep(2)
                continue
            new_password = generate_passwd(length)
            try:
                print(f"🔑 Generated: {new_password}")
                print(f"📊 Strength: {check_passwd_strength(new_password)}%")
            except ValueError:
                print("❌ Length must be at least 4")
            input("\nPress Enter...")
            clear_screen()
        elif choice == "5":
            clear_screen()
            break
        else:
            print("❌ Invalid.")
            time.sleep(2)
            clear_screen()

def main():
    clear_screen()
    gui_mode = "--gui" in sys.argv

    # ----- Authentication -----
    if not is_master_created():
        print("First time setup. Create a master password.")
        pwd = getpass.getpass("New master password: ")
        if len(pwd) < 4:
            print("Password must be at least 4 characters.")
            return
        if not authenticate_user(pwd):
            print("Authentication failed.")
            return
        print("Master password set.")
    else:
        pwd = getpass.getpass("Master password: ")
        if not authenticate_user(pwd):
            print("❌ Authentication failed.")
            return

    # ----- Launch appropriate interface -----
    if gui_mode:
        try:
            from ui import run_gui
            print("Starting GUI...")
            run_gui()
        except ImportError as e:
            print(f"Failed to import ui: {e}")
            print("Make sure ui.py and core.py are in the same folder.")
        except Exception as e:
            print(f"Unexpected error when starting GUI: {e}")
    else:
        terminal_menu()

if __name__ == "__main__":
    main()
