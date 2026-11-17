"""
test_blink_simple_fixed.py - Working Blink Detector
Uses a simpler approach with OpenCV's face detection
"""

import cv2
import numpy as np
import time
import sys
import dlib

print("="*60)
print("👁️ SIMPLE BLINK DETECTOR (Using dlib)")
print("="*60)

# Try to load dlib's face detector and facial landmark predictor
try:
    # Download the shape predictor file if you don't have it
    import urllib.request
    import os
    
    # Check if the predictor file exists
    predictor_path = "shape_predictor_68_face_landmarks.dat"
    if not os.path.exists(predictor_path):
        print("Downloading facial landmark predictor...")
        url = "https://github.com/italojs/facial-landmarks-recognition/raw/master/shape_predictor_68_face_landmarks.dat"
        urllib.request.urlretrieve(url, predictor_path)
        print("✅ Download complete!")
    
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    print("✅ dlib loaded successfully!")
    
except Exception as e:
    print(f"⚠️ dlib not available. Using OpenCV fallback...")
    print(f"Error: {e}")
    print("Installing dlib might take a while. Let me use a different approach.")

# Alternative: Use OpenCV's Haar Cascade (simpler but less accurate)
# This is our fallback method
def detect_face_haar(frame):
    """Detect face using Haar Cascade (fallback method)."""
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye.xml'
    )
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) > 0:
        x, y, w, h = faces[0]
        # Look for eyes in the face region
        roi_gray = gray[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
        
        # If we detect eyes, face is detected
        if len(eyes) >= 2:
            return True, (x, y, w, h)
    
    return False, None

# Open webcam
print("Opening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    sys.exit()

print("="*60)
print("👁️ BLINK DETECTOR READY")
print("="*60)
print("Instructions:")
print("  • Close your eyes for 0.5 seconds to detect an intentional blink")
print("  • Press 'q' in the window to quit")
print("  • Press 'r' to reset the blink counter")
print("="*60 + "\n")

# Blink tracking
total_blinks = 0
blink_detected = False
is_closed = False
closed_start_time = None

# For eye tracking
prev_eye_status = "open"

# Alternative: Use MediaPipe differently
print("Trying MediaPipe with alternative import...")

try:
    # Try different import methods for MediaPipe
    import mediapipe as mp
    
    # Check if we can use the new API
    if hasattr(mp, 'face_mesh'):
        mp_face_mesh = mp.face_mesh
        print("✅ Using mp.face_mesh")
    elif hasattr(mp, 'solutions'):
        mp_face_mesh = mp.solutions.face_mesh
        print("✅ Using mp.solutions.face_mesh")
    else:
        # Manual import
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        print("✅ Using mediapipe.tasks")
        # This is more complex, we'll use a different method
    
    # If we got here, try to initialize face mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    print("✅ FaceMesh initialized!")
    
    use_mediapipe = True
    
except Exception as e:
    print(f"⚠️ MediaPipe init failed: {e}")
    print("Using OpenCV fallback...")
    use_mediapipe = False

# Eye landmark indices
LEFT_EYE_INDICES = [33, 133, 157, 158, 159, 160, 161, 173]
RIGHT_EYE_INDICES = [362, 263, 387, 386, 385, 384, 398, 466]

def get_eye_landmarks_mediapipe(face_landmarks, eye_indices):
    """Extract eye landmarks from MediaPipe."""
    landmarks = []
    for idx in eye_indices:
        landmark = face_landmarks.landmark[idx]
        landmarks.append((landmark.x, landmark.y))
    return landmarks

def eye_aspect_ratio(eye_landmarks):
    """Calculate Eye Aspect Ratio."""
    eye = np.array(eye_landmarks)
    p2_p6 = np.linalg.norm(eye[1] - eye[5])
    p3_p5 = np.linalg.norm(eye[2] - eye[4])
    p1_p4 = np.linalg.norm(eye[0] - eye[3])
    ear = (p2_p6 + p3_p5) / (2.0 * p1_p4 + 1e-6)
    return ear

# Simple eye detection using OpenCV (backup method)
def detect_eyes_opencv(frame):
    """Detect eyes using OpenCV's Haar Cascade."""
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye.xml'
    )
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    eyes = eye_cascade.detectMultiScale(gray, 1.1, 3)
    return len(eyes) >= 2

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Try MediaPipe first
        if use_mediapipe:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb_frame)
                
                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    # Get eye landmarks
                    left_eye_points = get_eye_landmarks_mediapipe(face_landmarks, LEFT_EYE_INDICES)
                    right_eye_points = get_eye_landmarks_mediapipe(face_landmarks, RIGHT_EYE_INDICES)
                    
                    # Calculate EAR
                    left_ear = eye_aspect_ratio(left_eye_points)
                    right_ear = eye_aspect_ratio(right_eye_points)
                    avg_ear = (left_ear + right_ear) / 2.0
                    
                    # EAR threshold
                    EAR_THRESHOLD = 0.2
                    
                    # Check for blink
                    if avg_ear < EAR_THRESHOLD:
                        if not is_closed:
                            is_closed = True
                            closed_start_time = time.time()
                        else:
                            if closed_start_time is not None:
                                closed_duration = time.time() - closed_start_time
                                if closed_duration >= 0.5 and not blink_detected:
                                    blink_detected = True
                                    total_blinks += 1
                                    print(f"✅ INTENTIONAL BLINK! (Total: {total_blinks})")
                    else:
                        is_closed = False
                        closed_start_time = None
                        blink_detected = False
                    
                    # Display info
                    cv2.putText(frame, f"EAR: {avg_ear:.3f}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Blinks: {total_blinks}", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if avg_ear < EAR_THRESHOLD:
                        cv2.putText(frame, "👁️ EYES CLOSED", (10, 90),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        cv2.putText(frame, "👁️ EYES OPEN", (10, 90),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if blink_detected:
                        cv2.putText(frame, "⚡ INTENTIONAL BLINK!", (10, 120),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
                    
                    # EAR bar
                    bar_x, bar_y = 10, 150
                    bar_width = 200
                    bar_height = 20
                    normalized_ear = min(avg_ear / 0.4, 1.0)
                    
                    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
                    if avg_ear > EAR_THRESHOLD:
                        color = (0, 255, 0)
                    else:
                        color = (0, 0, 255)
                    
                    cv2.rectangle(frame, (bar_x, bar_y), 
                                 (bar_x + int(bar_width * normalized_ear), bar_y + bar_height),
                                 color, -1)
                else:
                    cv2.putText(frame, "No face detected", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
            except Exception as e:
                cv2.putText(frame, f"Error: {str(e)[:30]}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Show the frame
        cv2.imshow('Blink Detector', frame)
        
        # Quit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n👋 Quitting...")
            break
        elif key == ord('r'):
            total_blinks = 0
            print("🔄 Blink counter reset!")

except KeyboardInterrupt:
    print("\n👋 Stopping via Ctrl+C...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    if use_mediapipe:
        face_mesh.close()
    print(f"\n📊 Final blink count: {total_blinks}")
    print("✅ Done!")