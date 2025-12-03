"""
Camera and Face Recognition Diagnostic Tool
Run this to identify the exact issue
"""

import sys
print("=" * 60)
print("Camera & Face Recognition Diagnostic Tool")
print("=" * 60)
print()

# Check imports
print("[1] Checking required modules...")
print()

modules_ok = True

try:
    import cv2
    print(f"    [OK] OpenCV version: {cv2.__version__}")
except ImportError as e:
    print(f"    [ERROR] OpenCV: {e}")
    modules_ok = False

try:
    import numpy as np
    print(f"    [OK] NumPy version: {np.__version__}")
except ImportError as e:
    print(f"    [ERROR] NumPy: {e}")
    modules_ok = False

try:
    from PIL import Image
    print(f"    [OK] Pillow: available")
except ImportError as e:
    print(f"    [ERROR] Pillow: {e}")
    modules_ok = False

try:
    import face_recognition
    print(f"    [OK] face_recognition: available")
except ImportError as e:
    print(f"    [ERROR] face_recognition: {e}")
    modules_ok = False

try:
    import dlib
    print(f"    [OK] dlib version: {dlib.__version__}")
except ImportError as e:
    print(f"    [ERROR] dlib: {e}")
    modules_ok = False

if not modules_ok:
    print()
    print("[FATAL] Some modules are missing. Please install them first.")
    sys.exit(1)

print()
print("[2] Testing camera access...")
print()

# Try to open camera
cap = None
camera_index = None

for idx in [0, 1, -1]:
    print(f"    Trying camera index {idx}...")
    try:
        test_cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret and frame is not None:
                print(f"    [OK] Camera {idx} works!")
                cap = test_cap
                camera_index = idx
                break
            else:
                print(f"    [FAIL] Camera {idx} opened but can't read frames")
                test_cap.release()
        else:
            print(f"    [FAIL] Camera {idx} couldn't be opened")
    except Exception as e:
        print(f"    [ERROR] Camera {idx}: {e}")

# Try without DirectShow
if cap is None:
    print()
    print("    Trying without DirectShow...")
    for idx in [0, 1]:
        try:
            test_cap = cv2.VideoCapture(idx)
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                if ret and frame is not None:
                    print(f"    [OK] Camera {idx} works!")
                    cap = test_cap
                    camera_index = idx
                    break
                test_cap.release()
        except Exception as e:
            print(f"    [ERROR] Camera {idx}: {e}")

if cap is None:
    print()
    print("[FATAL] No working camera found!")
    sys.exit(1)

print()
print("[3] Analyzing camera frame...")
print()

ret, frame = cap.read()

if not ret or frame is None:
    print("[ERROR] Could not read frame from camera")
    cap.release()
    sys.exit(1)

print(f"    Frame type     : {type(frame)}")
print(f"    Frame dtype    : {frame.dtype}")
print(f"    Frame shape    : {frame.shape}")
print(f"    Frame size     : {frame.size}")
print(f"    Is contiguous  : {frame.flags['C_CONTIGUOUS']}")
print(f"    Min value      : {frame.min()}")
print(f"    Max value      : {frame.max()}")

print()
print("[4] Testing image conversion...")
print()

# Test BGR to RGB conversion
try:
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    print(f"    [OK] BGR to RGB conversion successful")
    print(f"        RGB dtype    : {rgb_frame.dtype}")
    print(f"        RGB shape    : {rgb_frame.shape}")
    print(f"        Is contiguous: {rgb_frame.flags['C_CONTIGUOUS']}")
except Exception as e:
    print(f"    [ERROR] BGR to RGB conversion failed: {e}")
    cap.release()
    sys.exit(1)

# Make contiguous
try:
    rgb_contiguous = np.ascontiguousarray(rgb_frame, dtype=np.uint8)
    print(f"    [OK] Made contiguous array")
    print(f"        Contiguous dtype: {rgb_contiguous.dtype}")
    print(f"        Is contiguous   : {rgb_contiguous.flags['C_CONTIGUOUS']}")
