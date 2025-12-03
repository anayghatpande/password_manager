"""
Face Authentication Module for Anay's Password Vault
With Liveness Detection and Quick PIN Support
"""

import cv2
import numpy as np
import os
import pickle
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime

# Import face_recognition
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[WARNING] face_recognition module not available")


class FaceAuthenticator:
    """
    Face Authentication with:
    - Liveness detection (blink detection)
    - Quick PIN for face-only unlock
    - Configurable security thresholds
    """
    
    # Security Levels
    SECURITY_LOW = 0.50
    SECURITY_MEDIUM = 0.60
    SECURITY_HIGH = 0.70
    SECURITY_FACE_ONLY = 0.80  # Minimum for PIN unlock
    SECURITY_MAXIMUM = 0.90
    
    def __init__(self, data_dir: str = "face_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Files
        self.encodings_file = self.data_dir / "face_encodings.pkl"
        self.settings_file = self.data_dir / "settings.pkl"
        self.pin_file = self.data_dir / "quick_pin.pkl"
        
        # Temp file
        self.temp_dir = tempfile.gettempdir()
        self.temp_image_path = os.path.join(self.temp_dir, "face_auth_temp.jpg")
        
        # Face data
        self.known_face_encodings = []
        
        # Security settings
        self.min_confidence_threshold = self.SECURITY_MEDIUM  # 60% default
        self.face_only_threshold = 0.80  # 80% for PIN unlock
        self.max_attempts = 3
        self.current_attempt = 0
        
        # Liveness detection
        self.liveness_enabled = True
        self.blink_counter = 0
        self.blinks_required = 2
        self.liveness_verified = False
        self.last_ear = 1.0
        self.ear_threshold = 0.22
        self.blink_state = "open"
        
        # Quick PIN
        self.pin_enabled = False
        
        # Load data
        self._load_settings()
        self.load_encodings()
        self._load_pin_status()
        
        print(f"[FaceAuth] Threshold: {self.min_confidence_threshold * 100:.0f}%")
        print(f"[FaceAuth] PIN unlock: {'Enabled' if self.pin_enabled else 'Disabled'}")
        print(f"[FaceAuth] Liveness: {'Enabled' if self.liveness_enabled else 'Disabled'}")
    
    # ==================== SETTINGS ====================
    
    def _load_settings(self):
        """Load settings."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'rb') as f:
                    settings = pickle.load(f)
                    self.min_confidence_threshold = settings.get('min_confidence_threshold', 0.60)
                    self.face_only_threshold = settings.get('face_only_threshold', 0.80)
                    self.max_attempts = settings.get('max_attempts', 3)
                    self.liveness_enabled = settings.get('liveness_enabled', True)
                    self.blinks_required = settings.get('blinks_required', 2)
            except Exception as e:
                print(f"Settings load error: {e}")
    
    def _save_settings(self):
        """Save settings."""
        try:
            settings = {
                'min_confidence_threshold': self.min_confidence_threshold,
                'face_only_threshold': self.face_only_threshold,
                'max_attempts': self.max_attempts,
                'liveness_enabled': self.liveness_enabled,
                'blinks_required': self.blinks_required,
                'pin_enabled': self.pin_enabled
            }
            with open(self.settings_file, 'wb') as f:
                pickle.dump(settings, f)
            return True
        except Exception as e:
            print(f"Settings save error: {e}")
            return False
    
    def set_security_level(self, level: float) -> bool:
        """Set security level (0.0 to 1.0)."""
        if 0.0 <= level <= 1.0:
            self.min_confidence_threshold = level
            self._save_settings()
            return True
        return False
    
    def get_security_level(self) -> float:
        """Get current security level."""
        return self.min_confidence_threshold
    
    def get_security_level_name(self) -> str:
        """Get security level name."""
        level = self.min_confidence_threshold
        if level >= 0.90:
            return "Maximum"
        elif level >= 0.80:
            return "High"
        elif level >= 0.70:
            return "Medium-High"
        elif level >= 0.60:
            return "Medium"
        else:
            return "Low"
    
    def set_liveness_enabled(self, enabled: bool):
        """Enable/disable liveness detection."""
        self.liveness_enabled = enabled
        self._save_settings()
    
    def set_blinks_required(self, count: int):
        """Set number of blinks required."""
        self.blinks_required = max(1, min(5, count))
        self._save_settings()
    
    # ==================== QUICK PIN ====================
    
    def setup_quick_pin(self, pin: str) -> tuple:
        """
        Setup quick PIN (4-6 digits).
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Validate PIN
        if not pin.isdigit():
            return False, "PIN must contain only digits"
        
        if len(pin) < 4 or len(pin) > 6:
            return False, "PIN must be 4-6 digits"
        
        try:
            # Hash PIN with salt
            salt = os.urandom(16)
            pin_hash = hashlib.pbkdf2_hmac('sha256', pin.encode(), salt, 100000)
            
            data = {
                'pin_hash': pin_hash,
                'salt': salt,
                'created_at': datetime.now().isoformat()
            }
            
            with open(self.pin_file, 'wb') as f:
                pickle.dump(data, f)
            
            self.pin_enabled = True
            self._save_settings()
            
            return True, "Quick PIN setup successfully!"
            
        except Exception as e:
            return False, f"PIN setup failed: {str(e)}"
    
    def verify_pin(self, pin: str) -> tuple:
        """
        Verify quick PIN.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.pin_enabled or not self.pin_file.exists():
            return False, "Quick PIN not enabled"
        
        try:
            with open(self.pin_file, 'rb') as f:
                data = pickle.load(f)
            
            pin_hash = hashlib.pbkdf2_hmac('sha256', pin.encode(), data['salt'], 100000)
            
            if pin_hash == data['pin_hash']:
                return True, "PIN verified!"
            else:
                return False, "Incorrect PIN"
                
        except Exception as e:
            return False, f"PIN verification failed: {str(e)}"
    
    def _load_pin_status(self):
        """Load PIN enabled status."""
        self.pin_enabled = self.pin_file.exists()
    
    def disable_quick_pin(self) -> bool:
        """Disable quick PIN."""
        try:
            if self.pin_file.exists():
                self.pin_file.unlink()
            self.pin_enabled = False
            self._save_settings()
            return True
        except Exception:
            return False
    
    def is_pin_enabled(self) -> bool:
        """Check if PIN is enabled."""
        return self.pin_enabled
    
    # ==================== LIVENESS DETECTION ====================
    
    def _calculate_ear(self, eye_points):
        """Calculate Eye Aspect Ratio."""
        try:
            # Vertical distances
            A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
            B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
            # Horizontal distance
            C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
            
            ear = (A + B) / (2.0 * C) if C > 0 else 0
            return ear
        except Exception:
            return 0.3
    
    def check_liveness_frame(self, frame) -> tuple:
        """
        Check single frame for liveness (blink detection).
        
        Returns:
            tuple: (is_verified: bool, blink_count: int, message: str)
        """
        if not self.liveness_enabled:
            return True, 0, "Liveness disabled"
        
        if self.liveness_verified:
            return True, self.blink_counter, "Already verified"
        
        if not FACE_RECOGNITION_AVAILABLE:
            return True, 0, "Skipped"
        
        try:
            # Save and load image
            cv2.imwrite(self.temp_image_path, frame)
            image = face_recognition.load_image_file(self.temp_image_path)
            
            # Get face landmarks
            landmarks_list = face_recognition.face_landmarks(image)
            
            if not landmarks_list:
                return False, self.blink_counter, "No face for liveness"
            
            landmarks = landmarks_list[0]
            
            # Get eyes
            left_eye = landmarks.get('left_eye', [])
            right_eye = landmarks.get('right_eye', [])
            
            if len(left_eye) < 6 or len(right_eye) < 6:
                return False, self.blink_counter, "Eyes not detected"
            
            # Calculate EAR
            left_ear = self._calculate_ear(left_eye)
            right_ear = self._calculate_ear(right_eye)
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Detect blink
            if avg_ear < self.ear_threshold:
                if self.blink_state == "open":
                    self.blink_state = "closed"
            else:
                if self.blink_state == "closed":
                    self.blink_counter += 1
                    self.blink_state = "open"
            
            self.last_ear = avg_ear
            
            # Check if enough blinks
            if self.blink_counter >= self.blinks_required:
                self.liveness_verified = True
                return True, self.blink_counter, f"Liveness verified! ({self.blink_counter} blinks)"
            
            remaining = self.blinks_required - self.blink_counter
            return False, self.blink_counter, f"Blink {remaining} more time(s)"
            
        except Exception as e:
            # Don't block on liveness errors
            return True, 0, f"Liveness check skipped: {str(e)[:20]}"
    
    def reset_liveness(self):
        """Reset liveness detection state."""
        self.blink_counter = 0
        self.liveness_verified = False
        self.blink_state = "open"
        self.last_ear = 1.0
    
    def is_liveness_verified(self) -> bool:
        """Check if liveness is verified."""
        return not self.liveness_enabled or self.liveness_verified
    
    # ==================== FACE ENCODING ====================
    
    def load_encodings(self) -> bool:
        """Load face encodings."""
        if self.encodings_file.exists():
            try:
                with open(self.encodings_file, 'rb') as f:
                    self.known_face_encodings = pickle.load(f)
                return True
            except Exception:
                return False
        return False
    
    def save_encodings(self) -> bool:
        """Save face encodings."""
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.known_face_encodings, f)
            return True
        except Exception:
            return False
    
    def is_registered(self) -> bool:
        """Check if face is registered."""
        return len(self.known_face_encodings) > 0 and FACE_RECOGNITION_AVAILABLE
    
    def get_registration_count(self) -> int:
        """Get number of face samples."""
        return len(self.known_face_encodings)
    
    def _load_image_reliable(self, frame):
        """Reliable image loading."""
        if not FACE_RECOGNITION_AVAILABLE:
            return None
        try:
            cv2.imwrite(self.temp_image_path, frame)
            return face_recognition.load_image_file(self.temp_image_path)
        except Exception:
            return None
    
    def detect_and_encode_face(self, frame):
        """Detect and encode face."""
        if not FACE_RECOGNITION_AVAILABLE:
            return None, None, "Not available"
        
        image = self._load_image_reliable(frame)
        if image is None:
            return None, None, "Image load failed"
        
        try:
            locations = face_recognition.face_locations(image, model="hog")
            
            if len(locations) == 0:
                return None, None, "No face detected"
            if len(locations) > 1:
                return None, None, "Multiple faces"
            
            encodings = face_recognition.face_encodings(image, locations)
            
            if len(encodings) == 0:
                return None, None, "Encoding failed"
            
            return encodings[0], locations[0], None
            
        except Exception as e:
            return None, None, str(e)
    
    def register_face_from_frame(self, frame) -> tuple:
        """Register face from frame."""
        encoding, location, error = self.detect_and_encode_face(frame)
        
        if error:
            return False, error
        
        self.known_face_encodings.append(encoding)
        self.save_encodings()
        
        # Save image
        try:
            img_path = self.data_dir / f"registration_{len(self.known_face_encodings)}.jpg"
            cv2.imwrite(str(img_path), frame)
        except Exception:
            pass
        
        return True, f"Sample {len(self.known_face_encodings)} registered!"
    
    # ==================== FACE VERIFICATION ====================
    
    def verify_face_from_frame(self, frame) -> tuple:
        """
        Verify face from frame.
        
        Returns:
            tuple: (success: bool, confidence: float, message: str, can_use_pin: bool)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return False, 0, "Not available", False
        
        if not self.is_registered():
            return False, 0, "No face registered", False
        
        # Check liveness first (if enabled)
        if self.liveness_enabled and not self.liveness_verified:
            is_live, blinks, msg = self.check_liveness_frame(frame)
            if not is_live:
                return False, 0, msg, False
        
        encoding, location, error = self.detect_and_encode_face(frame)
        
        if error:
            return False, 0, error, False
        
        try:
            # Calculate confidence
            distances = face_recognition.face_distance(self.known_face_encodings, encoding)
            best_distance = min(distances)
            confidence = (1 - best_distance) * 100
            confidence = max(0, min(100, confidence))
            
            threshold_percent = self.min_confidence_threshold * 100
            face_only_percent = self.face_only_threshold * 100
            
            # Can use PIN if: confidence >= 80% AND liveness verified AND PIN enabled
            can_use_pin = (
                confidence >= face_only_percent and
                self.is_liveness_verified() and
                self.pin_enabled
            )
            
            # Log attempt
            self._log_attempt(confidence >= threshold_percent, confidence, threshold_percent, can_use_pin)
            
            if confidence >= threshold_percent:
                self.current_attempt = 0
                
                if can_use_pin:
                    return True, confidence, f"Verified ({confidence:.0f}%) - PIN unlock available!", True
                else:
                    return True, confidence, f"Verified ({confidence:.0f}%)", False
            else:
                self.current_attempt += 1
                remaining = max(0, self.max_attempts - self.current_attempt)
                return False, confidence, f"Low: {confidence:.0f}% (need {threshold_percent:.0f}%) - {remaining} left", False
            
        except Exception as e:
            return False, 0, str(e), False
    
    def get_face_confidence(self, frame) -> tuple:
        """Get confidence without counting attempt."""
        if not FACE_RECOGNITION_AVAILABLE or not self.is_registered():
            return False, 0, "N/A"
        
        encoding, _, error = self.detect_and_encode_face(frame)
        if error:
            return False, 0, error
        
        try:
            distances = face_recognition.face_distance(self.known_face_encodings, encoding)
            confidence = (1 - min(distances)) * 100
            return True, max(0, min(100, confidence)), "OK"
        except Exception:
            return False, 0, "Error"
    
    # ==================== UTILITY ====================
    
    def reset_attempts(self):
        """Reset attempts and liveness."""
        self.current_attempt = 0
        self.reset_liveness()
    
    def is_locked_out(self) -> bool:
        """Check if locked out."""
        return self.current_attempt >= self.max_attempts
    
    def get_remaining_attempts(self) -> int:
        """Get remaining attempts."""
        return max(0, self.max_attempts - self.current_attempt)
    
    def _log_attempt(self, success: bool, confidence: float, threshold: float, pin_unlock: bool):
        """Log authentication attempt."""
        try:
            log_file = self.data_dir / "auth_log.txt"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "OK" if success else "FAIL"
            unlock = "PIN" if pin_unlock else "PASS"
            
            with open(log_file, 'a') as f:
                f.write(f"{timestamp} | {status} | {unlock} | {confidence:.1f}% | min:{threshold:.0f}%\n")
        except Exception:
            pass
    
    def get_auth_history(self, limit: int = 10) -> list:
        """Get auth history."""
        log_file = self.data_dir / "auth_log.txt"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                return lines[-limit:] if len(lines) > limit else lines
            except Exception:
                pass
        return []
    
    def reset_face_data(self) -> bool:
        """Reset face data."""
        try:
            if self.encodings_file.exists():
                self.encodings_file.unlink()
            self.known_face_encodings = []
            
            for img in self.data_dir.glob("registration_*.jpg"):
                try:
                    img.unlink()
                except Exception:
                    pass
            return True
        except Exception:
            return False
    
    def reset_all_data(self) -> bool:
        """Reset all authentication data."""
        try:
            self.reset_face_data()
            self.disable_quick_pin()
            if self.settings_file.exists():
                self.settings_file.unlink()
            log_file = self.data_dir / "auth_log.txt"
            if log_file.exists():
                log_file.unlink()
            return True
        except Exception:
            return False
    
    def get_status(self) -> dict:
        """Get current status."""
        return {
            'face_registered': self.is_registered(),
            'face_samples': self.get_registration_count(),
            'pin_enabled': self.pin_enabled,
            'liveness_enabled': self.liveness_enabled,
            'liveness_verified': self.liveness_verified,
            'blinks_done': self.blink_counter,
            'blinks_required': self.blinks_required,
            'security_level': self.get_security_level(),
            'security_name': self.get_security_level_name(),
            'face_only_threshold': self.face_only_threshold * 100
        }
    
    def __del__(self):
        """Cleanup."""
        try:
            if hasattr(self, 'temp_image_path') and os.path.exists(self.temp_image_path):
                os.remove(self.temp_image_path)
        except Exception:
            pass