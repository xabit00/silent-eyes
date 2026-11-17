"""
test_environment.py - Quick test to verify all libraries are working
"""

import numpy as np
import cv2
import mediapipe as mp
import pyttsx3
import scipy
import PIL
import joblib

print("✅ All libraries imported successfully!")
print(f"   NumPy version: {np.__version__}")
print(f"   OpenCV version: {cv2.__version__}")
print(f"   MediaPipe version: {mp.__version__}")
print(f"   SciPy version: {scipy.__version__}")
print(f"   Pillow version: {PIL.__version__}")
print(f"   Joblib version: {joblib.__version__}")

# Test text-to-speech
print("\nTesting Text-to-Speech...")
engine = pyttsx3.init()
engine.say("Hello! Welcome to the Neuro Silent project.")
engine.runAndWait()
print("✅ Text-to-Speech working!")

print("\n🎉 All tests passed! Your environment is ready for development.")