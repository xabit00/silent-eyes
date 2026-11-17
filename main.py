"""
main.py - Silent Eyes + NeuroBlink Fusion Engine (FIXED)
Better blink detection, slower focus decay, proper command execution
"""

import cv2
import time
import sys
import os
import threading
import pyttsx3
import numpy as np
import signal

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our modules
from eeg_processor.fake_eeg import FakeEEG

# ============================================
# GLOBAL FLAG FOR QUITTING
# ============================================
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("\n\n👋 Ctrl+C detected! Shutting down...")
    running = False

# Register Ctrl+C handler
signal.signal(signal.SIGINT, signal_handler)

print("="*70)
print("🧠 SILENT EYES + NEUROBLINK FUSION SYSTEM")
print("="*70)
print("Loading components...")

# ============================================
# 1. INITIALIZE EEG SIMULATOR
# ============================================
print("🔄 Initializing EEG Simulator...")
eeg = FakeEEG()
eeg.start_streaming()
print("✅ EEG Simulator ready!")

# ============================================
# 2. INITIALIZE TEXT-TO-SPEECH
# ============================================
print("🔄 Initializing Text-to-Speech...")
try:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
    tts_engine.setProperty('volume', 0.9)
    print("✅ Text-to-Speech ready!")
except Exception as e:
    print(f"⚠️ TTS error: {e}")
    tts_engine = None

