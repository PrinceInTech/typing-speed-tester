"""
Snake Game
===========
Built with Python + Pygame

Features:
  • Smooth snake movement with keyboard controls
  • Random food generation
  • Score & High Score tracking
  • Increasing speed per level
  • Wall & self-collision detection
  • Particle effect when eating food
  • Game Over screen with restart
  • Beautiful dark neon theme
"""

import pygame
import random
import sys
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ─────────────────────────── Constants ───────────────────────────

CELL        = 22          # grid cell size in pixels
COLS        = 28          # number of columns
ROWS        = 24          # number of rows
PANEL_H     = 72          # top score panel height
WIDTH       = COLS * CELL
HEIGHT      = ROWS * CELL + PANEL_H
FPS         = 60

# Colors
BG          = (10,  12,  20)
GRID_COL    = (18,  22,  35)
PANEL_COL   = (16,  18,  30)
BORDER_COL  = (46,  51,  80)

SNAKE_HEAD  = (124, 111, 247)   # purple
SNAKE_BODY  = (78,  205, 196)   # teal
SNAKE_EYE   = (255, 255, 255)

FOOD_COL    = (255, 80,  80)    # red
FOOD_GLOW   = (255, 140, 100)

SCORE_COL   = (232, 234, 246)
ACCENT      = (124, 111, 247)
ACCENT2     = (78,  205, 196)
DIM         = (139, 144, 184)

# Directions
UP    = (0, -1)
DOWN  = (0,  1)
LEFT  = (-1, 0)
RIGHT = (1,  0)

OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "highscore.txt")


# ─────────────────────────── Particles ───────────────────────────

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float = 1.0
    color: Tuple = (255, 200, 100)

    def update(self, dt: float):
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vy += 200 * dt   # gravity
        self.life -= dt * 2.5

    @property
    def alive(self): return self.life > 0


def spawn_particles(cx: int, cy: int) -> List[Particle]:
    parts = []
    for _ in range(12):
        angle = random.uniform(0, 6.28)
        speed = random.uniform(60, 180)
        col   = random.choice([FOOD_COL, FOOD_GLOW, SNAKE_BODY, (255,255,180)])
        parts.append(Particle(
            cx, cy,
            speed * __import__('math').cos(angle),
            speed * __import__('math').sin(angle),
            color=col
        ))
    return parts


# ─────────────────────────── High Score ──────────────────────────

def load_high_score() -> int:
    try:
        with open(HIGH_SCORE_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_high_score(score: int):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))
    except Exception:
        pass


# ─────────────────────────── Game Logic ──────────────────────────

class SnakeGame:
    def __init__(self):
        self.high_score = load_high_score()
        self.reset()

    def reset(self):
        # Start snake in middle, 3 cells long, moving right
        cx, cy = COLS // 2, ROWS // 2
        self.snake: List[Tuple[int,int]] = [(cx-i, cy) for i in range(3)]
        self.direction = RIGHT
        self.next_dir  = RIGHT
        self.score     = 0
        self.level     = 1
        self.food      = self._place_food()
        self.alive     = True
        self.move_timer = 0.0
        self.move_interval = 0.14   # seconds per step
        self.particles: List[Particle] = []
        self.food_pulse = 0.0       # for pulsing food animation

    def _place_food(self) -> Tuple[int,int]:
        snake_set = set(self.snake)
        while True:
            pos = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
            if pos not in snake_set:
                return pos

    def set_direction(self, new_dir: Tuple[int,int]):
        if new_dir != OPPOSITE.get(self.direction):
            self.next_dir = new_dir

    def update(self, dt: float):
        if not self.alive:
            return

        self.food_pulse += dt * 4
        self.move_timer += dt

        # Update particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

        if self.move_timer < self.move_interval:
            return

        self.move_timer -= self.move_interval
        self.direction = self.next_dir

        # Move snake
        hx, hy = self.snake[0]
        dx, dy  = self.direction
        new_head = (hx + dx, hy + dy)

        # Wall collision
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            self.alive = False
            self._update_high_score()
            return

        # Self collision (skip tail tip since it moves)
        if new_head in set(self.snake[:-1]):
            self.alive = False
            self._update_high_score()
            return

        self.snake.insert(0, new_head)

        # Food eaten
        if new_head == self.food:
            self.score += 10 * self.level
            self.food   = self._place_food()
            # Spawn particles at food center
            fx = self.food[0] * CELL + CELL//2
            fy = self.food[1] * CELL + CELL//2 + PANEL_H
            self.particles += spawn_particles(fx, fy)
            # Level up every 5 foods
            foods_eaten = len(self.snake) - 2   # started at 3
            if foods_eaten % 5 == 0:
                self.level += 1
                self.move_interval = max(0.06, self.move_interval - 0.01)
        else:
            self.snake.pop()

    def _update_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)


