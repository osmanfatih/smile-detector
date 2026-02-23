"""
Smile detector using MediaPipe Face Mesh.
Returns smile score and tier: NO_FACE | NO_SMILE | SMALL_SMILE | FULL_SMILE
"""

import base64
import numpy as np
import cv2
import mediapipe as mp


class SmileDetector:
    # Smile score thresholds
    SMALL_SMILE_THRESHOLD = 0.40
    FULL_SMILE_THRESHOLD = 0.70

    # Key MediaPipe Face Mesh landmark indices
    LEFT_CORNER = 61
    RIGHT_CORNER = 291
    UPPER_LIP = 13
    LOWER_LIP = 14
    NOSE_TIP = 1
    CHIN = 152

    MESSAGES = {
        "NO_FACE": "No face detected — step into the frame! 👀",
        "NO_SMILE": "Come on, show us that smile! 😊",
        "SMALL_SMILE": "Almost there — give us a bigger smile! 😁",
        "FULL_SMILE": "You did it! 🎉 Amazing smile!",
    }

    def __init__(self):
        self._mp_face_mesh = mp.solutions.face_mesh
        self._face_mesh = self._mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def detect(self, frame_bytes: bytes) -> dict:
        """
        Accepts raw JPEG bytes (or base64-encoded JPEG string bytes).
        Returns dict: {status, smile_score, message}
        """
        # Decode image
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return self._result("NO_FACE", 0.0)

        # MediaPipe expects RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return self._result("NO_FACE", 0.0)

        landmarks = results.multi_face_landmarks[0].landmark
        score = self._calculate_smile_score(landmarks)

        if score < self.SMALL_SMILE_THRESHOLD:
            status = "NO_SMILE"
        elif score < self.FULL_SMILE_THRESHOLD:
            status = "SMALL_SMILE"
        else:
            status = "FULL_SMILE"

        return self._result(status, score)

    def _calculate_smile_score(self, landmarks) -> float:
        """
        Smile score based on how much the mouth corners are raised
        relative to the mouth center, normalized by face height.

        In image coordinates (y increases downward):
          - Smiling → corners move UP → corner.y < mouth_center.y
          - corner_rise = mouth_center_y - corner_y  (positive = smile)
        """
        left_corner = landmarks[self.LEFT_CORNER]
        right_corner = landmarks[self.RIGHT_CORNER]
        upper_lip = landmarks[self.UPPER_LIP]
        lower_lip = landmarks[self.LOWER_LIP]
        nose_tip = landmarks[self.NOSE_TIP]
        chin = landmarks[self.CHIN]

        mouth_center_y = (upper_lip.y + lower_lip.y) / 2.0
        corner_avg_y = (left_corner.y + right_corner.y) / 2.0

        # How much corners are raised above the mouth center
        corner_rise = mouth_center_y - corner_avg_y

        # Normalize by lower face height (nose tip to chin)
        face_height = chin.y - nose_tip.y
        if face_height < 0.001:
            return 0.0

        normalized = corner_rise / face_height

        # Typical range: ~0.0 (neutral) → ~0.15 (big smile)
        # Scale so 0.15 maps to 1.0
        score = max(0.0, min(1.0, normalized / 0.15))
        return score

    def _result(self, status: str, score: float) -> dict:
        return {
            "status": status,
            "smile_score": round(score, 4),
            "message": self.MESSAGES[status],
        }
