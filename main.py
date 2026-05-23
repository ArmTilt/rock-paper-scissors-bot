import sys
import cv2
import pygame
from detector import GestureDetector, COUNTER_MOVES
from game import GameStateMachine, State
from ui import GameUI


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: cannot open webcam. Check camera permissions in System Settings → Privacy → Camera.")
        sys.exit(1)

    detector = GestureDetector()
    game = GameStateMachine()
    ui = GameUI()

    running = True
    while running:
        ret, frame = cap.read()
        if not ret:
            frame = None

        # Detect every frame — MediaPipe is fast enough at 30fps
        _, gesture, confidence, annotated = detector.process(frame) if frame is not None else (None, None, 0.0, frame)
        bot_counter = COUNTER_MOVES.get(gesture) if gesture else None

        # Handle pygame events
        for event in ui.process_events():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.on_space()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # Update game state — only feed gesture during throw window
        if game.state == State.THROW_WINDOW:
            game.update(gesture, confidence, bot_counter)
        else:
            game.update(None, 0.0, None)

        # Render
        ui.update_frame(annotated if annotated is not None else frame, game)

    cap.release()
    ui.quit()


if __name__ == '__main__':
    main()
