import numpy as np
import os
import time
import urllib.request

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

# Hand skeleton connections for drawing (landmark index pairs)
_HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]

_MODEL_URL = (
    'https://storage.googleapis.com/mediapipe-models/'
    'hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
)
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hand_landmarker.task')


def _ensure_model():
    if not os.path.exists(_MODEL_PATH):
        print('Downloading hand landmarker model (~30 MB) on first run...')
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print('Model ready.')


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


def _draw_hand(frame, landmarks):
    """Draw hand skeleton on frame using OpenCV directly."""
    import cv2
    h, w = frame.shape[:2]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in _HAND_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 200, 100), 2)
    for pt in pts:
        cv2.circle(frame, pt, 5, (255, 80, 80), -1)


class GestureDetector:
    def __init__(self):
        import cv2 as _cv2
        import mediapipe as _mp
        from mediapipe.tasks import python as _mptasks
        from mediapipe.tasks.python import vision as _vision

        _ensure_model()

        self._cv2 = _cv2
        self._mp = _mp
        options = _vision.HandLandmarkerOptions(
            base_options=_mptasks.BaseOptions(model_asset_path=_MODEL_PATH),
            running_mode=_vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self._landmarker = _vision.HandLandmarker.create_from_options(options)
        self._start_ms = int(time.time() * 1000)

    def close(self):
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def process(self, bgr_frame):
        """
        Returns (landmarks, gesture, confidence, annotated_frame).
        landmarks is None when no hand is detected.
        gesture is None when hand is detected but pose is ambiguous.
        """
        rgb = self._cv2.cvtColor(bgr_frame, self._cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(time.time() * 1000) - self._start_ms

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        annotated = bgr_frame.copy()

        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            _draw_hand(annotated, landmarks)
            gesture, confidence = classify_gesture(landmarks)
            return landmarks, gesture, confidence, annotated

        return None, None, 0.0, annotated
