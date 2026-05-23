import numpy as np

FINGER_INDICES = {
    'index':  (5, 6, 8),
    'middle': (9, 10, 12),
    'ring':   (13, 14, 16),
    'pinky':  (17, 18, 20),
}

COUNTER_MOVES = {
    'rock': 'paper',
    'paper': 'scissors',
    'scissors': 'rock',
}


def _angle_at_pip(landmarks, mcp_idx, pip_idx, distal_idx):
    mcp = np.array([landmarks[mcp_idx].x, landmarks[mcp_idx].y, landmarks[mcp_idx].z])
    pip = np.array([landmarks[pip_idx].x, landmarks[pip_idx].y, landmarks[pip_idx].z])
    distal = np.array([landmarks[distal_idx].x, landmarks[distal_idx].y, landmarks[distal_idx].z])
    v1 = pip - mcp
    v2 = distal - pip
    denom = np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6
    cos_a = np.dot(v1, v2) / denom
    return float(np.degrees(np.arccos(np.clip(cos_a, -1.0, 1.0))))


def classify_gesture(landmarks):
    """Return (gesture_str, confidence) or (None, 0.0) for ambiguous hands."""
    extended = {}
    for name, (mcp, pip, tip) in FINGER_INDICES.items():
        angle = _angle_at_pip(landmarks, mcp, pip, tip)
        extended[name] = angle < 90

    i = extended['index']
    m = extended['middle']
    r = extended['ring']
    p = extended['pinky']

    if not i and not m and not r and not p:
        return 'rock', 0.95
    if i and m and not r and not p:
        return 'scissors', 0.95
    if i and m and r and p:
        return 'paper', 0.95
    return None, 0.0


class GestureDetector:
    def __init__(self):
        # Defer heavy imports to instantiation time so the pure functions
        # (_angle_at_pip, classify_gesture) are importable without triggering
        # mediapipe's module-level initialisation.
        import cv2 as _cv2
        import mediapipe as _mp
        self._cv2 = _cv2
        self._mp_hands = _mp.solutions.hands
        self._mp_draw = _mp.solutions.drawing_utils
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

    def close(self):
        """Close the MediaPipe Hands instance."""
        self._hands.close()

    def __enter__(self):
        """Support using GestureDetector as a context manager."""
        return self

    def __exit__(self, *_):
        """Close resources when exiting the context manager."""
        self.close()

    def process(self, bgr_frame):
        """
        Returns (landmarks, gesture, confidence, annotated_frame).
        landmarks is None when no hand is detected.
        gesture is None when hand is detected but pose is ambiguous.
        """
        rgb = self._cv2.cvtColor(bgr_frame, self._cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb)
        annotated = bgr_frame.copy()

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            self._mp_draw.draw_landmarks(annotated, hand, self._mp_hands.HAND_CONNECTIONS)
            gesture, confidence = classify_gesture(hand.landmark)
            return hand.landmark, gesture, confidence, annotated

        return None, None, 0.0, annotated
