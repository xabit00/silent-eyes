"""
test_blink_simple.py - Standalone Blink Test
Updated for newer MediaPipe versions
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import sys

print("="*60)
print("👁️ STANDALONE BLINK DETECTOR")
print("="*60)
print("Loading MediaPipe...")

# MediaPipe Face Mesh - Updated import
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Eye landmark indices (MediaPipe Face Mesh)
# Left eye: 33, 133, 157, 158, 159, 160, 161, 173
# Right eye: 362, 263, 387, 386, 385, 384, 398, 466
LEFT_EYE_INDICES = [33, 133, 157, 158, 159, 160, 161, 173]
RIGHT_EYE_INDICES = [362, 263, 387, 386, 385, 384, 398, 466]

# EAR threshold
EAR_THRESHOLD = 0.2
INTENTIONAL_BLINK_DURATION = 0.5

def eye_aspect_ratio(eye_landmarks):
    """Calculate Eye Aspect Ratio."""
    eye = np.array(eye_landmarks)
    p2_p6 = np.linalg.norm(eye[1] - eye[5])
    p3_p5 = np.linalg.norm(eye[2] - eye[4])
    p1_p4 = np.linalg.norm(eye[0] - eye[3])
    ear = (p2_p6 + p3_p5) / (2.0 * p1_p4 + 1e-6)
    return ear

def get_eye_landmarks(face_landmarks, eye_indices):
    """Extract eye landmarks."""
    landmarks = []
    for idx in eye_indices:
        landmark = face_landmarks.landmark[idx]
        landmarks.append((landmark.x, landmark.y))
    return landmarks

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
print("  • Or press Ctrl+C in the terminal to quit")
print("="*60 + "\n")

# Blink tracking
is_closed = False
closed_start_time = None
total_blinks = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Could not read frame.")
            break
        
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect face
        results = face_mesh.process(rgb_frame)
        
        # Default values
        left_ear = 0.0
        right_ear = 0.0
        avg_ear = 0.0
        blink_detected = False
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Get eye landmarks
            left_eye_points = get_eye_landmarks(face_landmarks, LEFT_EYE_INDICES)
            right_eye_points = get_eye_landmarks(face_landmarks, RIGHT_EYE_INDICES)
            
            # Calculate EAR
            left_ear = eye_aspect_ratio(left_eye_points)
            right_ear = eye_aspect_ratio(right_eye_points)
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Check for blink
            if avg_ear < EAR_THRESHOLD:
                # Eye is closed
                if not is_closed:
                    is_closed = True
                    closed_start_time = time.time()
                else:
                    # Check how long it's been closed
                    if closed_start_time is not None:
                        closed_duration = time.time() - closed_start_time
                        if closed_duration >= INTENTIONAL_BLINK_DURATION and not blink_detected:
                            blink_detected = True
                            total_blinks += 1
                            print(f"✅ INTENTIONAL BLINK DETECTED! (Duration: {closed_duration:.2f}s, Total: {total_blinks})")
                            # Reset to avoid multiple triggers
                            is_closed = False
                            closed_start_time = None
            else:
                # Eye is open
                if is_closed:
                    is_closed = False
                    closed_start_time = None
        
        # Draw info on frame
        # EAR value
        cv2.putText(frame, f"EAR: {avg_ear:.3f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Blink count
        cv2.putText(frame, f"Blinks: {total_blinks}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Eye status
        if avg_ear < EAR_THRESHOLD:
            cv2.putText(frame, "👁️ EYES CLOSED", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "👁️ EYES OPEN", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Intentional blink message
        if blink_detected:
            cv2.putText(frame, "⚡ INTENTIONAL BLINK!", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
        
        # EAR bar
        bar_x, bar_y = 10, 150
        bar_width = 200
        bar_height = 20
        normalized_ear = min(avg_ear / 0.4, 1.0)
        
        # Background bar
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
        
        # Fill bar
        if avg_ear > EAR_THRESHOLD:
            color = (0, 255, 0)  # Green = open
        else:
            color = (0, 0, 255)  # Red = closed
        
        cv2.rectangle(frame, (bar_x, bar_y), 
                     (bar_x + int(bar_width * normalized_ear), bar_y + bar_height),
                     color, -1)
        
        # Threshold line
        threshold_x = bar_x + int(bar_width * (EAR_THRESHOLD / 0.4))
        cv2.line(frame, (threshold_x, bar_y), (threshold_x, bar_y + bar_height), (255, 255, 0), 2)
        
        # Show the frame
        cv2.imshow('Blink Detector', frame)
        
        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n👋 Quitting...")
            break

except KeyboardInterrupt:
    print("\n👋 Stopping via Ctrl+C...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    print(f"\n📊 Final blink count: {total_blinks}")
    print("✅ Done!")