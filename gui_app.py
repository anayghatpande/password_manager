"""
Anay's Password Vault — Optimized GUI
Modern UI with face recognition, keyboard shortcuts, edit capabilities, inline password generation,
and a polished user experience.
"""

import os
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk, filedialog
import pyperclip
import time
import re
import csv
import sys
import logging
from vault_core import derive_key, load_vault, save_vault, verify_master_password, save_master_password, MASTER_HASH_FILE, generate_recovery_codes, verify_recovery_code, has_recovery_codes
from password_generator import generate_password
from face_auth import FaceAuthDialog, is_face_registered, save_vault_key_for_face, get_vault_key_from_face

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PasswordVault")

# --- Constants ---
APP_NAME = "Anay's Password Vault"
PRIMARY = "#4CAF50"
PRIMARY_DARK = "#388E3C"
SECONDARY = "#FF5722"
BG_LIGHT = "#F5F5F5"
BG_WHITE = "#FFFFFF"
HEADER_TEAL = "#3C9D9B"
DANGER = "#F44336"
WARNING = "#FF9800"
TEXT_DARK = "#212121"
TEXT_GREY = "#757575"
BORDER = "#E0E0E0"
CLIPBOARD_CLEAR_SECONDS = 10
AUTO_LOCK_MINUTES = 5
FACE_POLL_TIMEOUT = 60


class PasswordManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.configure(bg=BG_LIGHT)
        self.root.minsize(800, 500)
        self.root.geometry("950x600")

        self.vault = {}
        self.key = None
        self.master_pw = None
        self.revealed_rows = {}
        self.sort_column = None
        self.sort_reverse = False

        self.clipboard_timer = None
        self.last_activity_time = time.time()
        self.auto_lock_timer = None

        if sys.platform == "win32":
            self.font_title = ("Segoe UI", 18, "bold")
            self.font_subtitle = ("Segoe UI", 12)
            self.font_normal = ("Segoe UI", 11)
            self.font_small = ("Segoe UI", 9)
            self.font_button = ("Segoe UI", 11, "bold")
        elif sys.platform == "darwin":
            self.font_title = ("Helvetica Neue", 18, "bold")
            self.font_subtitle = ("Helvetica Neue", 12)
            self.font_normal = ("Helvetica Neue", 11)
            self.font_small = ("Helvetica Neue", 9)
            self.font_button = ("Helvetica Neue", 11, "bold")
        else:
            self.font_title = ("Ubuntu", 18, "bold")
            self.font_subtitle = ("Ubuntu", 12)
            self.font_normal = ("Ubuntu", 11)
            self.font_small = ("Ubuntu", 9)
            self.font_button = ("Ubuntu", 11, "bold")

        self._configure_styles()
        self.login_screen()
        self._start_auto_lock_check()

    def _clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def _update_status(self):
        count = len(self.vault)
        self.badge_entries.config(text=f"{count} entries")
        if count > 0:
            hidden = sum(1 for v in self.revealed_rows.values() if v)
            self.count_label.config(text=f"Showing {count} services ({hidden} passwords visible)")
        else:
            self.count_label.config(text="No entries yet. Add your first password!")

    def _update_activity(self):
        self.last_activity_time = time.time()

    def _start_auto_lock_check(self):
        def _check():
            if self.key is not None and self.master_pw is not None:
                elapsed = time.time() - self.last_activity_time
                remaining = AUTO_LOCK_MINUTES * 60 - elapsed
                if remaining <= 0:
                    self._lock_vault(auto=True)
                    return
                if remaining < 45 and remaining > 35:
                    self.status_text.set(f"⚠️ Auto-lock in {int(remaining)} seconds — move mouse or type to stay active")
                elif remaining < 35:
                    self.status_text.set(f"⚠️⚠️ Locking in {int(remaining)}s...")
            self.auto_lock_timer = self.root.after(5000, _check)
        self.auto_lock_timer = self.root.after(30000, _check)

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Treeview", background=BG_WHITE, foreground=TEXT_DARK, rowheight=34, fieldbackground=BG_WHITE, font=self.font_normal, borderwidth=0)
        style.map("Treeview", background=[("selected", "#E3F2FD")], foreground=[("selected", TEXT_DARK)])
        style.configure("Treeview.Heading", background=HEADER_TEAL, foreground=BG_WHITE, font=(self.font_normal[0], 11, "bold"), borderwidth=0, relief="flat")
        style.map("Treeview.Heading", background=[("active", "#2E7D7B")])
        style.configure("TScrollbar", background=BORDER, troughcolor=BG_LIGHT, bordercolor=BORDER, arrowcolor=TEXT_GREY)

    # ====== LOGIN SCREEN ======

    def login_screen(self):
        """Display the login screen with master password and face auth options."""
        self._clear_screen()
        self.face_status_label = None
        container = tk.Frame(self.root, bg=BG_LIGHT)
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Icon
        tk.Label(container, text="🔐", font=(self.font_normal[0], 48),
                 bg=BG_LIGHT).pack(pady=(0, 5))
        tk.Label(container, text="Welcome to Anay's Password Vault",
                 font=self.font_title, fg=HEADER_TEAL,
                 bg=BG_LIGHT).pack(pady=5)
        tk.Label(container, text="Enter your master password or use face recognition",
                 font=self.font_subtitle, fg=TEXT_GREY,
                 bg=BG_LIGHT).pack(pady=(0, 20))

        # Password field
        pw_frame = tk.Frame(container, bg=BG_WHITE,
                            highlightbackground=BORDER,
                            highlightthickness=1, bd=0)
        pw_frame.pack(pady=5, ipadx=5, ipady=5)
        tk.Label(pw_frame, text="🔑  ", font=(self.font_normal[0], 14),
                 bg=BG_WHITE).pack(side=tk.LEFT, padx=(10, 0))

        self.master_password_var = tk.StringVar()
        self.pw_entry = tk.Entry(pw_frame,
                                  textvariable=self.master_password_var,
                                  show="*", font=self.font_normal,
                                  width=28, bd=0, highlightthickness=0)
        self.pw_entry.pack(side=tk.LEFT, padx=(0, 10), pady=8)
        self.pw_entry.bind("<Return>", lambda e: self.verify_master_password())
        self.pw_entry.focus_set()

        # Submit
        tk.Button(container, text="   Unlock Vault   ",
                   command=self.verify_master_password,
                   bg=PRIMARY, fg=BG_WHITE, font=self.font_button,
                   bd=0, padx=20, pady=8, cursor="hand2",
                   activebackground=PRIMARY_DARK).pack(pady=(15, 5))

        # Separator
        sep = tk.Frame(container, bg=BG_LIGHT)
        sep.pack(fill="x", pady=10)
        tk.Frame(sep, bg=BORDER, height=1).pack(fill="x",
                  side=tk.LEFT, expand=True)
        tk.Label(sep, text="  OR  ", bg=BG_LIGHT, fg=TEXT_GREY,
                 font=self.font_small).pack(side=tk.LEFT)
        tk.Frame(sep, bg=BORDER, height=1).pack(fill="x",
                  side=tk.LEFT, expand=True)

        # Face button
        face_icon = "📸" if is_face_registered() else "➕"
        face_text = "  Face Login  " if is_face_registered() else "  Enroll Face  "
        tk.Button(container, text=f"{face_icon}{face_text}",
                   command=self._handle_face_auth,
                   bg=HEADER_TEAL, fg=BG_WHITE, font=self.font_button,
                   bd=0, padx=20, pady=8, cursor="hand2",
                   activebackground="#2E7D7B").pack(pady=5)

        # Face status label (for auto-start feedback)
        self.face_status_label = tk.Label(container, text="",
                                           font=self.font_small, fg=HEADER_TEAL,
                                           bg=BG_LIGHT)
        self.face_status_label.pack(pady=(2, 0))

        tk.Label(container, text="v3.1 — Offline & Secure",
                 font=self.font_small, fg=TEXT_GREY,
                 bg=BG_LIGHT).pack(pady=(20, 0))

        self.root.title(f"🔒 {APP_NAME}")

        # Auto-start face authentication if face is registered
        if is_face_registered():
            self.face_status_label.config(text="📸 Face authentication starting...")
            self.root.after(1500, lambda: self._handle_face_auth(auto=True))

    def _handle_face_auth(self, auto=False):
        face_dialog = FaceAuthDialog(self.root)
        if is_face_registered():
            if self.face_status_label:
                self.face_status_label.config(
                    text="📸 Looking for your face in camera..."
                )
            face_dialog.run_authentication(silent=auto)
            poll_start = time.time()

            def _check_auth():
                elapsed = time.time() - poll_start

                if not face_dialog.auth_completed:
                    if elapsed > FACE_POLL_TIMEOUT:
                        if self.face_status_label:
                            self.face_status_label.config(text="")
                        return
                    self.root.after(500, _check_auth)
                    return

                result = face_dialog.result

                if result == 'full':
                    if self.face_status_label:
                        self.face_status_label.config(text="✅ Face matched! Unlocking...")
                    vault_key = get_vault_key_from_face()
                    if vault_key:
                        try:
                            self.key = vault_key
                            self.vault = load_vault(self.key)
                            self.main_screen()
                            return
                        except Exception as e:
                            logger.error(f"Face unlock vault load failed: {e}")
                            result = 'partial'
                    else:
                        result = 'partial'

                if result == 'partial':
                    if self.face_status_label:
                        self.face_status_label.config(text="✅ Face matched! Enter master password.")
                    pw = simpledialog.askstring(
                        "Face Recognized",
                        "Face verified! Enter your master password to unlock:",
                        show="*", parent=self.root
                    )
                    if pw and verify_master_password(pw):
                        self.master_password_var.set(pw)
                        self.verify_master_password()
                    elif pw is not None:
                        self._show_fallback_or_recovery()

                elif result == 'failed':
                    if self.face_status_label:
                        self.face_status_label.config(
                            text="❌ Face not recognized. Use password or recovery code."
                        )
                    self._show_fallback_or_recovery()

            self.root.after(1000, _check_auth)
        else:
            if not auto:
                face_dialog.run_enrollment()

    def _show_fallback_or_recovery(self):
        """Show fallback options after failed face auth."""
        answer = messagebox.askquestion(
            "Access Denied",
            "Face not recognized.\n\n"
            "• Enter your master password below\n"
            "• Use a recovery code if you forgot your password\n\n"
            "Try master password?",
            icon="warning", parent=self.root
        )
        if answer == "yes":
            self.pw_entry.focus_set()
        else:
            self._recovery_code_dialog()

    def _recovery_code_dialog(self):
        """Handle recovery code entry."""
        if not has_recovery_codes():
            messagebox.showerror(
                "No Recovery Codes",
                "No recovery codes available. You must use your master password.",
                parent=self.root
            )
            return
        code = simpledialog.askstring(
            "Recovery Code",
            "Enter one of your recovery codes (format: XXXX-XXXX-XXXX):",
            parent=self.root
        )
        if not code:
            return
        master_pw = verify_recovery_code(code.upper())
        if master_pw:
            messagebox.showinfo(
                "Recovery Successful",
                "Recovery code accepted! Unlocking vault...",
                parent=self.root
            )
            self.master_password_var.set(master_pw)
            self.verify_master_password()
        else:
            messagebox.showerror(
                "Invalid Code",
                "Recovery code is invalid or already used.\n"
                "Please try again or use your master password.",
                parent=self.root
            )

    def verify_master_password(self, first_run=False):
        self._update_activity()
        pw = self.master_password_var.get()
        if not pw:
            messagebox.showerror("Error", "Please enter a password.", parent=self.root)
            return
        if not os.path.exists(MASTER_HASH_FILE) or first_run:
            confirm = simpledialog.askstring(
                "Set Master Password",
                "Confirm master password:",
                show="*", parent=self.root
            )
            if not confirm:
                return
            if pw != confirm:
                messagebox.showerror("Error", "Passwords do not match.", parent=self.root)
                return
            save_master_password(pw)

            # Generate recovery codes on first setup
            codes = generate_recovery_codes(pw)
            codes_text = "\n".join(f"  {c}" for c in codes)
            messagebox.showinfo(
                "Recovery Codes",
                "YOUR RECOVERY CODES (save these somewhere safe!):\n\n"
                f"{codes_text}\n\n"
                "Each code can be used ONCE to access your vault\n"
                "if you forget your master password.",
                parent=self.root
            )
        elif not verify_master_password(pw):
            messagebox.showerror("Access Denied", "Incorrect master password.", parent=self.root)
            return
        self.master_pw = pw
        self.key = derive_key(pw)
        try:
            self.vault = load_vault(self.key)
        except Exception as e:
            logger.error(f"Vault load failed: {e}")
            messagebox.showerror("Error", "Vault corrupted or invalid password.", parent=self.root)
            return
        # Save vault key for face unlock if face is enrolled
        if is_face_registered():
            save_vault_key_for_face(self.key)
        self.main_screen()

    # ====== MAIN SCREEN ======

    def main_screen(self):
        self._clear_screen()
        self.root.title(f"🔐 {APP_NAME}")

        header = tk.Frame(self.root, bg=HEADER_TEAL, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🔐  Anay's Password Vault", font=(self.font_normal[0], 16, "bold"), fg=BG_WHITE, bg=HEADER_TEAL).pack(side=tk.LEFT, padx=20, pady=12)
        tk.Button(header, text="🔒 Lock", command=self._lock_vault, bg=HEADER_TEAL, fg=BG_WHITE, font=(self.font_normal[0], 10), bd=0, padx=12, cursor="hand2", activebackground="#2E7D7B").pack(side=tk.RIGHT, padx=15, pady=10)

        # -- Search Bar --
        search_bg = tk.Frame(self.root, bg=BG_WHITE, highlightbackground=BORDER, highlightthickness=1)
        search_bg.pack(fill="x", padx=15, pady=(12, 5))
        tk.Label(search_bg, text="🔍  ", font=(self.font_normal[0], 13), bg=BG_WHITE).pack(side=tk.LEFT, padx=(10, 0))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_bg, textvariable=self.search_var, font=self.font_normal, bd=0, highlightthickness=0, bg=BG_WHITE)
        search_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5), pady=8)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_tree())
        clear_lbl = tk.Label(search_bg, text="✕", font=(self.font_normal[0], 12), fg=TEXT_GREY, bg=BG_WHITE, cursor="hand2")
        clear_lbl.pack(side=tk.RIGHT, padx=(0, 10))
        clear_lbl.bind("<Button-1>", lambda e: [self.search_var.set(""), self.refresh_tree(), search_entry.focus_set()])

        self.count_label = tk.Label(self.root, text="", font=self.font_small, fg=TEXT_GREY, bg=BG_LIGHT)
        self.count_label.pack(anchor="w", padx=18, pady=(2, 0))

        tree_frame = tk.Frame(self.root, bg=BG_WHITE, highlightbackground=BORDER, highlightthickness=1)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(5, 5))
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        self.tree = ttk.Treeview(tree_frame, columns=("Service", "Username", "Password", "Action"), show="headings", yscrollcommand=vsb.set, xscrollcommand=hsb.set, selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.heading("Service", text="  Service", command=lambda: self._sort_tree("Service"))
        self.tree.heading("Username", text="Username", command=lambda: self._sort_tree("Username"))
        self.tree.heading("Password", text="Password")
        self.tree.heading("Action", text="Show/Hide")
        self.tree.column("Service", width=200, minwidth=100, anchor="w")
        self.tree.column("Username", width=180, minwidth=100, anchor="w")
        self.tree.column("Password", width=140, minwidth=100, anchor="center")
        self.tree.column("Action", width=100, minwidth=80, anchor="center")

        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<Return>", lambda e: self.copy_selected_password())

        toolbar = tk.Frame(self.root, bg=BG_LIGHT)
        toolbar.pack(pady=(5, 8))
        btn_s = {"bd": 0, "fg": BG_WHITE, "font": self.font_button, "padx": 14, "pady": 6, "cursor": "hand2"}
        tk.Button(toolbar, text="➕  Add New", bg=PRIMARY, command=self.add_entry, **btn_s).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="📋  Copy", bg=SECONDARY, command=self.copy_selected_password, **btn_s).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="🔁  Generate", bg=PRIMARY, command=self.add_entry_with_password, **btn_s).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="✏️  Edit", bg=WARNING, command=self._edit_selected, **btn_s).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="🗑️  Delete", bg=DANGER, command=self.delete_selected, **btn_s).pack(side=tk.LEFT, padx=3)
        tk.Frame(toolbar, bg=BORDER, width=1, height=24).pack(side=tk.LEFT, padx=6)
        tk.Button(toolbar, text="📤  Export", bg=HEADER_TEAL, command=self.export_csv, **btn_s).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="📥  Import", bg=HEADER_TEAL, command=self.import_csv, **btn_s).pack(side=tk.LEFT, padx=3)

        status_bar = tk.Frame(self.root, bg=BG_WHITE, highlightbackground=BORDER, highlightthickness=1)
        status_bar.pack(side="bottom", fill="x")
        self.status_text = tk.StringVar(value="Ready")
        tk.Label(status_bar, textvariable=self.status_text, font=self.font_small, fg=TEXT_GREY, bg=BG_WHITE, anchor="w").pack(side=tk.LEFT, padx=12, pady=4)
        self.badge_entries = tk.Label(status_bar, text="", font=self.font_small, fg=PRIMARY_DARK, bg=BG_WHITE)
        self.badge_entries.pack(side=tk.RIGHT, padx=12, pady=4)

        self.root.bind("<Control-f>", lambda e: search_entry.focus_set())
        self.root.bind("<Control-n>", lambda e: self.add_entry())
        self.root.bind("<Control-c>", lambda e: self.copy_selected_password())
        self.root.bind("<Control-e>", lambda e: self._edit_selected())
        self.root.bind("<Control-x>", lambda e: self.export_csv())

        self.refresh_tree()
        self._update_status()


    # ====== TREE METHODS ======

    def refresh_tree(self):
        self._update_activity()
        self.tree.delete(*self.tree.get_children())
        query = self.search_var.get().lower().strip()
        items = []
        for service, creds in self.vault.items():
            if query in service.lower() or query in creds["username"].lower():
                items.append((service, creds))
        if self.sort_column == "Service":
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        elif self.sort_column == "Username":
            items.sort(key=lambda x: x[1]["username"].lower(), reverse=self.sort_reverse)
        for service, creds in items:
            is_revealed = self.revealed_rows.get(service, False)
            password = creds["password"] if is_revealed else "●●●●●●●●"
            action = "🙈 Hide" if is_revealed else "👁 Show"
            self.tree.insert("", "end", iid=service, values=(f"  {service}", creds["username"], password, action))
        self._update_status()

    def _sort_tree(self, col):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        self.refresh_tree()

    def _on_tree_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        col = self.tree.identify_column(event.x)
        if col != "#4":
            return
        service_key = selected_item[0]
        clean_key = service_key.strip()
        if clean_key not in self.vault:
            messagebox.showerror("Error", "Service not found in vault.", parent=self.root)
            return
        is_revealed = self.revealed_rows.get(clean_key, False)
        if is_revealed:
            self.revealed_rows[clean_key] = False
            self.tree.item(service_key, values=(service_key, self.vault[clean_key]["username"], "●●●●●●●●", "👁 Show"))
        else:
            self.revealed_rows[clean_key] = True
            self.tree.item(service_key, values=(service_key, self.vault[clean_key]["username"], self.vault[clean_key]["password"], "🙈 Hide"))
        self._update_status()


    # ====== ACTIONS ======

    def add_entry(self):
        self._update_activity()
        def on_save(fields, dialog):
            service = fields["service"].get().strip()
            username = fields["username"].get().strip()
            password = fields["password"].get()
            if not service:
                messagebox.showerror("Error", "Service name required.", parent=dialog)
                return False
            if service in self.vault:
                if not messagebox.askyesno("Overwrite", f"'{service}' already exists. Overwrite?", parent=dialog):
                    return False
            self.vault[service] = {"username": username, "password": password}
            save_vault(self.vault, self.key)
            self.refresh_tree()
            self.status_text.set(f"✅ Added '{service}'")
        self._build_entry_dialog("➕ Add New Entry", "Add New Password Entry", [("Service Name", "service", ""), ("Username", "username", ""), ("Password", "password", "")], on_save)

    def add_entry_with_password(self):
        self._update_activity()
        generated = generate_password()
        def on_save(fields, dialog):
            service = fields["service"].get().strip()
            username = fields["username"].get().strip()
            password = fields["password"].get()
            if not service:
                messagebox.showerror("Error", "Service name required.", parent=dialog)
                return False
            if service in self.vault:
                if not messagebox.askyesno("Overwrite", f"'{service}' already exists. Overwrite?", parent=dialog):
                    return False
            self.vault[service] = {"username": username, "password": password}
            save_vault(self.vault, self.key)
            self.refresh_tree()
            self.status_text.set(f"✅ Added '{service}'")
        self._build_entry_dialog("➕ Add Entry (with Password)", "Add New Password Entry",
                                  [("Service Name", "service", ""),
                                   ("Username", "username", ""),
                                   ("Password", "password", generated)], on_save)

    def _edit_selected(self):
        self._update_activity()
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select an entry to edit.", parent=self.root)
            return
        service_key = selected.strip()
        if service_key not in self.vault:
            return
        creds = self.vault[service_key]
        def on_save(fields, dialog):
            new_service = fields["service"].get().strip()
            new_username = fields["username"].get().strip()
            new_password = fields["password"].get()
            if not new_service:
                messagebox.showerror("Error", "Service name required.", parent=dialog)
                return False
            if new_service != service_key:
                del self.vault[service_key]
                self.revealed_rows.pop(service_key, None)
                self.revealed_rows.pop(new_service, None)
            self.vault[new_service] = {"username": new_username, "password": new_password}
            save_vault(self.vault, self.key)
            self.refresh_tree()
            self.status_text.set(f"✏️ Updated '{new_service}'")
        self._build_entry_dialog(f"✏️ Edit: {service_key}", f"Editing '{service_key}'", [("Service Name", "service", service_key), ("Username", "username", creds["username"]), ("Password", "password", creds["password"])], on_save)


    def copy_selected_password(self):
        self._update_activity()
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select an entry.", parent=self.root)
            return
        service_key = selected.strip()
        if service_key not in self.vault:
            return
        pw = self.vault[service_key]["password"]
        pyperclip.copy(pw)
        self.status_text.set(f"📋 Copied password for '{service_key}'")
        logger.info(f"Password for '{service_key}' copied to clipboard.")
        self._start_clipboard_clear_timer()

    def delete_selected(self):
        self._update_activity()
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select an entry to delete.", parent=self.root)
            return
        service_key = selected.strip()
        if service_key not in self.vault:
            return
        confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete '{service_key}'?", parent=self.root)
        if confirm:
            del self.vault[service_key]
            self.revealed_rows.pop(service_key, None)
            save_vault(self.vault, self.key)
            self.refresh_tree()
            self.status_text.set(f"🗑️ Deleted '{service_key}'")

    def export_csv(self):
        self._update_activity()
        if not self.vault:
            messagebox.showinfo("Export", "No entries to export.", parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export vault as CSV",
            parent=self.root
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Service", "Username", "Password"])
                for service, creds in sorted(self.vault.items()):
                    writer.writerow([service, creds["username"], creds["password"]])
            self.status_text.set(f"📤 Exported {len(self.vault)} entries to CSV")
            logger.info(f"Vault exported to {path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self.root)

    def import_csv(self):
        self._update_activity()
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="Import CSV into vault",
            parent=self.root
        )
        if not path:
            return
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    service = row.get("Service", "").strip()
                    username = row.get("Username", "").strip()
                    password = row.get("Password", "")
                    if not service:
                        continue
                    self.vault[service] = {"username": username, "password": password}
                    count += 1
            save_vault(self.vault, self.key)
            self.refresh_tree()
            self.status_text.set(f"📥 Imported {count} entries from CSV")
            logger.info(f"Imported {count} entries from {path}")
        except Exception as e:
            messagebox.showerror("Import Failed", str(e), parent=self.root)

    def _lock_vault(self, auto=False):
        if self.clipboard_timer:
            self.root.after_cancel(self.clipboard_timer)
            self.clipboard_timer = None
        if auto:
            pyperclip.copy("")
            logger.info("Vault auto-locked due to inactivity.")
        else:
            logger.info("Vault locked by user.")
        self.key = None
        self.master_pw = None
        self.vault = {}
        self.revealed_rows = {}
        self._clear_screen()
        self.login_screen()

    def _start_clipboard_clear_timer(self):
        if self.clipboard_timer:
            self.root.after_cancel(self.clipboard_timer)
        def _clear_clipboard():
            pyperclip.copy("")
            self.status_text.set("🧹 Clipboard cleared for security")
            self.clipboard_timer = None
        self.clipboard_timer = self.root.after(CLIPBOARD_CLEAR_SECONDS * 1000, _clear_clipboard)

    def _password_strength(self, pwd: str) -> int:
        score = 0
        if len(pwd) >= 8:
            score += 1
        if len(pwd) >= 12:
            score += 1
        if re.search(r"[a-z]", pwd) and re.search(r"[A-Z]", pwd):
            score += 1
        if re.search(r"\d", pwd):
            score += 1
        if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", pwd):
            score += 1
        return score

    def _build_entry_dialog(self, title, header_text, fields_config, on_save):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("420x420")
        dialog.configure(bg=BG_WHITE)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=header_text, font=self.font_title, fg=HEADER_TEAL, bg=BG_WHITE).pack(pady=(15, 10))

        fields = {}
        for label, key, init_val in fields_config:
            tk.Label(dialog, text=label, font=self.font_subtitle, fg=TEXT_DARK, bg=BG_WHITE, anchor="w").pack(fill="x", padx=20, pady=(5, 0))
            entry = tk.Entry(dialog, font=self.font_normal, bd=1, relief="solid", highlightbackground=BORDER)
            if init_val:
                entry.insert(0, init_val)
            entry.pack(fill="x", padx=20, pady=(0, 5), ipady=3)
            fields[key] = entry

        if "password" in fields:
            fields["password"].config(show="*")
            strength_label = tk.Label(dialog, text="", font=self.font_small, bg=BG_WHITE)
            strength_label.pack()
            gen_btn_frame = tk.Frame(dialog, bg=BG_WHITE)
            gen_btn_frame.pack(fill="x", padx=20, pady=(0, 5))
            tk.Button(gen_btn_frame, text="🔁  Generate Strong Password", bg=PRIMARY, fg=BG_WHITE, font=(self.font_normal[0], 9, "bold"), bd=0, padx=10, pady=3, cursor="hand2", command=lambda: self._fill_generated_password(fields["password"], strength_label)).pack(side=tk.LEFT)

            def _check_strength(*args):
                pw = fields["password"].get()
                score = self._password_strength(pw)
                if score < 2:
                    strength_label.config(text="Weak", fg=DANGER)
                elif score < 4:
                    strength_label.config(text="Medium", fg=WARNING)
                else:
                    strength_label.config(text="Strong", fg=PRIMARY)
            fields["password"].bind("<KeyRelease>", _check_strength)

        btn_frame = tk.Frame(dialog, bg=BG_WHITE)
        btn_frame.pack(pady=(10, 5))
        tk.Button(btn_frame, text="💾  Save", bg=PRIMARY, fg=BG_WHITE, font=self.font_button, bd=0, padx=20, pady=6, cursor="hand2", activebackground=PRIMARY_DARK, command=lambda: self._save_entry_wrapper(dialog, fields, on_save)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", bg=BG_LIGHT, fg=TEXT_DARK, font=self.font_normal, bd=0, padx=20, pady=4, cursor="hand2", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        first_key = list(fields.keys())[0]
        fields[first_key].focus_set()
        return dialog, fields

    def _fill_generated_password(self, password_entry, strength_label):
        pwd = generate_password()
        password_entry.delete(0, tk.END)
        password_entry.insert(0, pwd)
        score = self._password_strength(pwd)
        if score < 2:
            strength_label.config(text="Weak", fg=DANGER)
        elif score < 4:
            strength_label.config(text="Medium", fg=WARNING)
        else:
            strength_label.config(text="Strong", fg=PRIMARY)

    def _save_entry_wrapper(self, dialog, fields, on_save):
        result = on_save(fields, dialog)
        if result is not False:
            dialog.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManagerGUI(root)
    root.mainloop()
