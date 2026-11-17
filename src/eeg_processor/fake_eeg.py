"""
fake_eeg.py - EEG Simulator Module

This module simulates brainwave data for the Silent Eyes component.
It generates fake EEG signals and allows manual triggering of "focus" events.
Think of it like a driving simulator for brain signals!
"""

import random
import math
import time
import threading

class FakeEEG:
    """
    A simulated EEG headset.
    
    This class mimics real EEG data by generating random noise with occasional
    focus spikes. It also allows manual control via keyboard input.
    
    Real-world analogy: This is like a heartbeat monitor that normally shows
    a steady rhythm, but spikes when the patient gets excited.
    """
    
    def __init__(self):
        """
        Initialize the fake EEG with default values.
        This runs automatically when you create a FakeEEG object.
        """
        # The current focus level (0.0 = no focus, 1.0 = maximum focus)
        # Think of this like a volume knob that goes from 0 to 10
        self.focus_level = 0.0
        
        # Flag to control the background thread
        self.running = False
        
        # The latest EEG sample (will be updated continuously)
        self.latest_sample = 0.0
        
        # Lock to prevent data corruption when multiple threads access variables
        # Think of this like a "Do Not Disturb" sign for our data
        self._lock = threading.Lock()
        
        print("🧠 Fake EEG initialized. Press 'f' to simulate focus.")
    
    def generate_noise(self):
        """
        Generate realistic-looking random brainwave noise.
        
        In real EEG, signals are a combination of different frequencies.
        We simulate this using a mix of random numbers and sine waves.
        
        Why sine waves? Because brainwaves are rhythmic, like ocean waves.
        """
        # Base random noise (like the background hum of the brain)
        # This is like static on a radio
        noise = random.uniform(-5, 5)
        
        # Add a sine wave component to simulate rhythmic brain activity
        # math.sin(time.time()) creates a smooth wave that goes up and down
        # The * 2 makes it faster (2 Hz = 2 waves per second)
        wave = 3 * math.sin(time.time() * 2)
        
        # Add a faster wave for beta-like activity (concentration waves)
        # * 10 means 10 waves per second
        fast_wave = 2 * math.sin(time.time() * 10)
        
        # Combine all three to make realistic-looking brain data
        return noise + wave + fast_wave
    
    def update_focus(self):
        """
        Update the focus level over time.
        
        When 'f' is pressed, focus spikes to 1.0 and slowly decays.
        This mimics how real focus works - you can't focus intensely forever.
        
        Real-world analogy: Think of sprinting. You can run fast for a short
        burst, but you slow down quickly.
        """
        with self._lock:
            # If we have a high focus level, decay it slowly
            if self.focus_level > 0.0:
                # Reduce focus by a small amount each update cycle
                # 0.01 means it takes about 100 cycles to go from 1.0 to 0.0
                self.focus_level -= 0.01
                
                # Ensure focus doesn't go below zero
                if self.focus_level < 0.0:
                    self.focus_level = 0.0
    
    def trigger_focus(self):
        """
        Manually trigger a focus event.
        
        This simulates the user concentrating on a task.
        In real usage, this would happen automatically when the user focuses.
        
        Think of this like pressing a "Boost" button in a video game.
        """
        with self._lock:
            self.focus_level = 1.0
            print("💡 FOCUS TRIGGERED! (Simulating user concentration)")
    
    def get_sample(self):
        """
        Get the latest EEG sample with the current focus level.
        
        This is the main method that other parts of the program will call
        to get the current brainwave reading.
        
        Returns:
            tuple: (raw_signal, focus_level)
            
        Example output: (12.34, 0.85) 
        Means: The raw brain signal is 12.34, and focus is at 85%
        """
        # Step 1: Generate a raw signal (the brain noise)
        raw_signal = self.generate_noise()
        
        # Step 2: If the user is focusing, add a boost to the signal
        with self._lock:
            if self.focus_level > 0.5:
                # Strong focus: add a large spike to the signal
                # 15 is just a number that makes the spike obvious
                raw_signal += 15 * self.focus_level
            
            # Store the current focus level for the return value
            current_focus = self.focus_level
        
        # Step 3: Update the focus decay (gradually reduce focus)
        self.update_focus()
        
        # Step 4: Return both the raw signal and the focus state
        return raw_signal, current_focus
    
    def start_streaming(self):
        """
        Start a background thread that continuously generates EEG data.
        
        In a real system, this would connect to the Bluetooth headset.
        Here, we just generate fake data every millisecond.
        
        Why a background thread? So the main program can do other things
        while the EEG runs in the background, like a silent worker.
        """
        if self.running:
            print("⚠️ EEG streaming is already running.")
            return
        
        self.running = True
        
        # Create a background thread
        # daemon=True means the thread will exit when the main program exits
        self._stream_thread = threading.Thread(target=self._stream_loop)
        self._stream_thread.daemon = True
        self._stream_thread.start()
        
        print("🔄 EEG streaming started. Data is flowing...")
    
    def _stream_loop(self):
        """
        The main loop that runs in the background.
        
        This generates fake EEG data continuously and stores the latest sample.
        It runs forever until the program stops.
        """
        while self.running:
            # Get a sample
            sample, focus = self.get_sample()
            
            # Store it for other parts of the program to read
            with self._lock:
                self.latest_sample = sample
            
            # Sleep for a very short time to simulate real-time data
            # 0.01 seconds = 100 samples per second (good enough for our demo)
            time.sleep(0.01)
        
        print("🔄 EEG streaming stopped.")
    
    def get_latest_sample(self):
        """
        Get the most recent EEG sample from the background stream.
        
        This is the main method you will call from your main program.
        
        Returns:
            tuple: (latest_raw_signal, current_focus_level)
        """
        with self._lock:
            return self.latest_sample, self.focus_level
    
    def stop_streaming(self):
        """
        Stop the background streaming thread.
        Always call this when you're done to clean up properly.
        """
        self.running = False
        print("🛑 EEG streaming stopped.")