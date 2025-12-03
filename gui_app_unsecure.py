import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from tkinter import font
import pyperclip
from vault_core import derive_key, load_vault, save_vault, verify_master_password
from password_generator import generate_password


class PasswordManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Anay's Password Vault")
        self.vault = {}
        self.key = None
        self.revealed_rows = {}  # Track revealed state

        self.font = ("Helvetica", 14)
        self.primary_color = "#4CAF50"  # Green
        self.bg_color = "#f4f4f9"  # Light grey background
        self.button_color = "#FF5722"  # Deep orange
        self.header_color = "#3C9D9B"  # Teal for header

        self.root.configure(bg=self.bg_color)
        self.login_screen()

    def login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create a frame for the master password screen
        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(pady=100, padx=20, fill="both", expand=True)

        # Header
        header = tk.Label(frame, text="🔐 Welcome to Anay's Password Vault", font=("Helvetica", 18, "bold"), fg=self.header_color, bg=self.bg_color)
        header.pack(pady=20)

        # Instructions label
        instructions = tk.Label(frame, text="Enter your master password to proceed", font=("Helvetica", 12), bg=self.bg_color)
        instructions.pack(pady=10)

        # Entry widget for the master password
        self.master_password_var = tk.StringVar()
        pw_entry = tk.Entry(frame, textvariable=self.master_password_var, show="*", font=self.font, width=25, bd=2, relief="solid")
        pw_entry.pack(pady=10)

        # Submit button
        submit_button = tk.Button(frame, text="Submit", command=self.verify_master_password, bg=self.primary_color, fg="white", font=("Helvetica", 12, "bold"), relief="raised", width=20)
        submit_button.pack(pady=20)

    def verify_master_password(self):
        pw = self.master_password_var.get()
        if not pw:
            messagebox.showerror("Error", "❌ Please enter a password.")
            return

        if not verify_master_password(pw):
            messagebox.showerror("Access Denied", "❌ Incorrect master password.")
            return

        self.key = derive_key(pw)
        try:
            self.vault = load_vault(self.key)
        except Exception:
            messagebox.showerror("Error", "❌ Vault corrupted or invalid password.")
            return

        self.main_screen()

    def main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # Search Bar
        search_frame = tk.Frame(self.root, bg=self.bg_color)
        search_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(search_frame, text="🔍 Search:", font=self.font, bg=self.bg_color).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=self.font, bd=2)
        search_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_tree())

        # Treeview
        self.tree = ttk.Treeview(self.root, columns=("Service", "Username", "Password", "Action"), show="headings")
        self.tree.heading("Service", text="Service")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Password", text="Password")
        self.tree.heading("Action", text="Action")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.refresh_tree()

        # Buttons
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="➕ Add New", command=self.add_entry, bg=self.primary_color, fg="white", font=self.font, relief="raised").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="📋 Copy Password", command=self.copy_selected_password, bg=self.button_color, fg="white", font=self.font, relief="raised").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="🔁 Generate & Copy", command=self.gen_and_copy, bg=self.primary_color, fg="white", font=self.font, relief="raised").grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self.delete_selected, bg="#f44336", fg="white", font=self.font, relief="raised").grid(row=0, column=3, padx=5)

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        query = self.search_var.get().lower().strip()

        for service, creds in self.vault.items():
            if query in service.lower() or query in creds["username"].lower():
                is_revealed = self.revealed_rows.get(service, False)
                password = creds["password"] if is_revealed else "●●●●●●●●"
                action = "Hide" if is_revealed else "Show"

                # Use service as the iid, and set all 4 columns
                self.tree.insert("", "end", iid=service, values=(service, creds["username"], password, action))

        self.tree.bind("<ButtonRelease-1>", self.toggle_password)


    def toggle_password(self, event=None):
        selected_item = self.tree.selection()

        if not selected_item:
            return

        item_id = selected_item[0]
        col = self.tree.identify_column(event.x)

        if col != "#4":  # Action column is #4
            return

        service_key = item_id  # The iid is the service name

        if service_key not in self.vault:
            messagebox.showerror("Error", f"Service '{service_key}' not found in vault.")
            return

        is_revealed = self.revealed_rows.get(service_key, False)

        if is_revealed:
            self.revealed_rows[service_key] = False
            self.tree.item(service_key, values=(
                service_key,
                self.vault[service_key]["username"],
                "●●●●●●●●",
                "Show"
            ))
        else:
            self.revealed_rows[service_key] = True
            self.tree.item(service_key, values=(
                service_key,
                self.vault[service_key]["username"],
                self.vault[service_key]["password"],
                "Hide"
            ))


    def add_entry(self):
        service = simpledialog.askstring("Service Name", "Enter service name:")
        if not service: return
        username = simpledialog.askstring("Username", "Enter username:")
        if username is None: return
        password = simpledialog.askstring("Password", "Enter password:", show="*")
        if password is None: return

        self.vault[service] = {"username": username, "password": password}
        save_vault(self.vault, self.key)
        self.refresh_tree()

    def copy_selected_password(self):
        selected = self.tree.focus()
        if selected:
            pw = self.vault[selected]["password"]
            pyperclip.copy(pw)
            messagebox.showinfo("Copied", f"🔐 Password for '{selected}' copied to clipboard.")
        else:
            messagebox.showwarning("No selection", "Please select an entry.")

    def gen_and_copy(self):
        pwd = generate_password()
        pyperclip.copy(pwd)
        messagebox.showinfo("Generated", f"Password copied to clipboard:\n\n{pwd}")

    def delete_selected(self):
        selected = self.tree.focus()
        if selected:
            confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete '{selected}'?")
            if confirm:
                del self.vault[selected]
                save_vault(self.vault, self.key)
                self.refresh_tree()
                messagebox.showinfo("Deleted", f"'{selected}' was deleted from the vault.")
        else:
            messagebox.showwarning("No selection", "Please select an entry to delete.")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x500")  # Increased resolution
    app = PasswordManagerGUI(root)
    root.mainloop()