# ============================================
# 3. INITIALIZE BLINK DETECTOR
# ============================================
print("🔄 Initializing Blink Detector...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    sys.exit()

# Load cascades
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
print("✅ Blink Detector ready!")

# ============================================
# 4. FUSION STATE VARIABLES
# ============================================
current_state = "idle"
last_focus_level = 0.0
command_executed = False

# Blink tracking - MORE RELIABLE
is_closed = False
closed_start_time = None
blink_detected = False
eye_closed_counter = 0  # Counter for smoothing

# Focus threshold - LOWER for easier triggering
FOCUS_THRESHOLD = 0.3  # 30% focus needed (was 50%)

# Commands
commands = [
    "I am thirsty, please give me water.",
    "I am hungry, please give me food.",
    "I need help, please come here.",
    "Yes, that is correct.",
    "No, that is not correct."
]
selected_command_index = 0

# For keyboard input in terminal
import msvcrt

def check_keyboard():
    """Check for keyboard input in a separate thread."""
    global running
    while running:
        try:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'q' or key == b'Q':
                    print("\n👋 'q' pressed in terminal! Shutting down...")
                    running = False
                    break
        except:
            pass
        time.sleep(0.1)

# Start keyboard listener thread
keyboard_thread = threading.Thread(target=check_keyboard, daemon=True)
keyboard_thread.start()

print("\n" + "="*70)
print("🎯 SYSTEM READY!")
print("="*70)
print("How to use:")
print("  1. Press 'f' to FOCUS (focus bar goes up)")
print("  2. Press '1-5' to select a command")
print("  3. CLOSE YOUR EYES for 1-2 seconds to CONFIRM")
print("  4. The system will SPEAK the command")
print("  5. Press 'q' or Ctrl+C to quit")
print("="*70)
print("\n📊 Commands:")
for i, cmd in enumerate(commands, 1):
    print(f"  {i}. {cmd}")
print("\n💡 TIP: Keep eyes closed for 1-2 seconds to trigger!")
print("="*70 + "\n")

# ============================================
# 5. SPEAK FUNCTION
# ============================================
def speak_text(text):
    """Speak text using TTS."""
    if tts_engine:
        try:
            print(f"🔊 Speaking: {text}")
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
    else:
        print(f"🔊 (Would speak): {text}")

# ============================================
# 6. MAIN LOOP
# ============================================
try:
    while running:
        # ------------------------------
        # A. READ EEG DATA
        # ------------------------------
        eeg_signal, focus_level = eeg.get_latest_sample()
        last_focus_level = focus_level
        
        # ------------------------------
        # B. READ WEBCAM (Blink Detection)
        # ------------------------------
        ret, frame = cap.read()
        if not ret:
            continue
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        eyes_found = False
        
        if len(faces) > 0:
            for (x, y, w, h) in faces[:1]:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                roi_gray = gray[y:y+h//2, x:x+w]
                eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(20, 20))
                if len(eyes) >= 2:
                    eyes_found = True
                    for (ex, ey, ew, eh) in eyes:
                        center = (x + ex + ew//2, y + ey + eh//2)
                        radius = int((ew + eh) / 4)
                        cv2.circle(frame, center, radius, (0, 255, 0), 2)
        
        # ------------------------------
        # C. BLINK DETECTION LOGIC (IMPROVED)
        # ------------------------------
        if eyes_found:
            # Eyes are OPEN
            if is_closed:
                # Eyes just opened - check if it was a long blink
                if closed_start_time is not None:
                    closed_duration = time.time() - closed_start_time
                    print(f"👁️ Eyes opened after {closed_duration:.2f}s")
                    
                    if closed_duration >= 1.0:  # 1 second threshold
                        # INTENTIONAL BLINK DETECTED!
                        print("✅ INTENTIONAL BLINK DETECTED!")
                        
                        if focus_level > FOCUS_THRESHOLD:
                            # Execute command
                            command = commands[selected_command_index]
                            print(f"⚡ FUSION TRIGGERED! (Focus: {focus_level*100:.0f}%)")
                            print(f"📣 Executing: {command}")
                            speak_text(command)
                            command_executed = True
                            current_state = "speaking"
                            time.sleep(0.5)
                        else:
                            print(f"⚠️ Low focus ({focus_level*100:.0f}%). Press 'f' to focus!")
                            # speak_text("Please focus more.")
                    else:
                        print(f"👁️ Natural blink ({closed_duration:.2f}s) - ignored")
                
                # Reset blink state
                is_closed = False
                closed_start_time = None
        else:
            # No eyes found - might be closed
            if len(faces) > 0:
                # Face detected but no eyes = eyes are CLOSED
                if not is_closed:
                    is_closed = True
                    closed_start_time = time.time()
                    print("👁️ Eyes closed - timer started!")
        
        # ------------------------------
        # D. DISPLAY INFORMATION
        # ------------------------------
        # EEG focus bar
        bar_x, bar_y = 10, 30
        bar_width = 300
        bar_height = 30
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        focus_bar_width = int(focus_level * bar_width)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + focus_bar_width, bar_y + bar_height), 
                     (0, 255, 0) if focus_level > FOCUS_THRESHOLD else (0, 150, 255), -1)
        cv2.putText(frame, f"Focus: {focus_level*100:.0f}%", (bar_x + bar_width + 10, bar_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Threshold line
        threshold_x = bar_x + int(FOCUS_THRESHOLD * bar_width)
        cv2.line(frame, (threshold_x, bar_y), (threshold_x, bar_y + bar_height), (0, 0, 255), 2)
        cv2.putText(frame, "THRESHOLD", (threshold_x - 30, bar_y + bar_height + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        
        # Selected command
        selected_text = f"Command {selected_command_index+1}: {commands[selected_command_index]}"
        cv2.putText(frame, selected_text, (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Eye status
        if is_closed:
            cv2.putText(frame, "👁️ EYES CLOSED - Hold for 1 second!", (10, 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if closed_start_time:
                elapsed = time.time() - closed_start_time
                # Show progress bar for blink
                progress = min(elapsed / 1.0, 1.0)
                cv2.rectangle(frame, (10, 160), (10 + int(progress * 200), 180), 
                             (0, 0, 255), -1)
                cv2.putText(frame, f"{elapsed:.1f}s / 1.0s", (220, 175),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                if progress >= 1.0:
                    cv2.putText(frame, "✅ READY TO TRIGGER!", (10, 205),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "👁️ EYES OPEN", (10, 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Status
        status_colors = {
            "idle": (255, 255, 255),
            "focusing": (0, 255, 255),
            "blink_detected": (0, 255, 0),
            "speaking": (0, 0, 255)
        }
        status_color = status_colors.get(current_state, (255, 255, 255))
        cv2.putText(frame, f"Status: {current_state.upper()}", (10, 235),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Show last command executed
        if command_executed:
            cv2.putText(frame, "✅ COMMAND EXECUTED!", (10, 265),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Instructions
        cv2.putText(frame, "F=focus | 1-5=cmd | CLOSE EYES=confirm | q=quit", (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Show frame
        cv2.imshow('Silent Eyes + NeuroBlink Fusion', frame)
        
        # ------------------------------
        # E. HANDLE KEYBOARD INPUT
        # ------------------------------
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == ord('Q'):
            print("\n👋 'q' pressed! Shutting down...")
            running = False
            break
        
        elif key == ord('f') or key == ord('F'):
            eeg.trigger_focus()
            current_state = "focusing"
            command_executed = False
            print("💡 FOCUS TRIGGERED! Focus level increased.")
        
        elif key == ord('1'):
            selected_command_index = 0
            command_executed = False
            print(f"📋 Selected: {commands[0]}")
        elif key == ord('2'):
            selected_command_index = 1
            command_executed = False
            print(f"📋 Selected: {commands[1]}")
        elif key == ord('3'):
            selected_command_index = 2
            command_executed = False
            print(f"📋 Selected: {commands[2]}")
        elif key == ord('4'):
            selected_command_index = 3
            command_executed = False
            print(f"📋 Selected: {commands[3]}")
        elif key == ord('5'):
            selected_command_index = 4
            command_executed = False
            print(f"📋 Selected: {commands[4]}")
        
        # Reset command executed flag after a moment
        if command_executed and current_state == "speaking":
            time.sleep(1)
            command_executed = False
            current_state = "idle"

except KeyboardInterrupt:
    print("\n\n👋 Ctrl+C detected! Shutting down...")

finally:
    # Cleanup
    running = False
    print("\n🧹 Cleaning up...")
    cap.release()
    cv2.destroyAllWindows()
    eeg.stop_streaming()
    if tts_engine:
        tts_engine.stop()
    print("\n✅ System stopped successfully!")
    print(f"📊 Final focus level: {last_focus_level*100:.0f}%")