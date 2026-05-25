# Rock Paper Scissors Bot 🤖✂️

A desktop game that **beats you every single time** — not by predicting your move, but by reading your completed gesture faster than your brain can process the result.

Inspired by viral RPS robots, this bot uses your webcam and hand-tracking AI to classify your throw in ~33–66ms and display the counter-move. At that speed, it looks simultaneous to a human.

---

## How It Works

1. Press **Space** to start a round
2. A countdown runs: **3… 2… 1… SHOOT**
3. You throw your gesture — the bot reads it the instant your hand settles
4. The bot reveals its counter-move and wins

The trick: human perception has ~150ms of slack. The bot classifies your gesture in ~33–66ms — well within that window — so the reveal *feels* simultaneous even though it's always a reaction.

---

## Demo

> *(screenshot coming soon)*

---

## Requirements

- **macOS** (tested on M3 Air — the Neural Engine accelerates hand tracking)
- **Python 3.9+**
- A webcam

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/ArmTilt/rock-paper-scissors-bot.git
cd rock-paper-scissors-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

> **First launch:** The app will automatically download the MediaPipe hand-tracking model (~30 MB). This only happens once.

---

## Controls

| Key | Action |
|-----|--------|
| `Space` | Start a round / trigger countdown |
| `Esc` | Quit |

---

## How the Gesture Detection Works

The bot doesn't use simple up/down finger comparisons (which break when your hand is tilted). Instead it measures the **angle at each finger's middle knuckle (PIP joint)** in 3D space:

| Gesture | Rule |
|---------|------|
| ✊ Rock | All four fingers curled |
| ✋ Paper | All four fingers extended |
| ✌️ Scissors | Index + middle extended, ring + pinky curled |

Detection only triggers when MediaPipe's landmark confidence exceeds 70%. If your hand isn't clearly visible, the round waits for a cleaner read.

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Hand tracking | [MediaPipe](https://developers.google.com/mediapipe) |
| Webcam capture | [OpenCV](https://opencv.org) |
| Game window & UI | [pygame](https://www.pygame.org) |
| Image processing | [Pillow](https://python-pillow.org), [NumPy](https://numpy.org) |

---

## Running Tests

```bash
pytest
```
