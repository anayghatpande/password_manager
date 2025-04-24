import getpass
from vault_core import derive_key, load_vault, save_vault, verify_master_password
# Testing platform for the password vault
def main():
    print("🔐 Welcome to your password vault.")
    master_password = getpass.getpass("Enter master password: ")

    if not verify_master_password(master_password):
        print("❌ Incorrect master password.")
        return

    key = derive_key(master_password)
    try:
        vault = load_vault(key)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    while True:
        print("\n📁 Stored Services:")
        if vault:
            for idx, svc in enumerate(vault, 1):
                print(f"{idx}. {svc}")
        else:
            print("  (No entries yet)")

        print("\nOptions:")
        print("1. View password")
        print("2. Add new entry")
        print("3. Exit")

        choice = input("Choose an option (1-3): ")

        if choice == "1":
            service = input("Enter service name to view: ")
            entry = vault.get(service)
            if entry:
                print(f"\n🔎 Username: {entry['username']}")
                print(f"🔐 Password: {entry['password']}")
            else:
                print("❌ Service not found.")

        elif choice == "2":
            service = input("New service name: ")
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            vault[service] = {"username": username, "password": password}
            save_vault(vault, key)
            print("✅ Saved.")

        elif choice == "3":
            print("👋 Exiting vault. Stay safe.")
            break

        else:
            print("❓ Invalid option.")

if __name__ == "__main__":
    main()
