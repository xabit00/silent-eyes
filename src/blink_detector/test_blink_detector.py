"""
test_blink_detector.py - Test the Blink Detector
"""

import cv2
import sys
import os
import time

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blink_detector.blink_detector import BlinkDetector

# Initialize the blink detector
detector = BlinkDetector()

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    sys.exit()

print("="*60)
print("👁️ BLINK DETECTOR TEST")
print("="*60)
print("Instructions:")
print("  • Close your eyes for 0.5 seconds to trigger an intentional blink")
print("  • Press 'q' in the webcam window to quit")
print("  • Or press Ctrl+C in the terminal to quit")
print("="*60 + "\n")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Could not read frame.")
            break
        
        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Detect blinks
        result = detector.detect_blink(frame)
        
        # Draw debug info
        frame = detector.draw_debug_info(frame, result)
        
        # Display
        cv2.imshow('Blink Detector', frame)
        
        # Print to console if intentional blink detected
        if result['blink_detected'] and result['is_intentional']:
            print(f"✅ INTENTIONAL BLINK DETECTED! (Total: {result['total_blinks']})")
        
        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n👋 Quitting...")
            break

except KeyboardInterrupt:
    print("\n👋 Stopping via Ctrl+C...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    detector.release()
    print("✅ Done!")