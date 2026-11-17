"""
main_final.py - SILENT EYES + NEUROBLINK
FINAL MERGED VERSION:
- Keeps your battery bar fix (correct fill math)
- Keeps your tightened face cascade (1.1, 4, minSize 60x60)
- Keeps your COMMANDS label gap fix
- Fixed "cyan" to TRUE cyan in BGR -> (255,255,0), was (255,200,0)
- Removed ALL emoji from cv2.putText() (kept in print() - terminal is fine)
- Bumped to 1280x720 so panels never overlap each other or the camera view
- Face/eye detection restricted to a safe zone between the two side panels
- Eye markers are thin outlines, not filled circles
- Background thread for TTS so camera never freezes
"""

import cv2
import time
import sys
import os
import signal
import numpy as np
import threading
import win32com.client
import math

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from eeg_processor.fake_eeg import FakeEEG

# ============================================
# GLOBALS
# ============================================
running = True
speaking = False
voice_thread = None
start_time = time.time()

def signal_handler(sig, frame):
    global running
    print("\n\n[!] Shutting down...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

# ============================================
# INITIALIZE COMPONENTS
# ============================================
print("="*60)
print("  SILENT EYES + NEUROBLINK  ")
print("="*60)

print("[*] Initializing EEG...")
eeg = FakeEEG()
eeg.start_streaming()
print("[OK] EEG Ready")

print("[*] Initializing Windows SAPI Voice...")
try:
    test_sapi = win32com.client.Dispatch("SAPI.SpVoice")
    test_sapi.Speak("Ready")
    test_sapi = None
    print("[OK] Windows SAPI Voice Ready!")
except Exception as e:
    print(f"[WARN] SAPI error: {e}")
    print("[ERROR] Please install: pip install pywin32")
    sys.exit(1)

print("[*] Initializing Webcam...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[WARN] No camera - continuing without video")
    cap = None

if cap is not None:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    print("[OK] Camera Ready")

# ============================================
# LAYOUT CONSTANTS
# ============================================
FRAME_W = 1280
FRAME_H = 720

SIDEBAR_W = 400
PANEL_W = 260
PANEL_X = FRAME_W - PANEL_W

CAM_SAFE_X_START = SIDEBAR_W + 20
CAM_SAFE_X_END = PANEL_X - 20

SIDEBAR_COLOR = (22, 22, 28)
CYAN = (255, 255, 0)   # TRUE cyan in BGR (B=255, G=255, R=0)

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

is_closed = False
closed_start_time = None

# ============================================
# SPEAK FUNCTIONS (background thread)
# ============================================

def speak_worker(text):
    global speaking
    try:
        speaking = True
        print(f"[SPEAK] {text}")
        sapi = win32com.client.Dispatch("SAPI.SpVoice")
        sapi.Speak(text)
        sapi = None
    except Exception as e:
        print(f"[WARN] Voice error: {e}")
    finally:
        speaking = False
        print("[OK] Speaking finished")

def speak_text(text):
    global speaking, voice_thread
    if speaking:
        print("[..] Already speaking...")
        return
    voice_thread = threading.Thread(target=speak_worker, args=(text,))
    voice_thread.daemon = True
    voice_thread.start()

def stop_speaking_func():
    global speaking
    speaking = False
    print("[STOP] Speaking stopped!")

# ============================================
# DRAW HELPERS
# ============================================

def draw_text_background(frame, text, x, y, font_scale, color, thickness=1, padding=5):
    (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    cv2.rectangle(frame, (x - padding, y - text_h - padding),
                  (x + text_w + padding, y + padding), (15, 15, 15), -1)
    cv2.rectangle(frame, (x - padding, y - text_h - padding),
                  (x + text_w + padding, y + padding), (55, 55, 55), 1)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

# ============================================
# LEFT SIDEBAR
# ============================================

def draw_header(frame):
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 50), (30, 30, 30), -1)
    cv2.putText(frame, "SILENT EYES + NEUROBLINK", (20, 33),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
    cv2.line(frame, (0, 50), (frame.shape[1], 50), (60, 60, 60), 1)

def draw_focus_bar(frame, focus):
    x, y = 20, 75
    w, h = 320, 25

    cv2.rectangle(frame, (x, y), (x + w, y + h), (40, 40, 40), -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 60, 60), 1)

    if focus < 0.1:
        scan_pos = int((time.time() * 60) % w)
        cv2.line(frame, (x + scan_pos, y), (x + scan_pos, y + h), (90, 90, 90), 2)

    fill = int(focus * w)
    color = (0, 200, 0) if focus > 0.3 else (200, 150, 0)
    cv2.rectangle(frame, (x, y), (x + fill, y + h), color, -1)
    cv2.rectangle(frame, (x, y), (x + fill, y + h // 2), (255, 255, 255), -1)

    pulse_color = (0, int(120 + 100 * abs(math.sin(time.time() * 3))), 0)
    cv2.circle(frame, (x + 8, y + h + 14), 4, pulse_color, -1)
    label = "LIVE" if focus > 0.1 else "SCANNING"
    cv2.putText(frame, f"{label}  FOCUS {int(focus*100)}%", (x + 20, y + h + 19),
               cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    threshold_x = x + int(0.3 * w)
    cv2.line(frame, (threshold_x, y), (threshold_x, y + h), (255, 255, 0), 1)
    cv2.putText(frame, "THR", (threshold_x - 12, y - 6),
               cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)

# Vertical layout computed in order so nothing can collide
COMMANDS_TOP = 130
COMMAND_ROW_H = 26
COMMANDS_BOTTOM = COMMANDS_TOP + 25 + len(COMMANDS) * COMMAND_ROW_H
CONTROLS_TOP = COMMANDS_BOTTOM + 25
CONTROLS_BOTTOM = CONTROLS_TOP + 25 + 4 * COMMAND_ROW_H
STATUS_TOP = CONTROLS_BOTTOM + 20

def draw_command(frame, idx):
    x, y = 20, COMMANDS_TOP
    cv2.putText(frame, "COMMANDS", (x, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    for i, cmd in enumerate(COMMANDS):
        yy = y + 25 + (i * COMMAND_ROW_H)
        display_text = f"{i+1}. {cmd[:42]}"
        if i == idx:
            draw_text_background(frame, "> " + display_text, x, yy, 0.42, (0, 255, 255), 1)
        else:
            draw_text_background(frame, "  " + display_text, x, yy, 0.38, (110, 110, 110), 1)

def draw_controls(frame):
    x, y = 20, CONTROLS_TOP
    cv2.putText(frame, "CONTROLS", (x, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    controls = [
        ("1-5", "Select Command"),
        ("f", "SPEAK Command"),
        ("s", "STOP Speaking"),
        ("q", "Quit")
    ]
    for i, (key, action) in enumerate(controls):
        yy = y + 25 + (i * COMMAND_ROW_H)
        cv2.putText(frame, key, (x, yy),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)
        cv2.putText(frame, action, (x + 55, yy),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

def draw_status(frame):
    x, y = 20, STATUS_TOP
    box_w, box_h = SIDEBAR_W - 40, 65
    cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (30, 30, 30), -1)
    cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (60, 60, 60), 1)

    if speaking:
        status, color = "SPEAKING...", (0, 200, 255)
        sub_status, sub_color = "Voice output active", (150, 200, 255)
    elif triggered:
        status, color = "COMMAND SENT", (0, 255, 0)
        sub_status, sub_color = "Waiting for next command", (150, 255, 150)
    else:
        status, color = "LISTENING...", (0, 200, 100)
        sub_status, sub_color = "Press 'f' or select 1-5", (150, 150, 150)

    cv2.putText(frame, status, (x + 15, y + 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, sub_status, (x + 15, y + 52),
               cv2.FONT_HERSHEY_SIMPLEX, 0.42, sub_color, 1)

def draw_bottom_bar(frame):
    h = frame.shape[0]
    cv2.rectangle(frame, (0, h - 30), (frame.shape[1], h), (30, 30, 30), -1)
    cv2.line(frame, (0, h - 30), (frame.shape[1], h - 30), (60, 60, 60), 1)
    if last_spoken:
        text = f"Last: {last_spoken[:55]}"
        cv2.putText(frame, text, (20, h - 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 150), 1)

def draw_big_prompt(frame):
    h, w = frame.shape[0], frame.shape[1]
    bx, by = w - 240, h - 90
    bw, bh = 220, 50

    pulse = 0.7 + 0.3 * abs(math.sin(time.time() * 2.5))
    intensity = int(180 * pulse)

    if speaking:
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 120, 220), -1)
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 200, 255), 2)
        cv2.putText(frame, "SPEAKING", (bx + 30, by + 28),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "PRESS 's' TO STOP", (bx + 18, by + 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 240, 255), 1)
    else:
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, intensity, 0), -1)
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
        cv2.putText(frame, "PRESS 'f'", (bx + 35, by + 28),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "TO SPEAK", (bx + 40, by + 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 255, 200), 1)

# ============================================
# RIGHT STATUS PANEL (battery fill math kept from your fix)
# ============================================

def draw_status_panel(frame, focus, elapsed_time):
    x, y = PANEL_X, 50
    w_panel, h_panel = PANEL_W, 230

    cv2.rectangle(frame, (x, y), (x + w_panel, y + h_panel), SIDEBAR_COLOR, -1)
    cv2.rectangle(frame, (x, y), (x + w_panel, y + h_panel), (55, 55, 65), 1)

    cv2.putText(frame, "STATUS", (x + 15, y + 28),
               cv2.FONT_HERSHEY_SIMPLEX, 0.55, (210, 210, 210), 1)
    cv2.line(frame, (x + 15, y + 35), (x + w_panel - 15, y + 35), (60, 60, 60), 1)

    row = y + 60
    battery_level = 85
    cv2.putText(frame, f"Battery: {battery_level}%", (x + 15, row),
               cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 255, 150), 1)
    bar_x, bar_w = x + 15, 80
    cv2.rectangle(frame, (bar_x, row + 8), (bar_x + bar_w, row + 14), (35, 35, 35), -1)
    fill_width = int(bar_w * (battery_level / 100))   # correct proportional fill
    cv2.rectangle(frame, (bar_x, row + 8), (bar_x + fill_width, row + 14), (0, 200, 0), -1)

    row += 38
    if focus > 0.3:
        cal_status, cal_color = "CALIBRATED", (0, 255, 0)
    else:
        cal_status, cal_color = "CALIBRATING...", (255, 200, 0)
    cv2.putText(frame, cal_status, (x + 15, row),
               cv2.FONT_HERSHEY_SIMPLEX, 0.42, cal_color, 1)

    row += 28
    cv2.putText(frame, f"Focus: {int(focus*100)}%", (x + 15, row),
               cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)

    row += 28
    if last_spoken:
        display_cmd = last_spoken[:24] + "..." if len(last_spoken) > 24 else last_spoken
        cv2.putText(frame, f"Last: {display_cmd}", (x + 15, row),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 150), 1)

    row += 28
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    cv2.putText(frame, f"Uptime: {minutes:02d}:{seconds:02d}", (x + 15, row),
               cv2.FONT_HERSHEY_SIMPLEX, 0.38, (160, 160, 160), 1)

    row += 28
    if cap is not None:
        cv2.putText(frame, "Eye Tracking: ACTIVE", (x + 15, row),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 255, 100), 1)
    else:
        cv2.putText(frame, "Eye Tracking: OFF", (x + 15, row),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 100, 100), 1)

