import flet as ft
import flet.canvas as cv
import random
import asyncio
from enum import Enum
from dataclasses import dataclass
from typing import Optional

GRID_ROWS = 20
MIN_COLS = 20
MIN_CELL = 18
GAME_SPEED = 0.15
SIDE_PANEL_W = 280
HEADER_H = 70
FOOTER_H = 40

FONT_TITLE = "Creepster"
FONT_TITLE_PATH = "fonts/Creepster-Regular.ttf"
FONT_MONO = "Courier New"

COLOR_BG         = "#1a1a2e"
COLOR_GRID_LINE  = "#16213e"
COLOR_SNAKE_HEAD = "#e94560"
COLOR_SNAKE_BODY = "#0f3460"
COLOR_SNAKE_GLOW = "#533483"
COLOR_FOOD       = "#f5c518"
COLOR_FOOD_GLOW  = "#ff6b35"
COLOR_TEXT        = "#eaeaea"
COLOR_ACCENT     = "#e94560"
COLOR_PANEL      = "#16213e"
COLOR_SURFACE    = "#0f3460"


class Direction(Enum):
    UP    = (0, -1)
    DOWN  = (0,  1)
    LEFT  = (-1, 0)
    RIGHT = ( 1, 0)

class GameState(Enum):
    MENU      = "menu"
    PLAYING   = "playing"
    PAUSED    = "paused"
    GAME_OVER = "game_over"

@dataclass
class Point:
    x: int
    y: int


class SnakeGame:
    def __init__(self, cols=20, rows=20):
        self.cols = cols
        self.rows = rows
        self.reset()

    def resize_grid(self, cols, rows):
        was_playing = self.state == GameState.PLAYING
        self.cols = cols
        self.rows = rows
        if not was_playing:
            self.reset()

    def reset(self):
        mid_x, mid_y = self.cols // 2, self.rows // 2
        self.snake: list[Point] = [
            Point(mid_x, mid_y),
            Point(mid_x - 1, mid_y),
            Point(mid_x - 2, mid_y),
        ]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.food: Point = self._spawn_food()
        self.score: int = 0
        self.high_score: int = getattr(self, "high_score", 0)
        self.state = GameState.MENU
        self.moves: int = 0

    def _spawn_food(self) -> Point:
        occupied = {(p.x, p.y) for p in self.snake}
        while True:
            p = Point(random.randint(0, self.cols - 1),
                      random.randint(0, self.rows - 1))
            if (p.x, p.y) not in occupied:
                return p

    def set_direction(self, direction: Direction):
        opposites = {
            Direction.UP: Direction.DOWN, Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT, Direction.RIGHT: Direction.LEFT,
        }
        if direction != opposites.get(self.direction):
            self.next_direction = direction

    def tick(self) -> bool:
        if self.state != GameState.PLAYING:
            return False
        self.direction = self.next_direction
        dx, dy = self.direction.value
        head = self.snake[0]
        new_head = Point(head.x + dx, head.y + dy)

        if not (0 <= new_head.x < self.cols and 0 <= new_head.y < self.rows):
            self._game_over()
            return False
        if any(p.x == new_head.x and p.y == new_head.y for p in self.snake):
            self._game_over()
            return False

        self.snake.insert(0, new_head)
        self.moves += 1
        if new_head.x == self.food.x and new_head.y == self.food.y:
            self.score += 10
            self.food = self._spawn_food()
        else:
            self.snake.pop()
        return True

    def _game_over(self):
        self.state = GameState.GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score


DIRECTION_LABELS = {
    Direction.UP: "W → UP", Direction.DOWN: "S → DOWN",
    Direction.LEFT: "A → LEFT", Direction.RIGHT: "D → RIGHT",
}


class GameUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.game = SnakeGame()
        self._loop_running = False
        self._last_voice_cmd: Optional[str] = None
        self.cell_size = 30
        self.grid_cols = MIN_COLS
        self.grid_rows = GRID_ROWS
        self.canvas_w = self.grid_cols * self.cell_size
        self.canvas_h = self.grid_rows * self.cell_size
        self._setup_page()
        self._build_ui()
        self.page.update()
        self.page.run_task(self._delayed_resize)

    async def _delayed_resize(self):
        for _ in range(5):
            await asyncio.sleep(0.3)
            self._recalc_sizes()

    def _setup_page(self):
        self.page.title = "Chamber of Echoes"
        self.page.bgcolor = COLOR_BG
        self.page.padding = 0
        self.page.spacing = 0
        self.page.window.full_screen = True
        self.page.fonts = {FONT_TITLE: FONT_TITLE_PATH}
        self.page.on_keyboard_event = self._on_key
        self.page.on_resized = self._on_resize

    def _recalc_sizes(self):
        pw = self.page.window.width or self.page.width or 1920
        ph = self.page.window.height or self.page.height or 1080
        avail_w = pw - SIDE_PANEL_W - 16
        avail_h = ph - HEADER_H - FOOTER_H - 60

        self.cell_size = max(MIN_CELL, int(avail_h / GRID_ROWS))
        self.grid_cols = max(MIN_COLS, int(avail_w / self.cell_size))
        self.grid_rows = GRID_ROWS
        self.canvas_w = self.grid_cols * self.cell_size
        self.canvas_h = self.grid_rows * self.cell_size

        self.game.resize_grid(self.grid_cols, self.grid_rows)
        self.canvas.width = self.canvas_w
        self.canvas.height = self.canvas_h
        self.canvas_container.width = self.canvas_w
        self.canvas_container.height = self.canvas_h
        self._paint()
        self.page.update()

    def _on_resize(self, e):
        self._recalc_sizes()

    def _build_ui(self):
        self.canvas = cv.Canvas(width=self.canvas_w, height=self.canvas_h)
        self.canvas_container = ft.Container(
            content=self.canvas,
            width=self.canvas_w, height=self.canvas_h,
            border_radius=6,
            border=ft.Border.all(2, COLOR_ACCENT),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=12,
                                 color=ft.Colors.with_opacity(0.2, COLOR_ACCENT)),
        )

        self.score_text = ft.Text("0", size=42, weight=ft.FontWeight.BOLD,
                                  color=COLOR_FOOD, font_family=FONT_MONO)
        self.high_score_text = ft.Text("BEST: 0", size=14, color=COLOR_TEXT,
                                       font_family=FONT_MONO)
        self.moves_text = ft.Text("MOVES: 0", size=14, color=COLOR_TEXT,
                                   font_family=FONT_MONO)
        self.state_text = ft.Text("PRESS SPACE TO START", size=12,
                                   color=COLOR_ACCENT, weight=ft.FontWeight.BOLD,
                                   font_family=FONT_MONO)
        self.voice_label = ft.Text("VOICE: waiting...", size=12,
                                    color="#666", italic=True, font_family=FONT_MONO)
        self.voice_indicator = ft.Container(width=10, height=10, border_radius=5, bgcolor="#444")

        self.dir_indicators = {}
        for d in Direction:
            self.dir_indicators[d] = ft.Container(
                width=48, height=48, border_radius=8, bgcolor=COLOR_SURFACE,
                alignment=ft.Alignment(0, 0),
                content=ft.Text(
                    {"UP": "▲", "DOWN": "▼", "LEFT": "◄", "RIGHT": "►"}[d.name],
                    size=18, color="#555", weight=ft.FontWeight.BOLD),
            )

        dir_pad = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3,
            controls=[
                self.dir_indicators[Direction.UP],
                ft.Row(spacing=3, alignment=ft.MainAxisAlignment.CENTER, controls=[
                    self.dir_indicators[Direction.LEFT],
                    ft.Container(width=48, height=48),
                    self.dir_indicators[Direction.RIGHT],
                ]),
                self.dir_indicators[Direction.DOWN],
            ],
        )

        cmd_map = ft.Column(spacing=6, controls=[
            ft.Text("COMMANDS", size=15, color=COLOR_ACCENT,
                     weight=ft.FontWeight.BOLD, font_family=FONT_MONO),
            *[ft.Text(label, size=14, color=COLOR_TEXT, font_family=FONT_MONO)
              for label in DIRECTION_LABELS.values()],
        ])

        header = ft.Container(
            height=HEADER_H, bgcolor="#0a0a1a",
            border=ft.Border(bottom=ft.BorderSide(1, COLOR_SURFACE)),
            padding=ft.Padding.symmetric(horizontal=30),
            alignment=ft.Alignment(0, 0),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("Chamber ", size=34, color=COLOR_ACCENT,
                             font_family=FONT_TITLE, weight=ft.FontWeight.BOLD),
                    ft.Text(" of ", size=34, color=COLOR_TEXT,
                             font_family=FONT_TITLE, weight=ft.FontWeight.BOLD),
                    ft.Text(" Echoes", size=34, color=COLOR_FOOD,
                             font_family=FONT_TITLE, weight=ft.FontWeight.BOLD),
                ],
            ),
        )

        footer = ft.Container(
            height=FOOTER_H, bgcolor="#0a0a1a",
            border=ft.Border(top=ft.BorderSide(1, COLOR_SURFACE)),
            padding=ft.Padding.symmetric(horizontal=30),
            alignment=ft.Alignment(0, 0),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Developer: Kumar Anurag", size=13,
                             color="#ffffff", font_family=FONT_MONO),
                    ft.Text("Controls: WASD / Arrow Keys", size=13,
                             color="#ffffff", font_family=FONT_MONO),
                ],
            ),
        )

        game_area = ft.Container(
            expand=True, bgcolor=COLOR_BG,
            alignment=ft.Alignment(0, 0),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=self.canvas_container,
        )

        left_section = ft.Column(expand=True, spacing=0,
                                  controls=[header, game_area, footer])

        side_panel = ft.Container(
            width=SIDE_PANEL_W, bgcolor=COLOR_PANEL, padding=20,
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                spacing=18,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("TALK TO SNAKE", size=22, weight=ft.FontWeight.BOLD,
                             color=COLOR_ACCENT, font_family=FONT_MONO),
                    ft.Divider(height=1, color=COLOR_SURFACE),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
                        controls=[
                            ft.Text("SCORE", size=11, color="#888", font_family=FONT_MONO),
                            self.score_text, self.high_score_text, self.moves_text,
                        ],
                    ),
                    ft.Divider(height=1, color=COLOR_SURFACE),
                    dir_pad,
                    ft.Divider(height=1, color=COLOR_SURFACE),
                    ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=6,
                           controls=[self.voice_indicator, self.voice_label]),
                    cmd_map,
                    ft.Divider(height=1, color=COLOR_SURFACE),
                    self.state_text,
                ],
            ),
        )

        self.page.add(ft.Row(expand=True, spacing=0, 
                              controls=[left_section, side_panel]))
        self._paint()

    def _paint(self):
        cs = self.cell_size
        cw, ch = self.canvas_w, self.canvas_h
        gc, gr = self.grid_cols, self.grid_rows
        shapes = []

        shapes.append(cv.Rect(0, 0, cw, ch,
                      paint=ft.Paint(color=COLOR_BG, style=ft.PaintingStyle.FILL)))

        grid_paint = ft.Paint(color=COLOR_GRID_LINE, stroke_width=0.5,
                               style=ft.PaintingStyle.STROKE)
        for c in range(gc + 1):
            x = c * cs
            shapes.append(cv.Line(x, 0, x, ch, paint=grid_paint))
        for r in range(gr + 1):
            y = r * cs
            shapes.append(cv.Line(0, y, cw, y, paint=grid_paint))

        fx = self.game.food.x * cs + cs // 2
        fy = self.game.food.y * cs + cs // 2
        shapes.append(cv.Circle(fx, fy, cs * 0.7,
                      paint=ft.Paint(color=ft.Colors.with_opacity(0.15, COLOR_FOOD_GLOW),
                                      style=ft.PaintingStyle.FILL)))
        pad = max(2, cs // 7)
        shapes.append(cv.Rect(
            self.game.food.x * cs + pad, self.game.food.y * cs + pad,
            cs - 2 * pad, cs - 2 * pad,
            border_radius=ft.BorderRadius(4, 4, 4, 4),
            paint=ft.Paint(color=COLOR_FOOD, style=ft.PaintingStyle.FILL),
        ))

        for i, seg in enumerate(reversed(self.game.snake)):
            idx = len(self.game.snake) - 1 - i
            if idx == 0:
                gx = seg.x * cs + cs // 2
                gy = seg.y * cs + cs // 2
                shapes.append(cv.Circle(gx, gy, cs * 0.8,
                              paint=ft.Paint(color=ft.Colors.with_opacity(0.2, COLOR_SNAKE_HEAD),
                                              style=ft.PaintingStyle.FILL)))
                hp = max(1, cs // 14)
                shapes.append(cv.Rect(
                    seg.x * cs + hp, seg.y * cs + hp, cs - 2 * hp, cs - 2 * hp,
                    border_radius=ft.BorderRadius(6, 6, 6, 6),
                    paint=ft.Paint(color=COLOR_SNAKE_HEAD, style=ft.PaintingStyle.FILL),
                ))
                dx, dy = self.game.direction.value
                cx, cy = seg.x * cs + cs // 2, seg.y * cs + cs // 2
                eo, er, ed = max(3, cs // 6), max(2, cs // 10), max(2, cs // 7)
                if dx != 0:
                    shapes.append(cv.Circle(cx + dx * ed, cy - eo, er,
                                  paint=ft.Paint(color="#fff", style=ft.PaintingStyle.FILL)))
                    shapes.append(cv.Circle(cx + dx * ed, cy + eo, er,
                                  paint=ft.Paint(color="#fff", style=ft.PaintingStyle.FILL)))
                else:
                    shapes.append(cv.Circle(cx - eo, cy + dy * ed, er,
                                  paint=ft.Paint(color="#fff", style=ft.PaintingStyle.FILL)))
                    shapes.append(cv.Circle(cx + eo, cy + dy * ed, er,
                                  paint=ft.Paint(color="#fff", style=ft.PaintingStyle.FILL)))
            else:
                t = idx / max(len(self.game.snake) - 1, 1)
                bp = max(2, int(cs * 0.1) + int(t * cs * 0.08))
                shapes.append(cv.Rect(
                    seg.x * cs + bp, seg.y * cs + bp, cs - 2 * bp, cs - 2 * bp,
                    border_radius=ft.BorderRadius(4, 4, 4, 4),
                    paint=ft.Paint(
                        color=COLOR_SNAKE_GLOW if idx % 2 == 0 else COLOR_SNAKE_BODY,
                        style=ft.PaintingStyle.FILL),
                ))

        if self.game.state == GameState.MENU:
            shapes += self._overlay("CHAMBER OF ECHOES", "Press SPACE to start",
                                     "WASD / Arrows")
        elif self.game.state == GameState.PAUSED:
            shapes += self._overlay("PAUSED", "Press SPACE to resume", "")
        elif self.game.state == GameState.GAME_OVER:
            shapes += self._overlay("GAME OVER", f"Score: {self.game.score}",
                                     "Press SPACE to restart")

        self.canvas.shapes = shapes
        self.canvas.update()

    def _overlay(self, title, sub1, sub2):
        cw, ch = self.canvas_w, self.canvas_h
        shapes = [
            cv.Rect(0, 0, cw, ch,
                     paint=ft.Paint(color=ft.Colors.with_opacity(0.8, "#000"),
                                     style=ft.PaintingStyle.FILL)),
            cv.Text(cw / 2 - len(title) * 9, ch / 2 - 50, title,
                     style=ft.TextStyle(size=38, color=COLOR_ACCENT,
                                         weight=ft.FontWeight.BOLD, font_family=FONT_MONO)),
            cv.Text(cw / 2 - len(sub1) * 5, ch / 2 + 10, sub1,
                     style=ft.TextStyle(size=16, color=COLOR_TEXT, font_family=FONT_MONO)),
        ]
        if sub2:
            shapes.append(cv.Text(
                cw / 2 - len(sub2) * 4.5, ch / 2 + 40, sub2,
                style=ft.TextStyle(size=14, color="#888", font_family=FONT_MONO)))
        return shapes

    def _update_panel(self):
        self.score_text.value = str(self.game.score)
        self.high_score_text.value = f"BEST: {self.game.high_score}"
        self.moves_text.value = f"MOVES: {self.game.moves}"
        states = {
            GameState.MENU: "PRESS SPACE TO START",
            GameState.PLAYING: "PLAYING...",
            GameState.PAUSED: "PAUSED",
            GameState.GAME_OVER: "GAME OVER — SPACE TO RETRY",
        }
        self.state_text.value = states[self.game.state]
        for d, container in self.dir_indicators.items():
            if d == self.game.direction and self.game.state == GameState.PLAYING:
                container.bgcolor = COLOR_ACCENT
                container.content.color = "#fff"
            else:
                container.bgcolor = COLOR_SURFACE
                container.content.color = "#555"
        self.page.update()

    def _on_key(self, e: ft.KeyboardEvent):
        key = e.key
        key_map = {
            "Arrow Up": Direction.UP, "Arrow Down": Direction.DOWN,
            "Arrow Left": Direction.LEFT, "Arrow Right": Direction.RIGHT,
            "W": Direction.UP, "S": Direction.DOWN,
            "A": Direction.LEFT, "D": Direction.RIGHT,
        }
        if key in key_map and self.game.state == GameState.PLAYING:
            self.game.set_direction(key_map[key])
            return
        if key == " ":
            if self.game.state == GameState.MENU:
                self.game.state = GameState.PLAYING
                self._start_loop()
            elif self.game.state == GameState.PLAYING:
                self.game.state = GameState.PAUSED
                self._paint()
                self._update_panel()
            elif self.game.state == GameState.PAUSED:
                self.game.state = GameState.PLAYING
                self._start_loop()
            elif self.game.state == GameState.GAME_OVER:
                self.game.reset()
                self.game.state = GameState.PLAYING
                self._start_loop()

    def voice_command(self, direction: Direction, label: str = ""):
        """Call from RC controller: game_ui.voice_command(Direction.UP, "8 → UP")"""
        if self.game.state == GameState.PLAYING:
            self.game.set_direction(direction)
            self._last_voice_cmd = label or direction.name
            self.voice_label.value = f"VOICE: {self._last_voice_cmd}"
            self.voice_indicator.bgcolor = COLOR_FOOD
            self.page.update()

    def _start_loop(self):
        if not self._loop_running:
            self._loop_running = True
            self.page.run_task(self._game_loop)

    async def _game_loop(self):
        while self.game.state == GameState.PLAYING:
            self.game.tick()
            self._paint()
            self._update_panel()
            await asyncio.sleep(GAME_SPEED)
        self._loop_running = False
        self._paint()
        self._update_panel()


def main(page: ft.Page):
    game_ui = GameUI(page)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")