"""
blink_detector.py - Webcam-based Blink Detection
"""

import cv2
import mediapipe as mp
import numpy as np
import time

class BlinkDetector:
    """Detects intentional blinks using webcam and MediaPipe."""
    
    def __init__(self):
        # MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Eye landmark indices
        self.LEFT_EYE_INDICES = [33, 133, 157, 158, 159, 160, 161, 173]
        self.RIGHT_EYE_INDICES = [362, 263, 387, 386, 385, 384, 398, 466]
        
        # EAR thresholds
        self.EAR_THRESHOLD = 0.2
        self.INTENTIONAL_BLINK_DURATION = 0.5
        
        # Blink tracking
        self.is_closed = False
        self.closed_start_time = None
        self.total_blinks = 0
        
        print("👁️ Blink Detector initialized.")
    
    def get_eye_landmarks(self, face_landmarks, eye_indices):
        """Extract eye landmarks from face mesh."""
        landmarks = []
        for idx in eye_indices:
            landmark = face_landmarks.landmark[idx]
            landmarks.append((landmark.x, landmark.y))
        return landmarks
    
    def eye_aspect_ratio(self, eye_landmarks):
        """Calculate Eye Aspect Ratio (EAR)."""
        eye = np.array(eye_landmarks)
        p2_p6 = np.linalg.norm(eye[1] - eye[5])
        p3_p5 = np.linalg.norm(eye[2] - eye[4])
        p1_p4 = np.linalg.norm(eye[0] - eye[3])
        ear = (p2_p6 + p3_p5) / (2.0 * p1_p4 + 1e-6)
        return ear
    
    def detect_blink(self, frame):
        """Process a frame and detect blinks."""
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        result = {
            'blink_detected': False,
            'is_intentional': False,
            'left_ear': 0.0,
            'right_ear': 0.0,
            'total_blinks': self.total_blinks,
            'eyes_open': True
        }
        
        if not results.multi_face_landmarks:
            return result
        
        face_landmarks = results.multi_face_landmarks[0]
        
        # Get eye landmarks
        left_eye_points = self.get_eye_landmarks(face_landmarks, self.LEFT_EYE_INDICES)
        right_eye_points = self.get_eye_landmarks(face_landmarks, self.RIGHT_EYE_INDICES)
        
        # Calculate EAR
        left_ear = self.eye_aspect_ratio(left_eye_points)
        right_ear = self.eye_aspect_ratio(right_eye_points)
        avg_ear = (left_ear + right_ear) / 2.0
        
        result['left_ear'] = left_ear
        result['right_ear'] = right_ear
        
        # Check if eye is closed
        if avg_ear < self.EAR_THRESHOLD:
            result['eyes_open'] = False
            
            if not self.is_closed:
                self.is_closed = True
                self.closed_start_time = time.time()
            else:
                if self.closed_start_time is not None:
                    closed_duration = time.time() - self.closed_start_time
                    if closed_duration >= self.INTENTIONAL_BLINK_DURATION:
                        result['blink_detected'] = True
                        result['is_intentional'] = True
                        self.total_blinks += 1
                        self.is_closed = False
                        self.closed_start_time = None
        else:
            result['eyes_open'] = True
            if self.is_closed:
                self.is_closed = False
                self.closed_start_time = None
        
        result['total_blinks'] = self.total_blinks
        return result
    
    def draw_debug_info(self, frame, result):
        """Draw debug information on frame."""
        left_ear = result['left_ear']
        right_ear = result['right_ear']
        avg_ear = (left_ear + right_ear) / 2.0
        
        cv2.putText(frame, f"EAR: {avg_ear:.3f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Blinks: {result['total_blinks']}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if result['eyes_open']:
            status = "Eyes Open"
            color = (0, 255, 0)
        else:
            status = "Eyes Closed"
            color = (0, 0, 255)
        
        cv2.putText(frame, f"Status: {status}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        if result['blink_detected'] and result['is_intentional']:
            cv2.putText(frame, "⚡ INTENTIONAL BLINK!", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        
        return frame
    
    def release(self):
        """Release resources."""
        self.face_mesh.close()
        print("👁️ Blink Detector released.")