# ============================================
# FACE / EYE DETECTION (tightened params kept, safe-zone restricted, true cyan)
# ============================================

def draw_eye_detection(frame, gray):
    if cap is None:
        return None

    safe_gray = gray[:, CAM_SAFE_X_START:CAM_SAFE_X_END]
    # Tightened detection kept from your fix: 1.1 scaleFactor, 4 minNeighbors, 60x60 minSize
    faces = face_cascade.detectMultiScale(safe_gray, 1.1, 4, minSize=(60, 60))

    eyes_found = False
    for (fx, fy, fw, fh) in faces[:1]:
        x = fx + CAM_SAFE_X_START
        y = fy

        cv2.rectangle(frame, (x, y), (x + fw, y + fh), CYAN, 2)
        cv2.putText(frame, "FACE", (x, y - 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, CYAN, 1)

        roi_gray = gray[y:y + fh // 2, x:x + fw]
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(15, 15))
        if len(eyes) >= 2:
            eyes_found = True

        for (ex, ey, ew, eh) in eyes[:2]:
            cx = x + ex + ew // 2
            cy = y + ey + eh // 2
            r = int((ew + eh) / 4)
            cv2.circle(frame, (cx, cy), r, CYAN, 2)
            cv2.circle(frame, (cx, cy), 2, CYAN, -1)
            cv2.putText(frame, "EYE", (cx - r, cy - r - 6),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, CYAN, 1)

    return eyes_found, len(faces) > 0

def draw_countdown_ring(frame, center_x, center_y, radius, progress, color=(0, 255, 0)):
    cv2.circle(frame, (center_x, center_y), radius, (50, 50, 50), -1)
    cv2.circle(frame, (center_x, center_y), radius, (80, 80, 80), 1)
    if progress > 0:
        start_angle = -90
        end_angle = start_angle + (360 * progress)
        cv2.ellipse(frame, (center_x, center_y), (radius, radius), 0,
                    start_angle, end_angle, color, 3)
        percent = int(progress * 100)
        cv2.putText(frame, f"{percent}%", (center_x - 20, center_y + 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

# ============================================
# MAIN LOOP
# ============================================
print("\n" + "="*60)
print("  SYSTEM READY!")
print("="*60)
print("  Press 1-5 : Select Command")
print("  Press f   : SPEAK (Camera keeps running!)")
print("  Press s   : STOP Speaking")
print("  Press q   : Quit")
print("="*60 + "\n")

try:
    while running:
        _, focus = eeg.get_latest_sample()
        elapsed_time = time.time() - start_time

        if triggered and time.time() - trigger_time > 1.5:
            triggered = False

        if cap is not None:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (FRAME_W, FRAME_H))
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
                gray = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)
                cv2.putText(frame, "CAMERA OFFLINE", (FRAME_W//2 - 120, FRAME_H//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        else:
            frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
            gray = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)
            cv2.putText(frame, "CAMERA NOT CONNECTED", (FRAME_W//2 - 150, FRAME_H//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (SIDEBAR_W, frame.shape[0]), SIDEBAR_COLOR, -1)
        frame = cv2.addWeighted(frame, 0.65, overlay, 0.35, 0)

        draw_header(frame)
        draw_focus_bar(frame, focus)
        draw_command(frame, selected)
        draw_controls(frame)
        draw_status(frame)

        detection = draw_eye_detection(frame, gray)
        eyes_found, face_found = detection if detection else (False, False)

        draw_status_panel(frame, focus, elapsed_time)
        draw_bottom_bar(frame)
        draw_big_prompt(frame)

        if cap is not None and face_found:
            if eyes_found:
                if is_closed:
                    is_closed = False
                    closed_start_time = None
            else:
                if not is_closed:
                    is_closed = True
                    closed_start_time = time.time()

        if is_closed and closed_start_time is not None:
            elapsed = time.time() - closed_start_time
            progress = min(elapsed / 1.0, 1.0)
            ring_x, ring_y = PANEL_X - 60, 120
            draw_countdown_ring(frame, ring_x, ring_y, 30, progress,
                              (0, 255, 0) if progress >= 1 else (0, 200, 255))
            if progress >= 1:
                cv2.putText(frame, "BLINK CONFIRMED!", (ring_x - 140, ring_y + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                cv2.putText(frame, f"Hold blink: {int((1-progress)*100)}%", (ring_x - 140, ring_y + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        cv2.imshow('Silent Eyes + NeuroBlink', frame)

        key = cv2.waitKey(50) & 0xFF

        if key == ord('q') or key == ord('Q'):
            print("\n[!] Quitting...")
            running = False
            break
        elif key == ord('s') or key == ord('S'):
            stop_speaking_func()
        elif key == ord('f') or key == ord('F'):
            print("\n" + "="*60)
            print(f"  SPEAK: {COMMANDS[selected]}")
            print("="*60)
            speak_text(COMMANDS[selected])
            last_spoken = COMMANDS[selected]
            triggered = True
            trigger_time = time.time()
            eeg.trigger_focus()
        elif key == ord('1'):
            selected = 0
            print(f"\n[CMD] {COMMANDS[0]}")
        elif key == ord('2'):
            selected = 1
            print(f"\n[CMD] {COMMANDS[1]}")
        elif key == ord('3'):
            selected = 2
            print(f"\n[CMD] {COMMANDS[2]}")
        elif key == ord('4'):
            selected = 3
            print(f"\n[CMD] {COMMANDS[3]}")
        elif key == ord('5'):
            selected = 4
            print(f"\n[CMD] {COMMANDS[4]}")

except KeyboardInterrupt:
    print("\n\n[!] Interrupted")

finally:
    running = False
    print("\n[*] Cleaning up...")
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    eeg.stop_streaming()
    print("\n[OK] System stopped.")