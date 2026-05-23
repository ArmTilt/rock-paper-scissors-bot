# Rock Paper Scissors Bot — PRD

**Last updated:** 2026-05-23  
**Status:** In brainstorm / pre-implementation

---

## Goal

A local desktop app that plays Rock Paper Scissors against the user and wins every single time. It works like the viral RPS robots — it appears to play its move simultaneously with the user, but it wins because it classifies the user's gesture the instant it settles and counters it in real time.

The app only needs to run on one machine (Mac M3 Air). It will not be published or distributed.

---

## How It Works (Core Mechanic)

The bot does **not** predict mid-throw. Instead:

1. A countdown runs ("3... 2... 1... SHOOT")
2. The user throws their gesture at SHOOT
3. MediaPipe classifies the settled gesture in 1–2 frames (~33–66ms)
4. The bot's counter-move appears simultaneously with the user's gesture completing

At ~33–66ms classification latency, this is indistinguishable from simultaneous to a human (our perception has ~150ms of slack). The bot wins every time because it counters the actual completed gesture, not a prediction.

---

## Technical Stack

| Component | Choice | Reason |
|---|---|---|
| Language | Python | Standard for CV projects, Claude Code will build it |
| Hand tracking | MediaPipe >= 0.10 | Native Apple Silicon support, 21 landmarks at ~30fps |
| Video capture | OpenCV | Standard webcam access on macOS |
| UI / game window | pygame | Proper sprite support, smooth rendering, real fonts — OpenCV alone can't render emoji cleanly |
| Platform | Mac M3 Air | Neural Engine accelerates MediaPipe inference |

---

## Gesture Classification

Uses **angle at each finger's PIP joint** (middle knuckle), not raw y-coordinate comparison. This works regardless of hand rotation/tilt.

| Gesture | Detection rule |
|---|---|
| Rock | All fingers curled (PIP angle acute) |
| Paper | All fingers extended (PIP angle straight) |
| Scissors | Index + middle extended, ring + pinky curled |

Classification only triggers when MediaPipe landmark confidence > 0.7. If confidence is below threshold, the bot waits for a cleaner reading.

---

## Game Mode: Round-Based with Countdown (Option B)

- User presses **[TBD — likely spacebar]** to start a round
- Countdown displays: "3... 2... 1... SHOOT"
- User throws their gesture
- Bot classifies and reveals its counter-move within ~33–66ms of gesture settling
- Result displayed (Win / Lose / — )
- Round ends, user can start next round

**Why not freeplay (Option A):** False positives from resting hand positions, and the reveal timing is inconsistent without a shared countdown beat. Option B gives precise timing control and matches the natural RPS ritual.

---

## UI

Built in pygame. Window shows:

- **Live webcam feed** with MediaPipe hand landmarks drawn on
- **Bot move display** — large icon (rock / paper / scissors) using sprite images or high-quality emoji rendered as sprites
- **Status indicator** — "Press SPACE to start" → "3... 2... 1... SHOOT" → "Result"
- **Scoreboard** — running win/loss count

---

## Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| Prediction timing | Post-throw fast classify, not mid-throw | Mid-throw scissors vs paper is indistinguishable until late; post-throw achieves ~98%+ vs ~85-95% |
| Classification method | PIP joint angle | Robust to hand rotation; y-coordinate comparison breaks on tilted hands |
| Game flow | Round-based countdown (Option B) | Simultaneous feel is achievable by design, not luck; eliminates false positives; natural RPS ritual |
| UI toolkit | pygame | Proper sprite/font rendering; OpenCV can't cleanly render emoji |
| Score structure | Unlimited rounds, running score | No reset; play as many rounds as you want |
| No hand at throw time | Round voids, retries | Fairer than auto-win; keeps the game honest |
| Countdown trigger | Spacebar | Simple, standard |
