"""
Face Recognition Authentication Module
Uses OpenCV Haar Cascade + LBPH Face Recognizer for biometric authentication.
Stores face encodings locally as an XML model.
"""

import os
import sys
import time
import hashlib
import base64
import cv2
import cv2.face
import numpy as np
import tkinter as tk
from tkinter import messagebox
import threading
import logging
from typing import Optional
from cryptography.fernet import Fernet
from vault_core import DATA_DIR

# Configuration
FACE_MODEL_FILE = os.path.join(DATA_DIR, "face_model.xml")
FACE_DATA_FILE = os.path.join(DATA_DIR, "face_data.npz")
FACE_KEY_FILE = os.path.join(DATA_DIR, "face_vault_key.enc")
CONFIDENCE_THRESHOLD = 70  # Lower = stricter authentication (0-100, 0=perfect match)
CONFIDENCE_AUTO_LOGIN = 60  # If confidence < this, skip master password entirely
FACE_CAPTURE_DELAY = 3  # Seconds between face capture attempts
BLUR_THRESHOLD = 80  # Lower = less tolerant of blur (Laplacian variance)
ENROLL_SAMPLES = 25  # Number of face samples to capture for training

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _is_blurry(image, threshold: int = BLUR_THRESHOLD) -> bool:
    """Check if an image is blurry using variance of Laplacian."""
    return cv2.Laplacian(image, cv2.CV_64F).var() < threshold


def _preprocess_face(face_roi):
    """Apply histogram equalization for consistent lighting + resize."""
    equalized = cv2.equalizeHist(face_roi)
    return cv2.resize(equalized, (200, 200))


def _load_face_cascade():
    """Load the best available Haar cascade for face detection."""
    paths = [
        cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml",
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
    ]
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        paths.extend([
            os.path.join(base, "cv2", "data", "haarcascade_frontalface_alt2.xml"),
            os.path.join(base, "cv2", "data", "haarcascade_frontalface_default.xml"),
        ])
    for p in paths:
        cascade = cv2.CascadeClassifier(p)
        if not cascade.empty():
            return cascade
    raise RuntimeError("Failed to load face detection cascade.")


def is_face_registered() -> bool:
    """Check if a face model already exists."""
    return os.path.exists(FACE_MODEL_FILE) and os.path.exists(FACE_DATA_FILE)


def _check_face_support():
    """Check if OpenCV contrib face module is available. Raises RuntimeError if not."""
    if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
        raise RuntimeError(
            "OpenCV face module not found. Install: pip install opencv-contrib-python"
        )


