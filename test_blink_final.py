"""
test_blink_final.py - SIMPLE BLINK DETECTOR
Uses ONLY OpenCV - No dlib, No MediaPipe issues!
"""

import cv2
import time
import numpy as np

print("="*60)
print("👁️ SIMPLE BLINK DETECTOR")
print("="*60)
print("Using OpenCV only - No complex libraries needed!")
print("")

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    exit()

print("✅ Webcam opened successfully!")
print("")
print("Instructions:")
print("  • Close your eyes for 0.5 seconds to detect an intentional blink")
print("  • Press 'q' to quit")
print("  • Press 'r' to reset counter")
print("="*60)
print("")

# Load eye cascade classifier
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Blink tracking variables
total_blinks = 0
is_closed = False
closed_start_time = None
blink_detected = False

# For smoothing
eye_detected_frames = 0
no_eye_frames = 0

while True:
    # Read frame
    ret, frame = cap.read()
    if not ret:
        print("❌ Error reading frame")
        break
    
    # Flip for mirror effect
    frame = cv2.flip(frame, 1)
    
    # Convert to grayscale for detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces first (to reduce false positives)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    eyes_found = False
    eye_positions = []
    
    # If we found a face, look for eyes within it
    if len(faces) > 0:
        for (x, y, w, h) in faces[:1]:  # Only first face
            # Draw face rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Look for eyes in the upper half of the face
            roi_gray = gray[y:y+h//2, x:x+w]
            roi_color = frame[y:y+h//2, x:x+w]
            
            # Detect eyes
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(20, 20))
            
            if len(eyes) >= 2:
                eyes_found = True
                # Draw circles around eyes
                for (ex, ey, ew, eh) in eyes:
                    center = (x + ex + ew//2, y + ey + eh//2)
                    radius = int((ew + eh) / 4)
                    cv2.circle(frame, center, radius, (0, 255, 0), 2)
                    eye_positions.append(center)
    
    # Simple blink detection logic
    if eyes_found:
        # Eyes are open
        if is_closed:
            # Check if it was a natural blink (short)
            if closed_start_time is not None:
                closed_duration = time.time() - closed_start_time
                if closed_duration < 0.5:
                    # Natural blink - ignore
                    pass
            is_closed = False
            closed_start_time = None
            blink_detected = False
        
        # Show status
        cv2.putText(frame, "👁️ EYES OPEN", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Show face count
        cv2.putText(frame, f"Face: {len(faces)} found", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    else:
        # No eyes detected - could be closed or not visible
        if len(faces) > 0:
            # We have a face but no eyes = eyes are closed
            if not is_closed:
                is_closed = True
                closed_start_time = time.time()
                # print("👁️ Eyes closed - timer started")
            else:
                # Check duration
                if closed_start_time is not None:
                    closed_duration = time.time() - closed_start_time
                    if closed_duration >= 0.5 and not blink_detected:
                        blink_detected = True
                        total_blinks += 1
                        print(f"✅ INTENTIONAL BLINK DETECTED! (Total: {total_blinks})")
                        # Reset to avoid multiple triggers
                        is_closed = False
                        closed_start_time = None
            
            # Show status
            cv2.putText(frame, "👁️ EYES CLOSED", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        else:
            # No face detected
            cv2.putText(frame, "😕 No face detected - please look at camera", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Display blink count
    cv2.putText(frame, f"Intentional Blinks: {total_blinks}", (10, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Show intentional blink message
    if blink_detected:
        cv2.putText(frame, "⚡ INTENTIONAL BLINK! ⚡", (10, 130),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
    
    # Simple visual indicator
    if is_closed and not blink_detected:
        # Show a timer bar for how long eyes have been closed
        if closed_start_time:
            elapsed = time.time() - closed_start_time
            bar_width = int(min(elapsed / 0.5, 1.0) * 200)
            cv2.rectangle(frame, (10, 160), (10 + bar_width, 180), (0, 0, 255), -1)
            cv2.putText(frame, f"Closed: {elapsed:.2f}s", (220, 175),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Instructions at bottom
    cv2.putText(frame, "Press 'q' to quit | Press 'r' to reset", (10, frame.shape[0] - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    # Show the frame
    cv2.imshow('Blink Detector - Simple Version', frame)
    
    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("\n👋 Quitting...")
        break
    elif key == ord('r'):
        total_blinks = 0
        blink_detected = False
        is_closed = False
        closed_start_time = None
        print("🔄 Counter reset!")

# Cleanup
cap.release()
cv2.destroyAllWindows()

print("="*60)
print(f"📊 FINAL RESULTS")
print(f"   Total intentional blinks: {total_blinks}")
print("="*60)
print("✅ Done!")