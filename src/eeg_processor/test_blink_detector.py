"""
test_blink_detector.py - Test the Blink Detector
"""

import cv2
import sys
import os
import threading
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
    exit()

print("="*60)
print("👁️ BLINK DETECTOR TEST")
print("="*60)
print("Instructions:")
print("  • Look at the webcam window")
print("  • Close your eyes for 0.5 seconds to trigger an intentional blink")
print("  • Press 'q' in the webcam window to quit")
print("  • Or press Ctrl+C in the terminal to quit")
print("="*60 + "\n")

# Flag to control the loop
running = True

def keyboard_listener():
    """Listen for 'q' key press in the terminal."""
    global running
    while running:
        try:
            # Check if 'q' is pressed (works in terminal)
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'q' or key == b'Q':
                    print("\n👋 Quitting via 'q' key...")
                    running = False
                    break
        except:
            pass
        time.sleep(0.1)

# Start keyboard listener thread
key_thread = threading.Thread(target=keyboard_listener, daemon=True)
key_thread.start()

# Main loop
try:
    while running:
        # Read frame
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Error: Could not read frame.")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Detect blinks
        result = detector.detect_blink(frame)
        
        # Draw debug info
        frame = detector.draw_debug_info(frame, result)
        
        # Display the frame
        cv2.imshow('Blink Detector', frame)
        
        # Show result in console if intentional blink detected
        if result['blink_detected'] and result['is_intentional']:
            print(f"✅ INTENTIONAL BLINK DETECTED! (Total: {result['total_blinks']})")
        
        # Check for 'q' key in OpenCV window
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("\n👋 Quitting via 'q' key in window...")
            running = False
            break
        
        # Small delay to prevent CPU overuse
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n👋 Stopping via Ctrl+C...")

finally:
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    detector.release()
    running = False
    print("✅ Done! Cleaned up successfully.")