except Exception as e:
    print(f"    [ERROR] Making contiguous failed: {e}")

print()
print("[5] Testing face_recognition with frame...")
print()

# Test face detection
try:
    print("    Testing face_locations()...")
    
    # Method 1: Direct
    print("    Method 1: Direct frame...")
    try:
        locations = face_recognition.face_locations(rgb_contiguous, model="hog")
        print(f"    [OK] Method 1 works! Faces found: {len(locations)}")
    except Exception as e:
        print(f"    [FAIL] Method 1: {e}")
    
    # Method 2: Resize first
    print("    Method 2: Resized frame...")
    try:
        small = cv2.resize(rgb_contiguous, (320, 240))
        small = np.ascontiguousarray(small, dtype=np.uint8)
        locations = face_recognition.face_locations(small, model="hog")
        print(f"    [OK] Method 2 works! Faces found: {len(locations)}")
    except Exception as e:
        print(f"    [FAIL] Method 2: {e}")
    
    # Method 3: Load from saved file
    print("    Method 3: Save and reload...")
    try:
        cv2.imwrite("test_frame.jpg", frame)
        loaded_img = face_recognition.load_image_file("test_frame.jpg")
        print(f"        Loaded image type : {type(loaded_img)}")
        print(f"        Loaded image dtype: {loaded_img.dtype}")
        print(f"        Loaded image shape: {loaded_img.shape}")
        locations = face_recognition.face_locations(loaded_img, model="hog")
        print(f"    [OK] Method 3 works! Faces found: {len(locations)}")
        
        # Clean up
        import os
        os.remove("test_frame.jpg")
    except Exception as e:
        print(f"    [FAIL] Method 3: {e}")
    
    # Method 4: Manual array creation
    print("    Method 4: Manual array creation...")
    try:
        height, width = frame.shape[:2]
        manual_rgb = np.zeros((height, width, 3), dtype=np.uint8)
        manual_rgb[:, :, 0] = frame[:, :, 2]  # R
        manual_rgb[:, :, 1] = frame[:, :, 1]  # G
        manual_rgb[:, :, 2] = frame[:, :, 0]  # B
        locations = face_recognition.face_locations(manual_rgb, model="hog")
        print(f"    [OK] Method 4 works! Faces found: {len(locations)}")
    except Exception as e:
        print(f"    [FAIL] Method 4: {e}")

except Exception as e:
    print(f"    [ERROR] Face detection test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("[6] Testing live detection loop...")
print()

print("    Running 5 frames of live detection...")
success_count = 0
fail_count = 0

for i in range(5):
    ret, frame = cap.read()
    if ret and frame is not None:
        try:
            # Save and reload method (most reliable)
            cv2.imwrite("temp_frame.jpg", frame)
            img = face_recognition.load_image_file("temp_frame.jpg")
            locations = face_recognition.face_locations(img, model="hog")
            success_count += 1
            print(f"    Frame {i+1}: [OK] Faces: {len(locations)}")
        except Exception as e:
            fail_count += 1
            print(f"    Frame {i+1}: [FAIL] {e}")
    else:
        fail_count += 1
        print(f"    Frame {i+1}: [FAIL] Could not read frame")

# Clean up temp file
try:
    import os
    os.remove("temp_frame.jpg")
except:
    pass

cap.release()

print()
print("=" * 60)
print("DIAGNOSTIC SUMMARY")
print("=" * 60)
print()
print(f"    Camera index    : {camera_index}")
print(f"    Frame shape     : {frame.shape}")
print(f"    Frame dtype     : {frame.dtype}")
print(f"    Success count   : {success_count}/5")
print(f"    Fail count      : {fail_count}/5")
print()

if success_count > 0:
    print("[RESULT] Face recognition CAN work with your camera!")
    print()
    print("The fix: Use 'save and reload' method for face detection.")
    print("I'll update your gui_app.py to use this method.")
else:
    print("[RESULT] There might be a compatibility issue.")
    print("Please share the full output above for further help.")

print()
print("=" * 60)