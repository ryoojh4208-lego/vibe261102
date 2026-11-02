"""뱀게임 (tkinter 사용 - 별도 설치 불필요)

조작: 방향키 또는 WASD로 이동, 스페이스바로 일시정지, R로 재시작
"""
import random
import tkinter as tk

CELL = 20          # 한 칸 크기(px)
COLS = 30          # 가로 칸 수
ROWS = 20          # 세로 칸 수
SPEED = 100        # 이동 간격(ms), 작을수록 빠름

DIRECTIONS = {
    "Up": (0, -1), "w": (0, -1),
    "Down": (0, 1), "s": (0, 1),
    "Left": (-1, 0), "a": (-1, 0),
    "Right": (1, 0), "d": (1, 0),
}


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("뱀게임")
        self.root.resizable(False, False)

        self.score_label = tk.Label(root, font=("맑은 고딕", 14))
        self.score_label.pack()

        self.canvas = tk.Canvas(
            root, width=COLS * CELL, height=ROWS * CELL,
            bg="black", highlightthickness=0,
        )
        self.canvas.pack()

        root.bind("<Key>", self.on_key)
        self.after_id = None
        self.reset()

    def reset(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.paused = False
        self.game_over = False
        self.place_food()
        self.update_score()
        self.tick()

    def place_food(self):
        empty = [(x, y) for x in range(COLS) for y in range(ROWS)
                 if (x, y) not in self.snake]
        self.food = random.choice(empty) if empty else None

    def on_key(self, event):
        key = event.keysym
        if key in ("r", "R"):
            self.reset()
            return
        if key == "space" and not self.game_over:
            self.paused = not self.paused
            self.draw()
            return
        new_dir = DIRECTIONS.get(key) or DIRECTIONS.get(key.lower())
        if new_dir:
            # 반대 방향으로는 바로 꺾을 수 없음
            dx, dy = self.direction
            if (new_dir[0], new_dir[1]) != (-dx, -dy):
                self.next_direction = new_dir

    def tick(self):
        if not self.paused and not self.game_over:
            self.step()
        self.draw()
        if not self.game_over:
            self.after_id = self.root.after(SPEED, self.tick)

    def step(self):
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # 벽 또는 자기 몸에 부딪히면 게임 오버 (꼬리는 이번에 빠지므로 제외)
        x, y = new_head
        body = self.snake[:-1] if new_head != self.food else self.snake
        if not (0 <= x < COLS and 0 <= y < ROWS) or new_head in body:
            self.game_over = True
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.update_score()
            self.place_food()
            if self.food is None:   # 화면을 꽉 채우면 승리
                self.game_over = True
        else:
            self.snake.pop()

    def update_score(self):
        self.score_label.config(text=f"점수: {self.score}")

    def draw(self):
        c = self.canvas
        c.delete("all")

        if self.food:
            fx, fy = self.food
            c.create_oval(fx * CELL + 2, fy * CELL + 2,
                          (fx + 1) * CELL - 2, (fy + 1) * CELL - 2,
                          fill="red", outline="")

        for i, (x, y) in enumerate(self.snake):
            color = "#7CFC00" if i == 0 else "#32CD32"
            c.create_rectangle(x * CELL + 1, y * CELL + 1,
                               (x + 1) * CELL - 1, (y + 1) * CELL - 1,
                               fill=color, outline="")

        w, h = COLS * CELL, ROWS * CELL
        if self.game_over:
            msg = "승리!" if self.food is None else "게임 오버"
            c.create_text(w / 2, h / 2 - 15, text=msg,
                          fill="white", font=("맑은 고딕", 28, "bold"))
            c.create_text(w / 2, h / 2 + 25, text="R 키를 눌러 다시 시작",
                          fill="white", font=("맑은 고딕", 14))
        elif self.paused:
            c.create_text(w / 2, h / 2, text="일시정지",
                          fill="white", font=("맑은 고딕", 24, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()
