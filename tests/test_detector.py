import numpy as np
import pytest
from detector import classify_gesture, _angle_at_pip, COUNTER_MOVES


class _LM:
    """Minimal landmark mock matching mediapipe NormalizedLandmark interface."""
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


def _make_landmarks(finger_states):
    """
    finger_states: dict with keys 'index','middle','ring','pinky'
                   values: 'extended' or 'curled'
    Returns a 21-element list of _LM mocks.
    """
    lms = [_LM(0.5, 0.9)] * 21  # default: wrist area

    configs = {
        'index':  (5, 6, 8),
        'middle': (9, 10, 12),
        'ring':   (13, 14, 16),
        'pinky':  (17, 18, 20),
    }
    for finger, (mcp_i, pip_i, tip_i) in configs.items():
        lms[mcp_i] = _LM(0.5, 0.80)
        lms[pip_i] = _LM(0.5, 0.60)
        if finger_states.get(finger) == 'extended':
            lms[tip_i] = _LM(0.5, 0.20)   # tip far above PIP → angle ~0°
        else:
            lms[tip_i] = _LM(0.5, 0.72, 0.15)  # tip curls back → angle >90°
    return lms


def test_angle_extended_finger():
    lms = _make_landmarks({'index': 'extended'})
    angle = _angle_at_pip(lms, 5, 6, 8)
    assert angle < 90, f"Expected extended (angle<90), got {angle:.1f}"


def test_angle_curled_finger():
    lms = _make_landmarks({'index': 'curled'})
    angle = _angle_at_pip(lms, 5, 6, 8)
    assert angle > 90, f"Expected curled (angle>90), got {angle:.1f}"


def test_classify_rock():
    lms = _make_landmarks({f: 'curled' for f in ['index','middle','ring','pinky']})
    gesture, conf = classify_gesture(lms)
    assert gesture == 'rock'
    assert conf > 0.9


def test_classify_paper():
    lms = _make_landmarks({f: 'extended' for f in ['index','middle','ring','pinky']})
    gesture, conf = classify_gesture(lms)
    assert gesture == 'paper'
    assert conf > 0.9


def test_classify_scissors():
    lms = _make_landmarks({
        'index': 'extended', 'middle': 'extended',
        'ring': 'curled', 'pinky': 'curled',
    })
    gesture, conf = classify_gesture(lms)
    assert gesture == 'scissors'
    assert conf > 0.9


def test_classify_ambiguous():
    # Three fingers extended — not a valid RPS gesture
    lms = _make_landmarks({
        'index': 'extended', 'middle': 'extended', 'ring': 'extended',
        'pinky': 'curled',
    })
    gesture, conf = classify_gesture(lms)
    assert gesture is None
    assert conf == 0.0


def test_counter_moves():
    assert COUNTER_MOVES['rock'] == 'paper'
    assert COUNTER_MOVES['paper'] == 'scissors'
    assert COUNTER_MOVES['scissors'] == 'rock'