def capture_face_samples(num_samples: int = ENROLL_SAMPLES) -> list:
    """
    Capture face samples from webcam for enrollment.
    Uses preprocessing (histogram equalization) and blur rejection
    to produce high-quality training data.
    Returns list of preprocessed face grayscale arrays.
    Camera is always released, even on error.
    """
    cap = None
    try:
        face_cascade = _load_face_cascade()

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Could not access webcam.")

        samples = []
        captured = 0
        rejected = 0

        while captured < num_samples:
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(100, 100))

            for (x, y, w, h) in faces:
                # Pad ROI slightly for better feature extraction
                pad = int(min(w, h) * 0.1)
                x1, y1 = max(0, x - pad), max(0, y - pad)
                x2, y2 = min(frame.shape[1], x + w + pad), min(frame.shape[0], y + h + pad)
                face_roi = gray[y1:y2, x1:x2]

                # Reject blurry samples
                if _is_blurry(face_roi):
                    rejected += 1
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(frame, "BLURRY! Hold still...", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    continue

                processed = _preprocess_face(face_roi)
                samples.append(processed)
                captured += 1
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"Captured: {captured}/{num_samples}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

            quality_msg = f"Rejected blurry: {rejected}" if rejected else ""
            cv2.putText(frame, quality_msg, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.imshow("Face Enrollment - Press 'q' to quit", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            # Delay between captures so user can reposition
            if captured > 0 and captured < num_samples:
                for remaining in range(FACE_CAPTURE_DELAY, 0, -1):
                    display = frame.copy()
                    status_color = (0, 255, 0)
                    cv2.putText(
                        display,
                        f"Next capture in {remaining}s - hold still...",
                        (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )
                    cv2.putText(
                        display,
                        f"Captured: {captured}/{num_samples}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        status_color,
                        2,
                    )
                    cv2.imshow("Face Enrollment - Press 'q' to quit", display)
                    if cv2.waitKey(1000) & 0xFF == ord("q"):
                        raise RuntimeError("Enrollment cancelled by user.")

        if len(samples) < 5:
            raise RuntimeError("Not enough face samples captured. Need at least 5.")

        logging.info(f"Enrollment complete: {len(samples)} good samples, {rejected} blurry rejected")
        return samples
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


def enroll_face():
    """Enroll user's face: capture samples, train LBPH model, save to file."""
    _check_face_support()
    samples = capture_face_samples()

    labels = np.ones(len(samples), dtype=np.int32)
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(samples, labels)
    recognizer.write(FACE_MODEL_FILE)
    np.savez(FACE_DATA_FILE, samples=np.array(samples), labels=labels)
    logging.info("Face model trained and saved successfully.")


def authenticate_face(timeout: int = 30) -> str:
    """
    Authenticate user by comparing live webcam face to enrolled face model.
    Uses same preprocessing (histogram equalization) as enrollment for consistent matching.
    Returns: 'full' (high confidence - skip master password),
             'partial' (matching but need master password),
             'failed' (no match)
    """
    _check_face_support()
    if not is_face_registered():
        raise RuntimeError("No face model found. Please enroll first.")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(FACE_MODEL_FILE)

    face_cascade = _load_face_cascade()

    cap = None
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Could not access webcam.")

        start_time = cv2.getTickCount()
        attempts = 0
        max_attempts = 15
        result = 'failed'

        while attempts < max_attempts:
            elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            if elapsed > timeout:
                break

            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(100, 100))

            for (x, y, w, h) in faces:
                attempts += 1
                face_roi = gray[y : y + h, x : x + w]
                processed = _preprocess_face(face_roi)
                label, confidence = recognizer.predict(processed)

                border_color = (0, 255, 0) if confidence < CONFIDENCE_THRESHOLD else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x + w, y + h), border_color, 2)
                cv2.putText(
                    frame,
                    f"Confidence: {confidence:.1f}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    border_color,
                    2,
                )

                if confidence < CONFIDENCE_AUTO_LOGIN:
                    result = 'full'
                    cv2.putText(frame, "MATCH! (Full Access)",
                                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.imshow("Face Authentication", frame)
                    cv2.waitKey(1000)
                    break
                elif confidence < CONFIDENCE_THRESHOLD:
                    result = 'partial'
                    cv2.putText(frame, "MATCH! (Enter password)",
                                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    cv2.imshow("Face Authentication", frame)
                    cv2.waitKey(1000)
                    break

            if result != 'failed':
                break

            cv2.putText(
                frame,
                f"Look at camera... ({attempts}/{max_attempts})",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2,
            )
            cv2.imshow("Face Authentication - Press 'q' to quit", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time.sleep(0.5)

        return result
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


def delete_face_data():
    """Remove stored face model, vault key and data files."""
    for f in [FACE_MODEL_FILE, FACE_DATA_FILE, FACE_KEY_FILE]:
        if os.path.exists(f):
            os.remove(f)


def save_vault_key_for_face(vault_key: bytes):
    """Encrypt and store the vault key, unlockable by face data."""
    if not os.path.exists(FACE_DATA_FILE):
        return
    data = np.load(FACE_DATA_FILE)
    samples = data['samples']
    samples_bytes = samples.tobytes()
    salt = os.urandom(16)
    face_key = hashlib.pbkdf2_hmac('sha256', samples_bytes, salt, 100000, dklen=32)
    face_key_b64 = base64.urlsafe_b64encode(face_key)
    fernet = Fernet(face_key_b64)
    encrypted_key = fernet.encrypt(vault_key)
    with open(FACE_KEY_FILE, 'wb') as f:
        f.write(salt + encrypted_key)


def get_vault_key_from_face() -> Optional[bytes]:
    """Decrypt and return the vault key using enrolled face data."""
    if not os.path.exists(FACE_KEY_FILE) or not os.path.exists(FACE_DATA_FILE):
        return None
    with open(FACE_KEY_FILE, 'rb') as f:
        data_bytes = f.read()
    salt = data_bytes[:16]
    encrypted_key = data_bytes[16:]
    data = np.load(FACE_DATA_FILE)
    samples = data['samples']
    samples_bytes = samples.tobytes()
    face_key = hashlib.pbkdf2_hmac('sha256', samples_bytes, salt, 100000, dklen=32)
    face_key_b64 = base64.urlsafe_b64encode(face_key)
    fernet = Fernet(face_key_b64)
    try:
        return fernet.decrypt(encrypted_key)
    except Exception:
        return None


# ---------- Tkinter Integration ----------

class FaceAuthDialog:
    """Tkinter dialog for face enrollment and authentication."""

    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.result = 'failed'
        self.auth_completed = False

    def run_enrollment(self) -> bool:
        """Run face enrollment in a separate thread with UI feedback."""
        if not messagebox.askyesno(
            "Face Enrollment",
            "This will capture your face using the webcam.\n"
            "Make sure your face is well-lit and visible.\n\nContinue?",
            parent=self.parent,
        ):
            return False

        threading.Thread(target=self._enroll_thread, daemon=True).start()
        messagebox.showinfo(
            "Face Enrollment",
            "Webcam will open. Look at the camera while we capture your face.\n"
            "Press 'q' to quit early if needed.",
            parent=self.parent,
        )
        return True

    def _enroll_thread(self):
        try:
            enroll_face()
            self.parent.after(0, self._show_enroll_success)
        except Exception as e:
            error_text = str(e)
            self.parent.after(0, self._show_enroll_error, error_text)

    def _show_enroll_success(self):
        messagebox.showinfo("Success", "Face enrolled successfully!", parent=self.parent)

    def _show_enroll_error(self, error_text):
        messagebox.showerror("Enrollment Failed", error_text, parent=self.parent)

    def run_authentication(self, silent: bool = False) -> bool:
        """Run face authentication with UI feedback.
        If silent=True, skip the info messagebox (used for auto-start).
        """
        if not is_face_registered():
            if not silent:
                msg = messagebox.askyesno(
                    "No Face Registered",
                    "No face data found. Would you like to enroll now?",
                    parent=self.parent,
                )
                if msg:
                    return self.run_enrollment()
            return False

        threading.Thread(target=self._auth_thread, daemon=True).start()
        if not silent:
            messagebox.showinfo(
                "Face Authentication",
                "Webcam will open. Look at the camera to authenticate.\n"
                "Press 'q' to cancel.",
                parent=self.parent,
            )
        return True

    def _auth_thread(self):
        try:
            result = authenticate_face()
            self.result = result
            self.auth_completed = True
            self.parent.after(0, self._on_auth_done, result)
        except Exception as e:
            self.result = 'failed'
            self.auth_completed = True
            error_text = str(e)
            self.parent.after(0, self._show_auth_error, error_text)

    def _on_auth_done(self, result: str):
        pass  # GUI polling loop handles all user feedback

    def _show_auth_error(self, error_text):
        messagebox.showerror("Error", error_text, parent=self.parent)

