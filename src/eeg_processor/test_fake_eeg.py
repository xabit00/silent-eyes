"""
test_fake_eeg.py - Test the Fake EEG Simulator
"""

import time
import threading
import keyboard  # We need to install this first

# Add the parent directory to path so we can import our module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eeg_processor.fake_eeg import FakeEEG

def listen_for_keys(eeg):
    """
    Listen for keyboard input to trigger focus.
    
    This runs in a separate thread so it doesn't block the main loop.
    """
    print("Press 'f' to simulate focus. Press 'q' to quit.")
    
    while True:
        if keyboard.is_pressed('f'):
            eeg.trigger_focus()
            time.sleep(0.5)  # Prevent multiple triggers
        elif keyboard.is_pressed('q'):
            print("Quitting...")
            break
        time.sleep(0.1)

# Step 1: Create the Fake EEG
eeg = FakeEEG()

# Step 2: Start streaming in the background
eeg.start_streaming()

# Step 3: Start a keyboard listener in a separate thread
keyboard_thread = threading.Thread(target=listen_for_keys, args=(eeg,))
keyboard_thread.daemon = True
keyboard_thread.start()

# Step 4: Main loop - display the EEG data in real-time
print("\n📊 Real-time EEG Data:")
print("Press 'f' to simulate focus, 'q' to quit\n")

try:
    while True:
        # Get the latest sample
        signal, focus = eeg.get_latest_sample()
        
        # Create a visual bar for the focus level
        bar_length = int(focus * 20)
        focus_bar = "█" * bar_length + "░" * (20 - bar_length)
        
        # Display the data
        print(f"Signal: {signal:8.2f} | Focus: [{focus_bar}] {focus*100:5.1f}%", end="\r")
        
        # Small delay to avoid flooding the console
        time.sleep(0.05)
        
except KeyboardInterrupt:
    print("\n\n👋 Stopping...")

finally:
    # Always clean up
    eeg.stop_streaming()
    print("✅ Done!")