# ─────────────────────────── Renderer ────────────────────────────

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_lg  = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_md  = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_sm  = pygame.font.SysFont("Arial", 14)
        self.font_xl  = pygame.font.SysFont("Arial", 52, bold=True)

    def draw_grid(self):
        self.screen.fill(BG)
        # Panel background
        pygame.draw.rect(self.screen, PANEL_COL, (0, 0, WIDTH, PANEL_H))
        pygame.draw.line(self.screen, BORDER_COL, (0, PANEL_H), (WIDTH, PANEL_H), 2)
        # Grid dots
        for r in range(ROWS+1):
            for c in range(COLS+1):
                x = c * CELL
                y = r * CELL + PANEL_H
                pygame.draw.circle(self.screen, GRID_COL, (x, y), 1)

    def draw_panel(self, game: SnakeGame):
        # Score
        self._text(f"SCORE", WIDTH//4, 14, self.font_sm, DIM, center=True)
        self._text(f"{game.score}", WIDTH//4, 32, self.font_lg, SCORE_COL, center=True)
        # High score
        self._text("BEST", WIDTH//2, 14, self.font_sm, DIM, center=True)
        self._text(f"{game.high_score}", WIDTH//2, 32, self.font_lg, ACCENT2, center=True)
        # Level
        self._text("LEVEL", 3*WIDTH//4, 14, self.font_sm, DIM, center=True)
        self._text(f"{game.level}", 3*WIDTH//4, 32, self.font_lg, ACCENT, center=True)
        # Length
        self._text("LENGTH", WIDTH-60, 14, self.font_sm, DIM, center=True)
        self._text(f"{len(game.snake)}", WIDTH-60, 32, self.font_md, DIM, center=True)

    def draw_snake(self, snake: List[Tuple[int,int]]):
        for i, (gx, gy) in enumerate(snake):
            x = gx * CELL
            y = gy * CELL + PANEL_H
            pad = 2 if i > 0 else 1
            rect = pygame.Rect(x+pad, y+pad, CELL-pad*2, CELL-pad*2)
            col  = SNAKE_HEAD if i == 0 else SNAKE_BODY
            # Gradient fade for tail
            if i > 0:
                fade = max(0.3, 1 - i / len(snake))
                col  = tuple(int(c * fade) for c in SNAKE_BODY)
            pygame.draw.rect(self.screen, col, rect, border_radius=5)

            # Eyes on head
            if i == 0:
                ex1, ex2 = x + 6,  x + CELL - 8
                ey       = y + 7
                pygame.draw.circle(self.screen, SNAKE_EYE, (ex1, ey), 3)
                pygame.draw.circle(self.screen, SNAKE_EYE, (ex2, ey), 3)
                pygame.draw.circle(self.screen, BG,        (ex1, ey), 1)
                pygame.draw.circle(self.screen, BG,        (ex2, ey), 1)

    def draw_food(self, food: Tuple[int,int], pulse: float):
        import math
        gx, gy = food
        cx = gx * CELL + CELL//2
        cy = gy * CELL + CELL//2 + PANEL_H
        radius = int(CELL//2 - 2 + math.sin(pulse) * 2)
        # Glow
        glow_surf = pygame.Surface((CELL*3, CELL*3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*FOOD_GLOW, 40),
                           (CELL*3//2, CELL*3//2), radius+6)
        self.screen.blit(glow_surf, (cx - CELL*3//2, cy - CELL*3//2))
        # Food circle
        pygame.draw.circle(self.screen, FOOD_COL, (cx, cy), radius)
        pygame.draw.circle(self.screen, FOOD_GLOW, (cx-2, cy-2), radius//3)

    def draw_particles(self, particles: List[Particle]):
        for p in particles:
            alpha = int(p.life * 255)
            r = max(2, int(4 * p.life))
            col = tuple(min(255, c) for c in p.color)
            pygame.draw.circle(self.screen, col, (int(p.x), int(p.y)), r)

    def draw_game_over(self, game: SnakeGame):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Box
        bw, bh = 360, 260
        bx, by = (WIDTH - bw)//2, (HEIGHT - bh)//2
        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        box.fill((22, 26, 42, 240))
        self.screen.blit(box, (bx, by))
        pygame.draw.rect(self.screen, ACCENT, (bx, by, bw, bh), 2, border_radius=12)

        # Text
        new_best = game.score >= game.high_score and game.score > 0
        self._text("GAME OVER", WIDTH//2, by+28, self.font_xl, FOOD_COL, center=True)
        self._text(f"Score: {game.score}", WIDTH//2, by+100, self.font_lg, SCORE_COL, center=True)
        if new_best:
            self._text("🏆 NEW HIGH SCORE!", WIDTH//2, by+136, self.font_md, ACCENT2, center=True)
        self._text(f"Best: {game.high_score}", WIDTH//2, by+158, self.font_md, DIM, center=True)

        # Buttons hint
        pygame.draw.rect(self.screen, ACCENT, (bx+60, by+196, 100, 38), border_radius=8)
        pygame.draw.rect(self.screen, BORDER_COL, (bx+200, by+196, 100, 38), border_radius=8)
        self._text("R  Restart", bx+110, by+208, self.font_sm, (255,255,255), center=True)
        self._text("Q  Quit",    bx+250, by+208, self.font_sm, DIM, center=True)

    def draw_start_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        self._text("🐍  SNAKE", WIDTH//2, HEIGHT//2 - 80, self.font_xl, ACCENT, center=True)
        self._text("Use Arrow Keys or WASD to move", WIDTH//2, HEIGHT//2, self.font_md, DIM, center=True)
        self._text("Eat food to grow and earn points!", WIDTH//2, HEIGHT//2+30, self.font_sm, DIM, center=True)

        pygame.draw.rect(self.screen, ACCENT,
                         (WIDTH//2-90, HEIGHT//2+70, 180, 44), border_radius=10)
        self._text("Press SPACE to Start", WIDTH//2, HEIGHT//2+80,
                   self.font_md, (255,255,255), center=True)

    def _text(self, txt, x, y, font, color, center=False):
        surf = font.render(str(txt), True, color)
        rect = surf.get_rect()
        if center:
            rect.centerx = x
            rect.top = y
        else:
            rect.left = x
            rect.top  = y
        self.screen.blit(surf, rect)


# ─────────────────────────── Main Loop ───────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Snake Game 🐍")

    screen   = pygame.display.set_mode((WIDTH, HEIGHT))
    clock    = pygame.time.Clock()
    renderer = Renderer(screen)
    game     = SnakeGame()

    STATE_START    = "start"
    STATE_PLAYING  = "playing"
    STATE_GAMEOVER = "gameover"
    state = STATE_START

    while True:
        dt = clock.tick(FPS) / 1000.0

        # ── Events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key

                if state == STATE_START:
                    if key == pygame.K_SPACE:
                        state = STATE_PLAYING

                elif state == STATE_PLAYING:
                    if key in (pygame.K_UP,    pygame.K_w): game.set_direction(UP)
                    if key in (pygame.K_DOWN,  pygame.K_s): game.set_direction(DOWN)
                    if key in (pygame.K_LEFT,  pygame.K_a): game.set_direction(LEFT)
                    if key in (pygame.K_RIGHT, pygame.K_d): game.set_direction(RIGHT)
                    if key == pygame.K_p:                    # pause placeholder
                        pass

                elif state == STATE_GAMEOVER:
                    if key in (pygame.K_r, pygame.K_SPACE):
                        game.reset()
                        state = STATE_PLAYING
                    if key == pygame.K_q:
                        pygame.quit()
                        sys.exit()

        # ── Update ──
        if state == STATE_PLAYING:
            game.update(dt)
            if not game.alive:
                state = STATE_GAMEOVER

        # ── Draw ──
        renderer.draw_grid()
        renderer.draw_panel(game)
        renderer.draw_food(game.food, game.food_pulse)
        renderer.draw_snake(game.snake)
        renderer.draw_particles(game.particles)

        if state == STATE_START:
            renderer.draw_start_screen()
        elif state == STATE_GAMEOVER:
            renderer.draw_game_over(game)

        pygame.display.flip()


if __name__ == "__main__":
    main()
