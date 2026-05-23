import os
import pygame
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from game import State

WIN_W, WIN_H = 1280, 600
TOP_H = 60
BOT_H = 60
MAIN_H = WIN_H - TOP_H - BOT_H  # 480
CAM_W = 640

BG_COLOR = (18, 18, 30)
PANEL_COLOR = (28, 28, 45)
ACCENT = (99, 179, 237)
TEXT_COLOR = (220, 220, 240)
DIM_TEXT = (120, 120, 150)
SHOOT_COLOR = (255, 80, 80)

EMOJI_MAP = {
    'rock': '✊',
    'paper': '✋',
    'scissors': '✌️',
}

EMOJI_FONT_PATH = '/System/Library/Fonts/Apple Color Emoji.ttc'
EMOJI_SIZE = 200


def _render_emoji_to_surface(emoji_char, size=EMOJI_SIZE):
    """Render a single emoji to a pygame Surface using Pillow."""
    canvas_size = size + 40
    img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(EMOJI_FONT_PATH, size)
        draw.text((20, 20), emoji_char, font=font, embedded_color=True)
    except Exception:
        # Fallback: draw text label
        fallback = ImageFont.load_default()
        draw.text((20, 20), emoji_char, font=fallback, fill=(220, 220, 240, 255))
    data = img.tobytes('raw', 'RGBA')
    return pygame.image.fromstring(data, img.size, 'RGBA')


def _generate_sprites(assets_dir):
    """Generate PNG sprite files and return as pygame Surfaces keyed by gesture name."""
    os.makedirs(assets_dir, exist_ok=True)
    surfaces = {}
    for name, emoji in EMOJI_MAP.items():
        path = os.path.join(assets_dir, f'{name}.png')
        surf = _render_emoji_to_surface(emoji)
        pygame.image.save(surf, path)
        surfaces[name] = surf
    return surfaces


class GameUI:
    def __init__(self, assets_dir='assets'):
        pygame.init()
        self._screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption('RPS Bot — Press SPACE to play')
        self._clock = pygame.time.Clock()

        self._font_lg = pygame.font.SysFont('helveticaneue', 72, bold=True)
        self._font_md = pygame.font.SysFont('helveticaneue', 36)
        self._font_sm = pygame.font.SysFont('helveticaneue', 22)

        self._sprites = _generate_sprites(assets_dir)
        self._cam_surf = None  # updated each frame

    def process_events(self):
        """Return list of pygame events this frame."""
        return pygame.event.get()

    def update_frame(self, bgr_frame, game):
        """Render one frame. bgr_frame is the annotated OpenCV BGR image."""
        self._screen.fill(BG_COLOR)
        self._draw_top_bar(game)
        self._draw_webcam(bgr_frame)
        self._draw_bot_panel(game)
        self._draw_bottom_bar(game)
        pygame.display.flip()
        self._clock.tick(30)

    def _draw_top_bar(self, game):
        bar = pygame.Rect(0, 0, WIN_W, TOP_H)
        pygame.draw.rect(self._screen, PANEL_COLOR, bar)
        label = self._font_md.render(
            f'Bot Wins: {game.bot_wins}   |   Rounds: {game.rounds}',
            True, TEXT_COLOR
        )
        self._screen.blit(label, (WIN_W // 2 - label.get_width() // 2, 12))

    def _draw_webcam(self, bgr_frame):
        if bgr_frame is None:
            return
        # Convert BGR → RGB, resize to fit left panel, convert to pygame surface
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        target_h = MAIN_H
        target_w = int(w * target_h / h)
        if target_w > CAM_W:
            target_w = CAM_W
            target_h = int(h * target_w / w)
        resized = cv2.resize(rgb, (target_w, target_h))
        surf = pygame.surfarray.make_surface(resized.transpose(1, 0, 2))
        x = (CAM_W - target_w) // 2
        y = TOP_H + (MAIN_H - target_h) // 2
        self._screen.blit(surf, (x, y))

    def _draw_bot_panel(self, game):
        panel = pygame.Rect(CAM_W, TOP_H, WIN_W - CAM_W, MAIN_H)
        pygame.draw.rect(self._screen, PANEL_COLOR, panel)

        center_x = CAM_W + (WIN_W - CAM_W) // 2
        center_y = TOP_H + MAIN_H // 2

        if game.state == State.RESULT and game.bot_move and game.bot_move in self._sprites:
            sprite = self._sprites[game.bot_move]
            sw, sh = sprite.get_size()
            self._screen.blit(sprite, (center_x - sw // 2, center_y - sh // 2))
            label = self._font_sm.render(game.bot_move.upper(), True, ACCENT)
            self._screen.blit(label, (center_x - label.get_width() // 2, center_y + sh // 2 + 8))
        else:
            placeholder = self._font_md.render('?', True, DIM_TEXT)
            self._screen.blit(placeholder, (center_x - placeholder.get_width() // 2,
                                            center_y - placeholder.get_height() // 2))

    def _draw_bottom_bar(self, game):
        bar = pygame.Rect(0, WIN_H - BOT_H, WIN_W, BOT_H)
        pygame.draw.rect(self._screen, PANEL_COLOR, bar)

        if game.countdown_label:
            color = SHOOT_COLOR if game.countdown_label == 'SHOOT!' else TEXT_COLOR
            text = self._font_lg.render(game.countdown_label, True, color)
        else:
            text = self._font_md.render(game.status_text, True, TEXT_COLOR)

        self._screen.blit(text, (WIN_W // 2 - text.get_width() // 2,
                                 WIN_H - BOT_H + (BOT_H - text.get_height()) // 2))

    def quit(self):
        pygame.quit()
