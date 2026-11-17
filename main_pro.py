"""
main_pro.py - SILENT EYES + NEUROBLINK
FIXED: Speaks every time you press 'f'!
"""

import cv2
import time
import sys
import os
import pyttsx3
import signal
import numpy as np
import threading

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from eeg_processor.fake_eeg import FakeEEG

# ============================================
# GLOBALS
# ============================================
running = True
speaking = False
tts_lock = threading.Lock()

def signal_handler(sig, frame):
    global running
    print("\n\n👋 Shutting down...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

# ============================================
# INITIALIZE COMPONENTS
# ============================================
print("="*60)
print("  SILENT EYES + NEUROBLINK  ")
print("="*60)

# EEG
print("🔄 Initializing EEG...")
eeg = FakeEEG()
eeg.start_streaming()

# TTS - Create a NEW engine each time to avoid issues
print("🔄 Initializing Text-to-Speech...")
tts_engine = None
try:
    # Test if pyttsx3 works
    test_engine = pyttsx3.init()
    test_engine.setProperty('rate', 150)
    test_engine.setProperty('volume', 0.9)
    test_engine.say("Test")
    test_engine.runAndWait()
    test_engine.stop()
    tts_engine = test_engine
    print("✅ TTS Ready")
except Exception as e:
    print(f"⚠️ TTS initialization warning: {e}")
    tts_engine = None

# Webcam
print("🔄 Initializing Webcam...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("⚠️ No camera - continuing without video")
    cap = None

# Load face/eye detectors
if cap is not None:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    print("✅ Camera Ready")

# ============================================
# COMMANDS
# ============================================
COMMANDS = [
    "I am thirsty, please give me water.",
    "I am hungry, please give me food.",
    "I need help, please come here.",
    "Yes, that is correct.",
    "No, that is not correct."
]

selected = 0
last_spoken = ""
triggered = False
trigger_time = 0

# ============================================
# FIXED SPEAK FUNCTION - Creates NEW engine each time!
# ============================================
def speak_text(text):
    """Speak text - creates fresh engine each time for reliability"""
    global speaking
    
    with tts_lock:
        try:
            speaking = True
            print(f"🔊 {text}")
            
            # Create a FRESH engine every time
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            
            # Speak
            engine.say(text)
            engine.runAndWait()
            
            # Clean up
            engine.stop()
            
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
        finally:
            speaking = False

def speak(text):
    """Start speaking in a background thread."""
    thread = threading.Thread(target=speak_text, args=(text,))
    thread.daemon = True
    thread.start()

def stop_speaking_func():
    """Stop the current TTS immediately."""
    global speaking
    try:
        # Try to stop all engines
        import pyttsx3
        # Create a temporary engine to stop everything
        temp_engine = pyttsx3.init()
        temp_engine.stop()
        temp_engine = None
        speaking = False
        print("⏹️ Speaking stopped!")
    except Exception as e:
        print(f"⚠️ Stop error: {e}")
        speaking = False

# ============================================
# DRAW FUNCTIONS - Clean Professional UI
# ============================================
def draw_header(frame):
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 50), (30, 30, 30), -1)
    cv2.putText(frame, "SILENT EYES + NEUROBLINK", (20, 33),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
    cv2.line(frame, (0, 50), (frame.shape[1], 50), (60, 60, 60), 1)

def draw_focus_bar(frame, focus):
    x, y = 20, 75
    w, h = 250, 25
    cv2.rectangle(frame, (x, y), (x + w, y + h), (40, 40, 40), -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 60, 60), 1)
    fill = int(focus * w)
    color = (0, 200, 0) if focus > 0.3 else (200, 150, 0)
    cv2.rectangle(frame, (x, y), (x + fill, y + h), color, -1)
    cv2.putText(frame, f"FOCUS {int(focus*100)}%", (x + w + 15, y + 18),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    threshold_x = x + int(0.3 * w)
    cv2.line(frame, (threshold_x, y), (threshold_x, y + h), (255, 255, 0), 1)

def draw_command(frame, idx):
    x, y = 20, 125
    cv2.putText(frame, "COMMAND", (x, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    cv2.putText(frame, f"{idx+1}. {COMMANDS[idx]}", (x, y + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

def draw_controls(frame):
    x, y = 20, 185
    cv2.putText(frame, "CONTROLS", (x, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    controls = [
        ("1-5", "Select Command"),
        ("f", "SPEAK Command"),
        ("s", "STOP Speaking"),
        ("q", "Quit")
    ]
    for i, (key, action) in enumerate(controls):
        yy = y + 25 + (i * 25)
        cv2.putText(frame, key, (x, yy),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
        cv2.putText(frame, action, (x + 60, yy),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

def draw_status(frame):
    x, y = 20, 310
    cv2.rectangle(frame, (x, y), (x + 300, y + 60), (30, 30, 30), -1)
    cv2.rectangle(frame, (x, y), (x + 300, y + 60), (60, 60, 60), 1)
    if speaking:
        status = "🔊 SPEAKING..."
        color = (0, 200, 255)
    elif triggered:
        status = "✅ COMMAND SENT"
        color = (0, 255, 0)
    else:
        status = "⏸️ READY"
        color = (150, 150, 150)
    cv2.putText(frame, status, (x + 15, y + 38),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

def draw_eye_detection(frame, gray):
    if cap is None:
        return
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces[:1]:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 200, 255), 2)
        cv2.putText(frame, "FACE", (x, y-8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 255), 1)
        roi_gray = gray[y:y+h//2, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(20, 20))
        for (ex, ey, ew, eh) in eyes[:2]:
            cx = x + ex + ew//2
            cy = y + ey + eh//2
            r = int((ew + eh) / 4)
            cv2.circle(frame, (cx, cy), r, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 2, (0, 255, 0), -1)
            cv2.putText(frame, "EYE", (cx-r, cy-r-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)

def draw_bottom_bar(frame):
    h = frame.shape[0]
    cv2.rectangle(frame, (0, h-30), (frame.shape[1], h), (30, 30, 30), -1)
    cv2.line(frame, (0, h-30), (frame.shape[1], h-30), (60, 60, 60), 1)
    if last_spoken:
        text = f"Last: {last_spoken[:40]}..."
        cv2.putText(frame, text, (20, h-8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

def draw_big_prompt(frame):
    h = frame.shape[0]
    w = frame.shape[1]
    x, y = w - 220, h - 80
    cv2.rectangle(frame, (x, y), (w-20, h-40), (0, 180, 0), -1)
    cv2.rectangle(frame, (x, y), (w-20, h-40), (0, 255, 0), 2)
    cv2.putText(frame, "PRESS 'f'", (x+20, y+28),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "TO SPEAK", (x+20, y+50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 255, 200), 1)

def draw_stop_prompt(frame):
    if not speaking:
        return
    h = frame.shape[0]
    w = frame.shape[1]
    x, y = 20, h - 80
    cv2.rectangle(frame, (x, y), (x + 180, h-40), (180, 0, 0), -1)
    cv2.rectangle(frame, (x, y), (x + 180, h-40), (255, 0, 0), 2)
    cv2.putText(frame, "PRESS 's'", (x+20, y+28),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "TO STOP", (x+20, y+50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 200), 1)

# ============================================
# MAIN LOOP
# ============================================
print("\n" + "="*60)
print("  SYSTEM READY")
print("="*60)
print("  Press 1-5 : Select Command")
print("  Press f   : Speak Command (WORKS EVERY TIME!)")
print("  Press s   : STOP Speaking")
print("  Press q   : Quit")
print("="*60 + "\n")

try:
    while running:
        # Get EEG data
        _, focus = eeg.get_latest_sample()
        
        # Update trigger flag
        if triggered and time.time() - trigger_time > 1.5:
            triggered = False
        
        # Read webcam
        if cap is not None:
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                gray = np.zeros((480, 640), dtype=np.uint8)
                cv2.putText(frame, "CAMERA OFFLINE", (250, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            gray = np.zeros((480, 640), dtype=np.uint8)
            cv2.putText(frame, "CAMERA NOT CONNECTED", (220, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        
        # Draw UI
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (380, frame.shape[0]), (20, 20, 25), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        draw_header(frame)
        draw_focus_bar(frame, focus)
        draw_command(frame, selected)
        draw_controls(frame)
        draw_status(frame)
        draw_eye_detection(frame, gray)
        draw_bottom_bar(frame)
        draw_big_prompt(frame)
        draw_stop_prompt(frame)
        
        cv2.imshow('Silent Eyes + NeuroBlink', frame)
        
        # Keyboard handling
        key = cv2.waitKey(50) & 0xFF
        
        if key == ord('q') or key == ord('Q'):
            print("\n👋 Quitting...")
            running = False
            break
        
        elif key == ord('s') or key == ord('S'):
            stop_speaking_func()
        
        elif key == ord('f') or key == ord('F'):
            print("\n" + "="*60)
            print(f"  SPEAK: {COMMANDS[selected]}")
            print("="*60)
            
            # Speak the command
            speak(COMMANDS[selected])
            last_spoken = COMMANDS[selected]
            triggered = True
            trigger_time = time.time()
            eeg.trigger_focus()
            print("💡 Focus activated!")
        
        elif key == ord('1'):
            selected = 0
            print(f"\n📋 Command: {COMMANDS[0]}")
        elif key == ord('2'):
            selected = 1
            print(f"\n📋 Command: {COMMANDS[1]}")
        elif key == ord('3'):
            selected = 2
            print(f"\n📋 Command: {COMMANDS[2]}")
        elif key == ord('4'):
            selected = 3
            print(f"\n📋 Command: {COMMANDS[3]}")
        elif key == ord('5'):
            selected = 4
            print(f"\n📋 Command: {COMMANDS[4]}")

except KeyboardInterrupt:
    print("\n\n👋 Interrupted")

finally:
    running = False
    print("\n🧹 Cleaning up...")
    
    # Clean up TTS
    try:
        import pyttsx3
        temp_engine = pyttsx3.init()
        temp_engine.stop()
        temp_engine = None
    except:
        pass
    
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    eeg.stop_streaming()
    print("\n✅ System stopped.")