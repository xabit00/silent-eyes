"""
test_fake_eeg_ultra_simple.py - Ultra Simple Test for Fake EEG
"""

import time
import sys
import os
import threading

# Add the parent directory to path so we can import our module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eeg_processor.fake_eeg import FakeEEG

def keyboard_listener(eeg):
    """
    Simple keyboard listener that runs in a separate thread.
    """
    print("\n🎮 Keyboard controls active!")
    print("   Press 'f' then ENTER to focus")
    print("   Press 'q' then ENTER to quit")
    
    while True:
        try:
            # Wait for user input
            user_input = input()
            
            if user_input.lower() == 'f':
                eeg.trigger_focus()
            elif user_input.lower() == 'q':
                print("\n👋 Quitting...")
                return
        except:
            break

# Step 1: Create the Fake EEG
eeg = FakeEEG()

# Step 2: Start streaming in the background
eeg.start_streaming()

# Step 3: Start keyboard listener in a separate thread
listener_thread = threading.Thread(target=keyboard_listener, args=(eeg,))
listener_thread.daemon = True
listener_thread.start()

print("\n" + "="*60)
print("🧠 FAKE EEG SIMULATOR")
print("="*60)
print("Instructions:")
print("  Type 'f' and press ENTER to simulate FOCUS")
print("  Type 'q' and press ENTER to QUIT")
print("="*60 + "\n")

print("📊 Real-time EEG Data (updates every 0.05 seconds):")

try:
    while True:
        # Get the latest sample
        signal, focus = eeg.get_latest_sample()
        
        # Create a visual bar for the focus level
        bar_length = int(focus * 20)
        focus_bar = "█" * bar_length + "░" * (20 - bar_length)
        
        # Display the data
        print(f"Signal: {signal:8.2f} | Focus: [{focus_bar}] {focus*100:5.1f}%", end="\r")
        
        # Small delay
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n\n👋 Stopping...")

finally:
    # Always clean up
    eeg.stop_streaming()
    print("✅ Done!")