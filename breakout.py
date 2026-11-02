import random
import tkinter as tk


class BreakoutGame:
    WIDTH = 800
    HEIGHT = 600
    PADDLE_WIDTH = 110
    PADDLE_HEIGHT = 16
    BALL_SIZE = 16
    ROWS = 6
    COLUMNS = 10
    BLOCK_WIDTH = 68
    BLOCK_HEIGHT = 24
    BLOCK_GAP = 8

    BLOCK_COLORS = [
        "#ff6b6b",
        "#ff9f43",
        "#ffd166",
        "#06d6a0",
        "#4dabf7",
        "#9b5de5",
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Block Breaker")
        self.root.resizable(False, False)
        self.root.configure(bg="#111827")

        self.score = 0
        self.lives = 3
        self.level = 1
        self.running = False
        self.paused = False
        self.game_over = False
        self.keys = set()

        self.info = tk.Frame(root, bg="#111827", height=54)
        self.info.pack(fill="x")

        self.score_label = tk.Label(
            self.info,
            text="SCORE 00000",
            font=("Segoe UI", 12, "bold"),
            fg="#f8fafc",
            bg="#111827",
        )
        self.score_label.pack(side="left", padx=18, pady=14)

        self.status_label = tk.Label(
            self.info,
            text="SPACE TO START",
            font=("Segoe UI", 11, "bold"),
            fg="#ffd166",
            bg="#111827",
        )
        self.status_label.pack(side="left", expand=True)

        self.lives_label = tk.Label(
            self.info,
            text="LIVES 3",
            font=("Segoe UI", 12, "bold"),
            fg="#f8fafc",
            bg="#111827",
        )
        self.lives_label.pack(side="right", padx=18, pady=14)

        self.canvas = tk.Canvas(
            root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#0b1220",
            highlightthickness=0,
        )
        self.canvas.pack(padx=12, pady=(0, 12))

        self.blocks = {}
        self.paddle = None
        self.ball = None
        self.ball_dx = 0
        self.ball_dy = 0

        self.build_level()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.focus_force()
        self.game_loop()

    def build_level(self):
        self.canvas.delete("all")
        self.blocks.clear()

        left = (self.WIDTH - (
            self.COLUMNS * self.BLOCK_WIDTH
            + (self.COLUMNS - 1) * self.BLOCK_GAP
        )) / 2
        top = 52

        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                x1 = left + column * (self.BLOCK_WIDTH + self.BLOCK_GAP)
                y1 = top + row * (self.BLOCK_HEIGHT + self.BLOCK_GAP)
                block = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x1 + self.BLOCK_WIDTH,
                    y1 + self.BLOCK_HEIGHT,
                    fill=self.BLOCK_COLORS[row],
                    outline="#ffffff",
                    width=1,
                    tags="block",
                )
                self.blocks[block] = row

        paddle_x = self.WIDTH / 2
        paddle_y = self.HEIGHT - 42
        self.paddle = self.canvas.create_rectangle(
            paddle_x - self.PADDLE_WIDTH / 2,
            paddle_y - self.PADDLE_HEIGHT / 2,
            paddle_x + self.PADDLE_WIDTH / 2,
            paddle_y + self.PADDLE_HEIGHT / 2,
            fill="#f8fafc",
            outline="",
            tags="paddle",
        )
        self.reset_ball()

    def reset_ball(self):
        paddle_coords = self.canvas.coords(self.paddle)
        paddle_center = (paddle_coords[0] + paddle_coords[2]) / 2
        paddle_top = paddle_coords[1]
        ball_x = paddle_center - self.BALL_SIZE / 2
        ball_y = paddle_top - self.BALL_SIZE - 4
        self.ball = self.canvas.create_oval(
            ball_x,
            ball_y,
            ball_x + self.BALL_SIZE,
            ball_y + self.BALL_SIZE,
            fill="#ffffff",
            outline="#bde0fe",
            width=2,
            tags="ball",
        )
        self.ball_dx = random.choice([-4, -3, 3, 4])
        self.ball_dy = -4

    def on_key_press(self, event):
        key = event.keysym.lower()
        self.keys.add(key)

        if key == "space":
            if self.game_over:
                self.restart()
            elif not self.running:
                self.running = True
                self.status_label.configure(text="PLAYING")
            else:
                self.paused = not self.paused
                self.status_label.configure(
                    text="PAUSED" if self.paused else "PLAYING"
                )
        elif key == "r":
            self.restart()

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def move_paddle(self):
        direction = 0
        if "left" in self.keys or "a" in self.keys:
            direction -= 1
        if "right" in self.keys or "d" in self.keys:
            direction += 1

        if direction == 0:
            return

        x1, _, x2, _ = self.canvas.coords(self.paddle)
        movement = direction * 8
        if x1 + movement < 0:
            movement = -x1
        elif x2 + movement > self.WIDTH:
            movement = self.WIDTH - x2
        self.canvas.move(self.paddle, movement, 0)

    def move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        ball = self.canvas.coords(self.ball)
        x1, y1, x2, y2 = ball

        if x1 <= 0 or x2 >= self.WIDTH:
            self.ball_dx *= -1
            self.canvas.move(self.ball, self.ball_dx, 0)
        if y1 <= 0:
            self.ball_dy = abs(self.ball_dy)
            self.canvas.move(self.ball, 0, self.ball_dy)

        if self.ball_hits(self.paddle) and self.ball_dy > 0:
            paddle = self.canvas.coords(self.paddle)
            paddle_center = (paddle[0] + paddle[2]) / 2
            ball_center = (x1 + x2) / 2
            offset = (ball_center - paddle_center) / (self.PADDLE_WIDTH / 2)
            self.ball_dx = max(-6, min(6, offset * 6))
            if abs(self.ball_dx) < 1.2:
                self.ball_dx = 1.2 if self.ball_dx >= 0 else -1.2
            self.ball_dy = -abs(self.ball_dy)
            self.canvas.move(self.ball, 0, -abs(self.ball_dy))

        hit_block = self.find_hit_block()
        if hit_block is not None:
            self.canvas.delete(hit_block)
            del self.blocks[hit_block]
            self.score += 10
            self.update_labels()
            self.ball_dy *= -1

            if not self.blocks:
                self.level += 1
                self.ROWS = min(8, self.ROWS + 1)
                self.build_level()
                self.status_label.configure(text=f"LEVEL {self.level}")

        if y2 >= self.HEIGHT:
            self.lose_life()

    def ball_hits(self, item):
        ball = self.canvas.coords(self.ball)
        target = self.canvas.coords(item)
        return (
            ball[2] >= target[0]
            and ball[0] <= target[2]
            and ball[3] >= target[1]
            and ball[1] <= target[3]
        )

    def find_hit_block(self):
        ball = self.canvas.coords(self.ball)
        for block in list(self.blocks):
            target = self.canvas.coords(block)
            if (
                ball[2] >= target[0]
                and ball[0] <= target[2]
                and ball[3] >= target[1]
                and ball[1] <= target[3]
            ):
                return block
        return None

    def lose_life(self):
        self.lives -= 1
        self.update_labels()
        if self.lives <= 0:
            self.game_over = True
            self.running = False
            self.status_label.configure(text="GAME OVER - SPACE TO RESTART")
            self.canvas.create_text(
                self.WIDTH / 2,
                self.HEIGHT / 2,
                text="GAME OVER",
                fill="#ff6b6b",
                font=("Segoe UI", 32, "bold"),
                tags="message",
            )
            return

        self.running = False
        self.canvas.delete(self.ball)
        self.reset_ball()
        self.status_label.configure(text="LIFE LOST - SPACE TO CONTINUE")

    def update_labels(self):
        self.score_label.configure(text=f"SCORE {self.score:05d}")
        self.lives_label.configure(text=f"LIVES {self.lives}")

    def restart(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.ROWS = 6
        self.running = False
        self.paused = False
        self.game_over = False
        self.update_labels()
        self.build_level()
        self.status_label.configure(text="SPACE TO START")

    def game_loop(self):
        self.move_paddle()
        if self.running and not self.paused and not self.game_over:
            self.move_ball()
        self.root.after(16, self.game_loop)


def main():
    root = tk.Tk()
    BreakoutGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()