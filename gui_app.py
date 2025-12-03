"""
Anay's Password Vault - GUI Application
With Face Recognition Authentication
"""

import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import pyperclip
import cv2
from PIL import Image, ImageTk
import numpy as np
import tempfile
import os

# Import vault modules
from vault_core import derive_key, load_vault, save_vault, verify_master_password
from password_generator import generate_password

# Import face_recognition with error handling
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[WARNING] face_recognition not available")

# Import face_auth
try:
    from face_auth import FaceAuthenticator
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    
    class FaceAuthenticator:
        """Dummy class when face_auth is not available."""
        def __init__(self, *args, **kwargs):
            pass
        def is_registered(self):
            return False
        def reset_attempts(self):
            pass
        def is_locked_out(self):
            return False
        def get_registration_count(self):
            return 0
        def reset_face_data(self):
            return True
        def register_face_from_frame(self, frame):
            return False, "Face auth not available"
        def verify_face_from_frame(self, frame):
            return False, 0, "Face auth not available"
        def get_face_confidence(self, frame):
            return False, 0, "Not available"
        def get_security_level(self):
            return 0.6
        def set_security_level(self, level):
            return True
        def get_security_level_name(self):
            return "Medium"
        def get_auth_history(self, limit=10):
            return []


class PasswordManagerGUI:
    """Main GUI Application for Password Manager."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Anay's Password Vault")
        self.vault = {}
        self.key = None
        self.revealed_rows = {}

        # Face authentication
        self.face_auth = FaceAuthenticator()
        self.camera_running = False
        self.cap = None
        self.current_frame = None
        self.registration_mode = False
        self.samples_needed = 5
        
        # Temp file for reliable face detection
        self.temp_dir = tempfile.gettempdir()
        self.temp_image_path = os.path.join(self.temp_dir, "face_auth_temp.jpg")

        # Styling
        self.font = ("Helvetica", 14)
        self.primary_color = "#4CAF50"
        self.bg_color = "#f4f4f9"
        self.button_color = "#FF5722"
        self.header_color = "#3C9D9B"
        self.face_auth_color = "#2196F3"

        self.root.configure(bg=self.bg_color)
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the appropriate screen
        if FACE_RECOGNITION_AVAILABLE and self.face_auth.is_registered():
            self.face_login_screen()
        elif FACE_RECOGNITION_AVAILABLE:
            self.face_setup_screen()
        else:
            self.login_screen()

    # ==================== UTILITY METHODS ====================
    
    def on_closing(self):
        """Handle window close event."""
        self.stop_camera()
        try:
            if os.path.exists(self.temp_image_path):
                os.remove(self.temp_image_path)
        except Exception:
            pass
        self.root.destroy()

    def clear_screen(self):
        """Clear all widgets from the screen."""
        self.stop_camera()
        for widget in self.root.winfo_children():
            widget.destroy()

    def detect_faces_reliable(self, frame):
        """
        Reliable face detection using save-and-reload method.
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return []
        
        try:
            cv2.imwrite(self.temp_image_path, frame)
            image = face_recognition.load_image_file(self.temp_image_path)
            face_locations = face_recognition.face_locations(image, model="hog")
            return face_locations
        except Exception as e:
            print(f"Face detection error: {e}")
            return []

    def encode_face_reliable(self, frame):
        """
        Reliable face encoding using save-and-reload method.
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return None, None, "face_recognition not available"
        
        try:
            cv2.imwrite(self.temp_image_path, frame)
            image = face_recognition.load_image_file(self.temp_image_path)
            face_locations = face_recognition.face_locations(image, model="hog")
            
            if len(face_locations) == 0:
                return None, None, "No face detected"
            
            if len(face_locations) > 1:
                return None, None, "Multiple faces detected"
            
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) == 0:
                return None, None, "Could not encode face"
            
            return face_encodings[0], face_locations[0], None
            
        except Exception as e:
            return None, None, f"Error: {str(e)}"

    # ==================== CAMERA METHODS ====================

    def start_camera(self):
        """Start the camera feed."""
        self.current_frame = None
        self.camera_running = True
        
        self.cap = None
        
        # Try DirectShow first (Windows)
        for index in [0, 1]:
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        self.cap = cap
                        print(f"Camera opened with DirectShow, index {index}")
                        break
                cap.release()
            except Exception as e:
                print(f"DirectShow camera {index} error: {e}")
        
        # Try without DirectShow
        if self.cap is None:
            for index in [0, 1]:
                try:
                    cap = cv2.VideoCapture(index)
                    if cap.isOpened():
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None:
                            self.cap = cap
                            print(f"Camera opened without DirectShow, index {index}")
                            break
                    cap.release()
                except Exception as e:
                    print(f"Camera {index} error: {e}")
        
        if self.cap is None:
            self.status_label.config(text="❌ Could not access camera!", fg="red")
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.status_label.config(text="📷 Camera ready - Position your face", fg="green")
        self.update_camera()

    def update_camera(self):
        """Update camera feed with liveness and confidence display."""
        if not self.camera_running or self.cap is None:
            return

        try:
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                self.current_frame = frame.copy()
                display_frame = frame.copy()
                
                # Detect faces
                face_locations = self.detect_faces_reliable(frame)
                
                # Check liveness
                liveness_msg = ""
                if self.face_auth.liveness_enabled and not self.registration_mode:
                    is_live, blinks, liveness_msg = self.face_auth.check_liveness_frame(frame)
                
                # Draw rectangles
                for (top, right, bottom, left) in face_locations:
                    # Get confidence
                    if self.face_auth.is_registered() and not self.registration_mode:
                        has_face, confidence, _ = self.face_auth.get_face_confidence(frame)
                        threshold = self.face_auth.get_security_level() * 100
                        face_only_threshold = self.face_auth.face_only_threshold * 100
                        
                        if has_face:
                            if confidence >= face_only_threshold:
                                color = (0, 255, 0)  # Green - PIN unlock available
                                status = f"{confidence:.0f}% (PIN OK)"
                            elif confidence >= threshold:
                                color = (0, 200, 255)  # Yellow-ish
                                status = f"{confidence:.0f}%"
                            else:
                                color = (0, 165, 255)  # Orange
                                status = f"{confidence:.0f}% LOW"
                        else:
                            color = (0, 0, 255)
                            status = "NO MATCH"
                    else:
                        color = (0, 255, 0)
                        status = "Detected"
                    
                    cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(display_frame, status, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Update status label
                if len(face_locations) == 0:
                    self.status_label.config(text="👤 No face - Move closer", fg="orange")
                elif len(face_locations) > 1:
                    self.status_label.config(text="⚠️ Multiple faces", fg="orange")
                else:
                    if self.registration_mode:
                        self.status_label.config(text="✅ Face detected - Click Capture", fg="green")
                    else:
                        # Show liveness status
                        if self.face_auth.liveness_enabled:
                            if self.face_auth.is_liveness_verified():
                                self.status_label.config(text="✅ Liveness OK - Click Verify", fg="green")
                            else:
                                blinks = self.face_auth.blink_counter
                                needed = self.face_auth.blinks_required
                                self.status_label.config(
                                    text=f"👁️ Blink to verify ({blinks}/{needed})",
                                    fg="blue"
                                )
                        else:
                            self.status_label.config(text="✅ Ready - Click Verify", fg="green")
                
                # Convert for display
                display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                display_resized = cv2.resize(display_rgb, (480, 360))
                
                img = Image.fromarray(display_resized)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.camera_frame.imgtk = imgtk
                self.camera_frame.configure(image=imgtk)
            
        except Exception as e:
            print(f"Camera error: {e}")
        
        if self.camera_running:
            self.root.after(100, self.update_camera)

    def stop_camera(self):
        """Stop the camera feed."""
        self.camera_running = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.current_frame = None

    # ==================== FACE SETUP SCREEN ====================

    def face_setup_screen(self):
        """First-time face registration screen."""
        self.clear_screen()
        self.registration_mode = True

        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Header
        tk.Label(
            frame, 
            text="🔐 Welcome to Anay's Password Vault", 
            font=("Helvetica", 20, "bold"), 
            fg=self.header_color, 
            bg=self.bg_color
        ).pack(pady=10)

        # Subtitle
        tk.Label(
            frame, 
            text="📸 First-time Setup: Register Your Face", 
            font=("Helvetica", 14), 
            fg=self.face_auth_color, 
            bg=self.bg_color
        ).pack(pady=5)

        # Instructions
        tk.Label(
            frame, 
            text=f"We'll capture {self.samples_needed} photos of your face for secure authentication.\n"
                 "Position your face in the camera and click 'Capture' for each sample.",
            font=("Helvetica", 11), 
            bg=self.bg_color,
            justify="center"
        ).pack(pady=10)

        # Progress label
        self.progress_label = tk.Label(
            frame, 
            text=f"Samples captured: 0/{self.samples_needed}", 
            font=("Helvetica", 12, "bold"), 
            fg=self.primary_color, 
            bg=self.bg_color
        )
        self.progress_label.pack(pady=5)

        # Camera frame
        self.camera_frame = tk.Label(frame, bg="black", width=640, height=480)
        self.camera_frame.pack(pady=10)

        # Status label
        self.status_label = tk.Label(
            frame, 
            text="📷 Camera starting...", 
            font=("Helvetica", 11), 
            fg="#666", 
            bg=self.bg_color
        )
        self.status_label.pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(frame, bg=self.bg_color)
        btn_frame.pack(pady=10)

        self.capture_btn = tk.Button(
            btn_frame, 
            text="📸 Capture Sample", 
            command=self.capture_registration_sample,
            bg=self.face_auth_color, 
            fg="white", 
            font=("Helvetica", 12, "bold"),
            relief="raised",
            width=20
        )
        self.capture_btn.grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame, 
            text="⏭️ Skip (Password Only)", 
            command=self.skip_face_setup,
            bg="#9E9E9E", 
            fg="white", 
            font=("Helvetica", 12),
            relief="raised",
            width=20
        ).grid(row=0, column=1, padx=10)

        self.start_camera()

    def capture_registration_sample(self):
        """Capture a face sample for registration."""
        if self.current_frame is None:
            self.status_label.config(text="❌ No frame available", fg="red")
            return

        success, message = self.face_auth.register_face_from_frame(self.current_frame)
        
        if success:
            count = self.face_auth.get_registration_count()
            self.progress_label.config(text=f"Samples captured: {count}/{self.samples_needed}")
            self.status_label.config(text=f"✅ {message}", fg="green")
            
            if count >= self.samples_needed:
                self.stop_camera()
                messagebox.showinfo(
                    "Registration Complete", 
                    "✅ Face registration successful!\n\n"
                    "You can now use face authentication to access your vault."
                )
                self.login_screen()
        else:
            self.status_label.config(text=f"❌ {message}", fg="red")

    def skip_face_setup(self):
        """Skip face setup and go to password-only login."""
        if messagebox.askyesno(
            "Skip Face Setup?",
            "Are you sure you want to skip face authentication setup?\n\n"
            "You can set it up later from the main menu."
        ):
            self.stop_camera()
            self.login_screen()

    # ==================== FACE LOGIN SCREEN ====================

    def face_login_screen(self):
        """Face authentication login screen."""
        self.clear_screen()
        self.registration_mode = False
        self.face_auth.reset_attempts()

        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Header
        tk.Label(
            frame, 
            text="🔐 Anay's Password Vault", 
            font=("Helvetica", 20, "bold"), 
            fg=self.header_color, 
            bg=self.bg_color
        ).pack(pady=10)

        # Subtitle with security level
        security_level = self.face_auth.get_security_level() * 100
        tk.Label(
            frame, 
            text=f"📸 Face Authentication (Security: {security_level:.0f}%)", 
            font=("Helvetica", 14), 
            fg=self.face_auth_color, 
            bg=self.bg_color
        ).pack(pady=5)

        # Instructions
        tk.Label(
            frame, 
            text="Position your face in the camera and click 'Verify' to authenticate.",
            font=("Helvetica", 11), 
            bg=self.bg_color
        ).pack(pady=10)

        # Camera frame
        self.camera_frame = tk.Label(frame, bg="black", width=640, height=480)
        self.camera_frame.pack(pady=10)

        # Status label
        self.status_label = tk.Label(
            frame, 
            text="📷 Camera starting...", 
            font=("Helvetica", 11), 
            fg="#666", 
            bg=self.bg_color
        )
        self.status_label.pack(pady=5)

        # Confidence display
        self.confidence_label = tk.Label(
            frame, 
            text="", 
            font=("Helvetica", 12, "bold"), 
            bg=self.bg_color
        )
        self.confidence_label.pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(frame, bg=self.bg_color)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, 
            text="🔓 Verify Face", 
            command=self.verify_face,
            bg=self.primary_color, 
            fg="white", 
            font=("Helvetica", 12, "bold"),
            relief="raised",
            width=15
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame, 
            text="🔑 Use Password", 
            command=self.switch_to_password_login,
            bg=self.button_color, 
            fg="white", 
            font=("Helvetica", 12),
            relief="raised",
            width=15
        ).grid(row=0, column=1, padx=10)

        self.start_camera()

    def verify_face(self):
        """Verify face with PIN unlock support."""
        if self.face_auth.is_locked_out():
            self.stop_camera()
            messagebox.showerror("Locked Out", "❌ Too many failed attempts!")
            self.switch_to_password_login()
            return

        if self.current_frame is None:
            self.status_label.config(text="❌ No frame available", fg="red")
            return

        # Verify face
        success, confidence, message, can_use_pin = self.face_auth.verify_face_from_frame(self.current_frame)
        
        if success:
            self.stop_camera()
            self.confidence_label.config(text=f"✅ Match: {confidence:.1f}%", fg="green")
            self.status_label.config(text="✅ Face verified!", fg="green")
            self.root.update()
            
            if can_use_pin:
                # Show PIN entry (faster than password)
                self.root.after(500, self.show_pin_entry)
            else:
                # Need full password
                self.root.after(500, self.password_verification_after_face)
        else:
            self.status_label.config(text=f"❌ {message}", fg="red")
            self.confidence_label.config(
                text=f"Confidence: {confidence:.1f}%",
                fg="red" if confidence < 50 else "orange"
            )
            
            if self.face_auth.is_locked_out():
                self.stop_camera()
                messagebox.showerror("Locked Out", "❌ Maximum attempts reached!")
                self.switch_to_password_login()


    def password_verification_after_face(self):
        """Show password verification after successful face auth."""
        self.clear_screen()

        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(pady=100, padx=20, fill="both", expand=True)

        tk.Label(
            frame, 
            text="✅ Face Verified!", 
            font=("Helvetica", 16, "bold"), 
            fg="green", 
            bg=self.bg_color
        ).pack(pady=10)

        tk.Label(
            frame, 
            text="🔑 Enter Master Password", 
            font=("Helvetica", 18, "bold"), 
            fg=self.header_color, 
            bg=self.bg_color
        ).pack(pady=20)

        tk.Label(
            frame, 
            text="Enter your master password to decrypt the vault",
            font=("Helvetica", 12), 
            bg=self.bg_color
        ).pack(pady=10)

        self.master_password_var = tk.StringVar()
        pw_entry = tk.Entry(
            frame, 
            textvariable=self.master_password_var, 
            show="*", 
            font=self.font, 
            width=25, 
            bd=2, 
            relief="solid"
        )
        pw_entry.pack(pady=10)
        pw_entry.focus()
        pw_entry.bind("<Return>", lambda e: self.verify_master_password())

        tk.Button(
            frame, 
            text="🔓 Unlock Vault", 
            command=self.verify_master_password, 
            bg=self.primary_color, 
            fg="white", 
            font=("Helvetica", 12, "bold"), 
            relief="raised", 
            width=20
        ).pack(pady=20)

    def show_pin_entry(self):
        """Show PIN entry screen after face verification."""
        self.clear_screen()

        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(pady=80, padx=20, fill="both", expand=True)

        # Success header
        tk.Label(
            frame,
            text="✅ Face Verified!",
            font=("Helvetica", 18, "bold"),
            fg="green",
            bg=self.bg_color
        ).pack(pady=15)

        tk.Label(
            frame,
            text="🔓 Enter Quick PIN to Unlock",
            font=("Helvetica", 16),
            fg=self.header_color,
            bg=self.bg_color
        ).pack(pady=10)

        # PIN Entry
        self.pin_var = tk.StringVar()
        pin_frame = tk.Frame(frame, bg=self.bg_color)
        pin_frame.pack(pady=20)
        
        pin_entry = tk.Entry(
            pin_frame,
            textvariable=self.pin_var,
            show="●",
            font=("Helvetica", 24),
            width=8,
            justify="center",
            bd=2,
            relief="solid"
        )
        pin_entry.pack()
        pin_entry.focus()
        pin_entry.bind("<Return>", lambda e: self.verify_pin_and_unlock())
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=self.bg_color)
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="🔓 Unlock",
            command=self.verify_pin_and_unlock,
            bg=self.primary_color,
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=15
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="🔑 Use Password",
            command=self.password_verification_after_face,
            bg=self.button_color,
            fg="white",
            font=("Helvetica", 12),
            width=15
        ).grid(row=0, column=1, padx=10)

        # Info
        tk.Label(
            frame,
            text="Or use your master password instead",
            font=("Helvetica", 10),
            fg="#666",
            bg=self.bg_color
        ).pack(pady=10)


    def verify_pin_and_unlock(self):
        """Verify PIN and unlock vault."""
        pin = self.pin_var.get()
        
        if not pin:
            messagebox.showerror("Error", "Please enter your PIN")
            return
        
        success, message = self.face_auth.verify_pin(pin)
        
        if success:
            # PIN verified - now need password for vault decryption
            # But we can show a simpler password prompt
            self.show_simple_password_prompt()
        else:
            messagebox.showerror("Error", f"❌ {message}")


    def show_simple_password_prompt(self):
        """Show simplified password prompt after PIN verification."""
        self.clear_screen()

        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(pady=100, padx=20, fill="both", expand=True)

        tk.Label(
            frame,
            text="✅ Face + PIN Verified!",
            font=("Helvetica", 16, "bold"),
            fg="green",
            bg=self.bg_color
        ).pack(pady=10)

        tk.Label(
            frame,
            text="🔑 Enter Master Password",
            font=("Helvetica", 14),
            fg=self.header_color,
            bg=self.bg_color
        ).pack(pady=15)

        self.master_password_var = tk.StringVar()
        pw_entry = tk.Entry(
            frame,
            textvariable=self.master_password_var,
            show="*",
            font=self.font,
            width=25,
            bd=2,
            relief="solid"
        )
        pw_entry.pack(pady=10)
        pw_entry.focus()
        pw_entry.bind("<Return>", lambda e: self.verify_master_password())

        tk.Button(
            frame,
            text="🔓 Unlock Vault",
            command=self.verify_master_password,
            bg=self.primary_color,
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=20
        ).pack(pady=20)


    def switch_to_password_login(self):
        """Switch to password-only login."""
        self.stop_camera()
        self.login_screen()

    # ==================== PASSWORD LOGIN SCREEN ====================

    def login_screen(self):
        """Original password login screen."""
        self.clear_screen()

        frame = tk.Frame(self.root, bg=self.bg_color)
        frame.pack(pady=100, padx=20, fill="both", expand=True)

        tk.Label(
            frame, 
            text="🔐 Welcome to Anay's Password Vault", 
            font=("Helvetica", 18, "bold"), 
            fg=self.header_color, 
            bg=self.bg_color
        ).pack(pady=20)

        tk.Label(
            frame, 
            text="Enter your master password to proceed", 
            font=("Helvetica", 12), 
            bg=self.bg_color
        ).pack(pady=10)

        self.master_password_var = tk.StringVar()
        pw_entry = tk.Entry(
            frame, 
            textvariable=self.master_password_var, 
            show="*", 
            font=self.font, 
            width=25, 
            bd=2, 
            relief="solid"
        )
        pw_entry.pack(pady=10)
        pw_entry.focus()
        pw_entry.bind("<Return>", lambda e: self.verify_master_password())

        btn_frame = tk.Frame(frame, bg=self.bg_color)
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame, 
            text="🔓 Submit", 
            command=self.verify_master_password, 
            bg=self.primary_color, 
            fg="white", 
            font=("Helvetica", 12, "bold"), 
            relief="raised", 
            width=15
        ).grid(row=0, column=0, padx=10)

        if FACE_RECOGNITION_AVAILABLE and self.face_auth.is_registered():
            tk.Button(
                btn_frame, 
                text="📸 Use Face", 
                command=self.face_login_screen, 
                bg=self.face_auth_color, 
                fg="white", 
                font=("Helvetica", 12, "bold"), 
                relief="raised", 
                width=15
            ).grid(row=0, column=1, padx=10)

    def verify_master_password(self):
        """Verify master password and load vault."""
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

    # ==================== MAIN SCREEN ====================

    def main_screen(self):
        """Main password manager screen."""
        self.clear_screen()

        # Search Bar
        search_frame = tk.Frame(self.root, bg=self.bg_color)
        search_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(search_frame, text="🔍 Search:", font=self.font, bg=self.bg_color).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=self.font, bd=2)
        search_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_tree())

        # Treeview
        self.tree = ttk.Treeview(
            self.root, 
            columns=("Service", "Username", "Password", "Action"), 
            show="headings"
        )
        self.tree.heading("Service", text="Service")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Password", text="Password")
        self.tree.heading("Action", text="Action")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.refresh_tree()

        # Main action buttons
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="➕ Add New", command=self.add_entry,
            bg=self.primary_color, fg="white", font=self.font, relief="raised"
        ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            btn_frame, text="📋 Copy Password", command=self.copy_selected_password,
            bg=self.button_color, fg="white", font=self.font, relief="raised"
        ).grid(row=0, column=1, padx=5)
        
        tk.Button(
            btn_frame, text="🔁 Generate & Copy", command=self.gen_and_copy,
            bg=self.primary_color, fg="white", font=self.font, relief="raised"
        ).grid(row=0, column=2, padx=5)
        
        tk.Button(
            btn_frame, text="🗑️ Delete", command=self.delete_selected,
            bg="#f44336", fg="white", font=self.font, relief="raised"
        ).grid(row=0, column=3, padx=5)

        # Settings buttons
        settings_frame = tk.Frame(self.root, bg=self.bg_color)
        settings_frame.pack(pady=5)

        if FACE_RECOGNITION_AVAILABLE:
            tk.Button(
                settings_frame, text="📸 Face Auth Settings", command=self.manage_face_auth,
                bg=self.face_auth_color, fg="white", font=("Helvetica", 11), relief="raised"
            ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            settings_frame, text="🔒 Lock", command=self.lock_vault,
            bg="#9E9E9E", fg="white", font=("Helvetica", 11), relief="raised"
        ).grid(row=0, column=1, padx=5)

    # ==================== FACE AUTH SETTINGS ====================

    def manage_face_auth(self):
        """Face authentication settings dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("📸 Face Auth Settings")
        dialog.geometry("450x550")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()

        # Header
        tk.Label(
            dialog,
            text="📸 Face Authentication",
            font=("Helvetica", 16, "bold"),
            bg=self.bg_color,
            fg=self.header_color
        ).pack(pady=15)

        # Status
        status = self.face_auth.get_status()
        
        status_frame = tk.LabelFrame(dialog, text="Status", bg=self.bg_color)
        status_frame.pack(pady=10, fill="x", padx=20)
        
        status_text = (
            f"Face: {'✅ Registered' if status['face_registered'] else '❌ Not registered'} "
            f"({status['face_samples']} samples)\n"
            f"Quick PIN: {'✅ Enabled' if status['pin_enabled'] else '❌ Disabled'}\n"
            f"Liveness: {'✅ Enabled' if status['liveness_enabled'] else '❌ Disabled'} "
            f"({status['blinks_required']} blinks)\n"
            f"Security: {status['security_name']} ({status['security_level']*100:.0f}%)\n"
            f"PIN Unlock: ≥{status['face_only_threshold']:.0f}% confidence"
        )
        
        tk.Label(status_frame, text=status_text, font=("Helvetica", 10),
                bg=self.bg_color, justify="left").pack(pady=10, padx=10)

        # Quick PIN Section
        pin_frame = tk.LabelFrame(dialog, text="🔢 Quick PIN", bg=self.bg_color)
        pin_frame.pack(pady=10, fill="x", padx=20)
        
        if status['pin_enabled']:
            tk.Label(pin_frame, text="Quick PIN is enabled", bg=self.bg_color).pack(pady=5)
            
            def disable_pin():
                if messagebox.askyesno("Disable PIN", "Disable Quick PIN?"):
                    self.face_auth.disable_quick_pin()
                    dialog.destroy()
                    self.manage_face_auth()
            
            tk.Button(pin_frame, text="Disable PIN", command=disable_pin,
                    bg="#f44336", fg="white").pack(pady=5)
        else:
            tk.Label(pin_frame, text="Setup 4-6 digit PIN:", bg=self.bg_color).pack(pady=5)
            
            pin_var = tk.StringVar()
            pin_entry = tk.Entry(pin_frame, textvariable=pin_var, show="*", width=10, justify="center")
            pin_entry.pack(pady=5)
            
            def setup_pin():
                pin = pin_var.get()
                success, msg = self.face_auth.setup_quick_pin(pin)
                if success:
                    messagebox.showinfo("Success", "✅ PIN setup complete!")
                    dialog.destroy()
                    self.manage_face_auth()
                else:
                    messagebox.showerror("Error", msg)
            
            tk.Button(pin_frame, text="Setup PIN", command=setup_pin,
                    bg=self.primary_color, fg="white").pack(pady=5)

        # Liveness Section
        liveness_frame = tk.LabelFrame(dialog, text="👁️ Liveness Detection", bg=self.bg_color)
        liveness_frame.pack(pady=10, fill="x", padx=20)
        
        liveness_var = tk.BooleanVar(value=status['liveness_enabled'])
        tk.Checkbutton(
            liveness_frame,
            text="Enable blink detection",
            variable=liveness_var,
            bg=self.bg_color,
            command=lambda: self.face_auth.set_liveness_enabled(liveness_var.get())
        ).pack(pady=5)
        
        blinks_frame = tk.Frame(liveness_frame, bg=self.bg_color)
        blinks_frame.pack(pady=5)
        
        tk.Label(blinks_frame, text="Blinks required:", bg=self.bg_color).pack(side="left")
        blinks_var = tk.IntVar(value=status['blinks_required'])
        tk.Spinbox(blinks_frame, from_=1, to=5, textvariable=blinks_var, width=5,
                command=lambda: self.face_auth.set_blinks_required(blinks_var.get())).pack(side="left", padx=5)

        # Security Level
        security_frame = tk.LabelFrame(dialog, text="🔒 Security Level", bg=self.bg_color)
        security_frame.pack(pady=10, fill="x", padx=20)
        
        level_label = tk.Label(security_frame,
            text=f"{status['security_name']} ({status['security_level']*100:.0f}%)",
            bg=self.bg_color)
        level_label.pack(pady=5)
        
        security_var = tk.DoubleVar(value=status['security_level'] * 100)
        
        def update_level(*args):
            val = security_var.get()
            name = "Maximum" if val >= 90 else "High" if val >= 80 else "Medium" if val >= 60 else "Low"
            level_label.config(text=f"{name} ({val:.0f}%)")
        
        tk.Scale(security_frame, from_=50, to=95, orient="horizontal",
                variable=security_var, command=update_level, length=200,
                showvalue=False, bg=self.bg_color).pack(pady=5)
        
        tk.Button(security_frame, text="Apply",
                command=lambda: self.face_auth.set_security_level(security_var.get()/100),
                bg=self.primary_color, fg="white").pack(pady=5)

        # Actions
        actions_frame = tk.Frame(dialog, bg=self.bg_color)
        actions_frame.pack(pady=15)
        
        def re_register():
            dialog.destroy()
            if messagebox.askyesno("Re-register", "Delete face data and re-register?"):
                self.face_auth.reset_face_data()
                self.face_setup_screen()
        
        def reset_all():
            if messagebox.askyesno("Reset ALL", "Delete ALL face auth data?"):
                self.face_auth.reset_all_data()
                dialog.destroy()
                messagebox.showinfo("Done", "All data reset.")
        
        tk.Button(actions_frame, text="🔄 Re-register", command=re_register,
                bg=self.face_auth_color, fg="white", width=15).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(actions_frame, text="📋 History", 
                command=lambda: self.show_auth_history(dialog),
                bg="#607D8B", fg="white", width=15).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(actions_frame, text="🗑️ Reset All", command=reset_all,
                bg="#f44336", fg="white", width=15).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(actions_frame, text="Close", command=dialog.destroy,
                bg="#9E9E9E", fg="white", width=15).grid(row=1, column=1, padx=5, pady=5)


    def show_auth_history(self, parent):
        """Show authentication history."""
        history = self.face_auth.get_auth_history(20)
        
        dialog = tk.Toplevel(parent)
        dialog.title("Auth History")
        dialog.geometry("500x300")
        
        text = tk.Text(dialog, font=("Courier", 9))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", "".join(history) if history else "No history")
        text.config(state="disabled")
        
        tk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)

    def lock_vault(self):
        """Lock the vault and return to login."""
        self.vault = {}
        self.key = None
        self.revealed_rows = {}
        
        if FACE_RECOGNITION_AVAILABLE and self.face_auth.is_registered():
            self.face_login_screen()
        else:
            self.login_screen()

    # ==================== VAULT OPERATIONS ====================

    def refresh_tree(self):
        """Refresh the password tree view."""
        self.tree.delete(*self.tree.get_children())
        query = self.search_var.get().lower().strip()

        for service, creds in self.vault.items():
            if query in service.lower() or query in creds["username"].lower():
                is_revealed = self.revealed_rows.get(service, False)
                password = creds["password"] if is_revealed else "●●●●●●●●"
                action = "Hide" if is_revealed else "Show"
                self.tree.insert("", "end", iid=service, values=(service, creds["username"], password, action))

        self.tree.bind("<ButtonRelease-1>", self.toggle_password)

    def toggle_password(self, event=None):
        """Toggle password visibility in the tree."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item_id = selected_item[0]
        col = self.tree.identify_column(event.x)

        if col != "#4":
            return

        service_key = item_id

        if service_key not in self.vault:
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
        """Add a new password entry."""
        service = simpledialog.askstring("Service Name", "Enter service name:")
        if not service:
            return
        username = simpledialog.askstring("Username", "Enter username:")
        if username is None:
            return
        password = simpledialog.askstring("Password", "Enter password:", show="*")
        if password is None:
            return

        self.vault[service] = {"username": username, "password": password}
        save_vault(self.vault, self.key)
        self.refresh_tree()

    def copy_selected_password(self):
        """Copy selected password to clipboard."""
        selected = self.tree.focus()
        if selected:
            pw = self.vault[selected]["password"]
            pyperclip.copy(pw)
            messagebox.showinfo("Copied", f"🔐 Password for '{selected}' copied!")
        else:
            messagebox.showwarning("No selection", "Please select an entry.")

    def gen_and_copy(self):
        """Generate a password and copy to clipboard."""
        pwd = generate_password()
        pyperclip.copy(pwd)
        messagebox.showinfo("Generated", f"Password copied:\n\n{pwd}")

    def delete_selected(self):
        """Delete selected password entry."""
        selected = self.tree.focus()
        if selected:
            if messagebox.askyesno("Delete", f"Delete '{selected}'?"):
                del self.vault[selected]
                save_vault(self.vault, self.key)
                self.refresh_tree()
                messagebox.showinfo("Deleted", f"'{selected}' deleted.")
        else:
            messagebox.showwarning("No selection", "Please select an entry.")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 50)
    print("Anay's Password Vault")
    print("=" * 50)
    
    if FACE_RECOGNITION_AVAILABLE:
        print("[OK] Face recognition available")
    else:
        print("[WARNING] Face recognition not available")
        print("         Running in password-only mode")
    
    print()
    
    root = tk.Tk()
    root.geometry("800x650")
    app = PasswordManagerGUI(root)
    root.mainloop()