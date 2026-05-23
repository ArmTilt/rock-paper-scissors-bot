import pytest
from game import GameStateMachine, State


def make_game(now=0.0):
    g = GameStateMachine()
    g._now = lambda: now  # override time source for tests
    return g


def test_initial_state():
    g = make_game()
    assert g.state == State.IDLE
    assert g.bot_move is None
    assert g.rounds == 0
    assert g.bot_wins == 0


def test_space_starts_countdown():
    g = make_game(now=0.0)
    g.on_space()
    assert g.state == State.COUNTDOWN


def test_space_ignored_during_countdown():
    g = make_game(now=0.0)
    g.on_space()
    g.on_space()  # second press during countdown — should do nothing
    assert g.state == State.COUNTDOWN


def test_countdown_label_progression():
    g = make_game(now=0.0)
    g.on_space()

    g._now = lambda: 0.5
    g.update(None, 0.0, None)
    assert g.countdown_label == '3'

    g._now = lambda: 1.5
    g.update(None, 0.0, None)
    assert g.countdown_label == '2'

    g._now = lambda: 2.5
    g.update(None, 0.0, None)
    assert g.countdown_label == '1'

    g._now = lambda: 3.1
    g.update(None, 0.0, None)
    assert g.countdown_label == 'SHOOT!'


def test_transitions_to_throw_window_after_shoot():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)
    assert g.state == State.THROW_WINDOW


def test_gesture_detected_triggers_result():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)  # enter THROW_WINDOW

    g._now = lambda: 3.15
    g.update('rock', 0.95, 'paper')
    assert g.state == State.RESULT
    assert g.user_move == 'rock'
    assert g.bot_move == 'paper'
    assert g.rounds == 1
    assert g.bot_wins == 1


def test_timeout_triggers_void():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)  # enter THROW_WINDOW

    g._now = lambda: 5.2  # 2.1s after entering throw window
    g.update(None, 0.0, None)
    assert g.state == State.VOID
    assert g.rounds == 0  # void round not counted


def test_result_auto_returns_to_idle():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)
    g._now = lambda: 3.15
    g.update('scissors', 0.95, 'rock')
    assert g.state == State.RESULT

    g._now = lambda: 5.2  # 2s+ after result
    g.update(None, 0.0, None)
    assert g.state == State.IDLE


def test_void_auto_returns_to_idle():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)
    g._now = lambda: 5.2
    g.update(None, 0.0, None)
    assert g.state == State.VOID

    g._now = lambda: 6.8  # 1.6s after void
    g.update(None, 0.0, None)
    assert g.state == State.IDLE


def test_low_confidence_gesture_not_counted():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)

    g._now = lambda: 3.15
    g.update('rock', 0.5, 'paper')  # confidence below threshold
    assert g.state == State.THROW_WINDOW  # should NOT have triggered result


def test_space_during_result_starts_new_round():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)
    g._now = lambda: 3.15
    g.update('paper', 0.95, 'scissors')
    assert g.state == State.RESULT

    g._now = lambda: 3.2
    g.on_space()
    assert g.state == State.COUNTDOWN


def test_exact_confidence_threshold_counts():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)  # enter THROW_WINDOW

    g._now = lambda: 3.15
    g.update('rock', 0.70, 'paper')  # exactly at threshold
    assert g.state == State.RESULT


def test_space_during_void_starts_new_round():
    g = make_game(now=0.0)
    g.on_space()
    g._now = lambda: 3.1
    g.update(None, 0.0, None)   # enter THROW_WINDOW
    g._now = lambda: 5.2
    g.update(None, 0.0, None)   # timeout → VOID
    assert g.state == State.VOID

    g._now = lambda: 5.3
    g.on_space()
    assert g.state == State.COUNTDOWN
