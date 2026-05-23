import time
from enum import Enum

class State(Enum):
    IDLE = 'idle'
    COUNTDOWN = 'countdown'
    THROW_WINDOW = 'throw_window'
    RESULT = 'result'
    VOID = 'void'

_COUNTDOWN_BEATS = [(0.0, '3'), (1.0, '2'), (2.0, '1'), (3.0, 'SHOOT!')]
_THROW_TIMEOUT = 2.0
_RESULT_DISPLAY = 2.0
_VOID_DISPLAY = 1.5
_CONFIDENCE_THRESHOLD = 0.7


class GameStateMachine:
    def __init__(self):
        self.state = State.IDLE
        self.bot_move = None
        self.user_move = None
        self.rounds = 0
        self.bot_wins = 0
        self.countdown_label = ''
        self.status_text = 'Press SPACE to play'
        self._t = 0.0
        self._now = time.time  # injectable for testing

    def on_space(self):
        if self.state in (State.IDLE, State.RESULT, State.VOID):
            self._start_countdown()

    def _start_countdown(self):
        self.state = State.COUNTDOWN
        self._t = self._now()
        self.bot_move = None
        self.user_move = None
        self.countdown_label = '3'
        self.status_text = ''

    def update(self, gesture, confidence, bot_counter):
        """Call every frame with current gesture detection results."""
        now = self._now()

        if self.state == State.COUNTDOWN:
            elapsed = now - self._t
            for beat_time, label in _COUNTDOWN_BEATS:
                if elapsed >= beat_time:
                    self.countdown_label = label
            if elapsed >= 3.0:
                # countdown_label stays as 'SHOOT!' through THROW_WINDOW intentionally
                # (cleared when gesture detected or timeout)
                self.state = State.THROW_WINDOW
                self._t = now

        elif self.state == State.THROW_WINDOW:
            elapsed = now - self._t
            if gesture and confidence >= _CONFIDENCE_THRESHOLD:
                self.user_move = gesture
                self.bot_move = bot_counter
                self.rounds += 1
                self.bot_wins += 1  # bot wins every round by design
                self.state = State.RESULT
                self._t = now
                self.countdown_label = ''
                self.status_text = f'Bot plays {self.bot_move.upper()}!'
            elif elapsed > _THROW_TIMEOUT:
                self.state = State.VOID
                self._t = now
                self.countdown_label = ''
                self.status_text = 'No hand detected — round void'

        elif self.state == State.RESULT:
            if now - self._t > _RESULT_DISPLAY:
                self.state = State.IDLE
                self.status_text = 'Press SPACE to play'

        elif self.state == State.VOID:
            if now - self._t > _VOID_DISPLAY:
                self.state = State.IDLE
                self.status_text = 'Press SPACE to play'
