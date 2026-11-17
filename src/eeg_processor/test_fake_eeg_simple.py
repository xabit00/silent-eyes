"""
test_fake_eeg_simple.py - Simple Test for Fake EEG Simulator
Uses pynput for keyboard detection (works better on Windows)
"""

import time
import sys
import os

# Add the parent directory to path so we can import our module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eeg_processor.fake_eeg import FakeEEG

# Step 1: Create the Fake EEG
eeg = FakeEEG()

# Step 2: Start streaming in the background
eeg.start_streaming()

print("\n" + "="*60)
print("🧠 FAKE EEG SIMULATOR")
print("="*60)
print("Instructions:")
print("  Press 'F' to simulate FOCUS (brain concentration)")
print("  Press 'Q' to QUIT the program")
print("="*60 + "\n")

# We'll use a simple input-based approach instead of complex key detection
# This is more reliable on Windows

try:
    while True:
        # Get the latest sample
        signal, focus = eeg.get_latest_sample()
        
        # Create a visual bar for the focus level
        bar_length = int(focus * 20)
        focus_bar = "█" * bar_length + "░" * (20 - bar_length)
        
        # Display the data
        print(f"Signal: {signal:8.2f} | Focus: [{focus_bar}] {focus*100:5.1f}%", end="\r")
        
        # Check for keyboard input using a different method
        # This doesn't block the loop
        try:
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'f' or key == b'F':
                    eeg.trigger_focus()
                elif key == b'q' or key == b'Q':
                    print("\n\n👋 Quitting...")
                    break
        except:
            # Fallback: just wait for input in a separate thread
            pass
        
        # Small delay
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n\n👋 Stopping...")

finally:
    # Always clean up
    eeg.stop_streaming()
    print("✅ Done!")