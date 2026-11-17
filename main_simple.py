"""
main_simple.py - SIMPLE VERSION - FINAL FIX!
Press 'f' to speak the selected command EVERY TIME - No delays!
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

# Import our modules
from eeg_processor.fake_eeg import FakeEEG

# ============================================
# GLOBAL FLAG FOR QUITTING
# ============================================
running = True
speaking = False  # Flag to track if TTS is speaking

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("\n\n👋 Ctrl+C detected! Shutting down...")
    running = False

# Register Ctrl+C handler
signal.signal(signal.SIGINT, signal_handler)

print("="*70)
print("🧠 SILENT EYES + NEUROBLINK - SIMPLE VERSION")
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
# 3. INITIALIZE WEBCAM (Just for display)
# ============================================
print("🔄 Initializing Webcam...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("⚠️ Webcam not available - continuing without video")
    cap = None
else:
    print("✅ Webcam ready!")

# ============================================
# 4. COMMANDS
# ============================================
commands = [
    "I am thirsty, please give me water.",
    "I am hungry, please give me food.",
    "I need help, please come here.",
    "Yes, that is correct.",
    "No, that is not correct."
]
selected_command_index = 0
last_focus_level = 0.0
last_command_spoken = ""
command_triggered = False
trigger_time = 0

print("\n" + "="*70)
print("🎯 SYSTEM READY!")
print("="*70)
print("HOW TO USE:")
print("  🔹 Press '1-5' to SELECT a command")
print("  🔹 Press 'f' to SPEAK the command (works EVERY TIME!)")
print("  🔹 Press 'q' or Ctrl+C to quit")
print("="*70)
print("\n📊 COMMANDS:")
for i, cmd in enumerate(commands, 1):
    print(f"  {i}. {cmd}")
print("\n" + "="*70)
print("\n💡 TIP: Press '2' then 'f' - works every single time!")
print("="*70 + "\n")

# ============================================
# 5. SPEAK FUNCTION (Non-blocking)
# ============================================
def speak_text_async(text):
    """Speak text in a separate thread so it doesn't block."""
    global speaking
    if tts_engine:
        try:
            speaking = True
            print(f"🔊 Speaking: {text}")
            tts_engine.say(text)
            tts_engine.runAndWait()
            speaking = False
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
            speaking = False
    else:
        print(f"🔊 (Would speak): {text}")

def speak_text(text):
    """Start speaking in a background thread."""
    thread = threading.Thread(target=speak_text_async, args=(text,))
    thread.daemon = True
    thread.start()

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
        
        # If command was triggered, show visual feedback
        if command_triggered:
            if time.time() - trigger_time > 2.0:  # Show for 2 seconds
                command_triggered = False
        
        # ------------------------------
        # B. READ WEBCAM (Just for display)
        # ------------------------------
        if cap is not None:
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
            else:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Camera unavailable", (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Camera not connected", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # ------------------------------
        # C. DISPLAY INFORMATION
        # ------------------------------
        # Title
        cv2.putText(frame, "SILENT EYES + NEUROBLINK", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Focus bar
        bar_x, bar_y = 10, 60
        bar_width = 300
        bar_height = 30
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        focus_bar_width = int(focus_level * bar_width)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + focus_bar_width, bar_y + bar_height), 
                     (0, 255, 0) if focus_level > 0.3 else (0, 150, 255), -1)
        cv2.putText(frame, f"Focus: {focus_level*100:.0f}%", (bar_x + bar_width + 10, bar_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Selected command
        selected_text = f"Selected: {selected_command_index+1}. {commands[selected_command_index]}"
        cv2.putText(frame, selected_text, (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Instructions
        cv2.putText(frame, "Press '1-5' to select command", (10, 170),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(frame, "Press 'f' to SPEAK the command", (10, 200),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 230),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Show current command in big text
        cv2.putText(frame, commands[selected_command_index], (10, 300),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # BIG GREEN "PRESS F" indicator - ALWAYS visible
        cv2.putText(frame, "PRESS 'f' TO SPEAK!", (10, 380),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)
        
        # Show when command was triggered
        if command_triggered:
            cv2.putText(frame, "✅ COMMAND TRIGGERED! Speaking...", (10, 420),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show speaking status
        if speaking:
            cv2.putText(frame, "🔊 SPEAKING...", (10, 450),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Last spoken command
        if last_command_spoken:
            cv2.putText(frame, f"Last: {last_command_spoken[:30]}...", (10, 480),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Show frame
        cv2.imshow('Silent Eyes + NeuroBlink - Simple', frame)
        
        # ------------------------------
        # D. HANDLE KEYBOARD INPUT - NON-BLOCKING!
        # ------------------------------
        key = cv2.waitKey(50) & 0xFF  # 50ms delay - very responsive!
        
        if key == ord('q') or key == ord('Q'):
            print("\n👋 Quitting...")
            running = False
            break
        
        elif key == ord('f') or key == ord('F'):
            # FINAL BOSS! Speak the command - ALWAYS works!
            print("\n" + "="*60)
            print("💡 'f' PRESSED! Speaking command...")
            print("="*60)
            
            # Speak in background thread
            speak_text(commands[selected_command_index])
            last_command_spoken = commands[selected_command_index]
            command_triggered = True
            trigger_time = time.time()
            
            # Trigger focus for visual effect
            eeg.trigger_focus()
            
            print("="*60 + "\n")
        
        elif key == ord('1'):
            selected_command_index = 0
            last_command_spoken = ""
            print(f"\n📋 Command selected: {commands[0]}")
        elif key == ord('2'):
            selected_command_index = 1
            last_command_spoken = ""
            print(f"\n📋 Command selected: {commands[1]}")
        elif key == ord('3'):
            selected_command_index = 2
            last_command_spoken = ""
            print(f"\n📋 Command selected: {commands[2]}")
        elif key == ord('4'):
            selected_command_index = 3
            last_command_spoken = ""
            print(f"\n📋 Command selected: {commands[3]}")
        elif key == ord('5'):
            selected_command_index = 4
            last_command_spoken = ""
            print(f"\n📋 Command selected: {commands[4]}")

except KeyboardInterrupt:
    print("\n\n👋 Ctrl+C detected! Shutting down...")

finally:
    # Cleanup
    running = False
    print("\n🧹 Cleaning up...")
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    eeg.stop_streaming()
    if tts_engine:
        tts_engine.stop()
    print("\n✅ System stopped successfully!")