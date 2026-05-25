# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## GitHub

- **Repo:** `https://github.com/ArmTilt/rock-paper-scissors-bot`
- **Default branch:** `main` — always the stable, working version
- When adding a new feature or fix, create a branch first: `git checkout -b feature/<name>` or `fix/<name>`
- Push branches and open PRs against `main`; merge only when the feature is working and tests pass

## Commands

```bash
# Run the game
python main.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_game.py

# Run a single test by name
pytest tests/test_game.py::test_gesture_detected_triggers_result
```

## Architecture

The app is structured as three clean layers with no circular dependencies:

```
detector.py  →  game.py  →  ui.py
                  ↑
              main.py (wires all three together)
```

**`detector.py` — vision layer**
- `GestureDetector` wraps MediaPipe's `HandLandmarker` in VIDEO mode (not IMAGE — timestamp required)
- `classify_gesture(landmarks)` uses PIP joint angles, not y-coordinate comparisons, making it robust to hand tilt
- `_ensure_model()` auto-downloads `hand_landmarker.task` (~30 MB) on first run if missing
- `COUNTER_MOVES` dict is the only place the bot's winning logic lives

**`game.py` — state machine**
- `GameStateMachine` has 5 states: `IDLE → COUNTDOWN → THROW_WINDOW → RESULT → IDLE` (or `VOID` on timeout)
- `_now` is an injectable time source (`self._now = lambda: now`) — used heavily in tests to simulate time without sleeping
- `update()` is called every frame; only processes gesture input when state is `THROW_WINDOW`
- Confidence threshold (`_CONFIDENCE_THRESHOLD = 0.7`) is enforced here, not in the detector

**`ui.py` — rendering layer**
- `GameUI` is a pure renderer — it reads from `GameStateMachine` but never modifies it
- Emoji sprites are generated at startup via Apple Color Emoji font and cached as PNG files in `assets/`
- Layout is fixed: 1280×600, left 640px = webcam feed, right 640px = bot panel, 60px bars top/bottom

**`main.py` — entry point**
- The game loop: read webcam frame → run detector → handle pygame events → update state machine → render
- Gesture is only passed to `game.update()` when `game.state == State.THROW_WINDOW`; otherwise `None` is passed

## Testing approach

- Tests in `tests/` cover `detector.py` and `game.py` only — `ui.py` and `main.py` are not tested (require display/webcam)
- `_make_landmarks()` in `test_detector.py` builds minimal landmark mocks without importing MediaPipe
- `make_game(now=0.0)` in `test_game.py` injects a fixed clock, letting all timing tests run instantly
- No mocking libraries used — time injection via lambda is the only test seam needed
