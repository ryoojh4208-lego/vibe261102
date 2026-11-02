"""
SKY STRIKE - pygame 종스크롤 슈팅 게임

조작법
  방향키 / WASD : 이동
  Z / Space     : 사격 (누르고 있으면 연사)
  X             : 폭탄 (화면의 적 탄환 제거 + 전체 공격)
  Shift         : 저속 이동 (정밀 회피)
  P / Esc       : 일시정지
  Enter         : 시작 / 다시 시작

  P 아이템을 먹을 때마다 고구마 탄이 2 → 4 → 8 → 16발로 늘어난다.

실행: pip install pygame  →  python shooting.py
"""

import math
import random
import sys
from array import array

import pygame

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 480, 720
FPS = 60
SCROLL_SPEED = 1.5

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 220, 60)
RED = (240, 70, 70)
ORANGE = (255, 150, 40)
CYAN = (80, 220, 255)
GREEN = (90, 220, 120)
PURPLE = (190, 110, 255)
SEA = (22, 52, 96)
SEA_DARK = (16, 40, 78)
LAND = (64, 112, 60)
LAND_DARK = (46, 86, 44)
SAND = (186, 170, 112)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def angle_to(src, dst):
    return math.atan2(dst[1] - src[1], dst[0] - src[0])


# ---------------------------------------------------------------------------
# 효과음: 외부 파일 없이 코드로 직접 합성
# ---------------------------------------------------------------------------
class Sfx:
    def __init__(self):
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 256)
            self.rate, _, self.channels = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(24)
        except pygame.error:
            return  # 오디오 장치가 없으면 소리 없이 진행

        s = self.synth
        self.sounds = {
            "shoot": s([(1400, 700, 0.05, "square")], 0.08),
            "explode": s([(900, 120, 0.25, "noise")], 0.35),
            "big_explode": s([(500, 40, 0.9, "noise")], 0.6),
            "player_down": s([(700, 90, 0.5, "square"), (300, 30, 0.6, "noise")], 0.45),
            "powerup": s([(523, 523, 0.06, "tri"), (659, 659, 0.06, "tri"),
                          (784, 784, 0.06, "tri"), (1047, 1047, 0.16, "tri")], 0.5),
            "item": s([(880, 1320, 0.1, "tri")], 0.4),
            "bomb": s([(160, 25, 1.2, "noise")], 0.7),
            "warning": s([(440, 440, 0.18, "square"), (0, 0, 0.08, "square")] * 3, 0.25),
            "stage": s([(392, 392, 0.1, "tri"), (523, 523, 0.1, "tri"),
                        (659, 659, 0.1, "tri"), (784, 784, 0.3, "tri")], 0.5),
        }

    def synth(self, segments, volume):
        """segments: (시작 주파수, 끝 주파수, 길이(초), 파형) 목록을 이어 붙인다"""
        buf = array("h")
        for f0, f1, dur, wave in segments:
            n = int(self.rate * dur)
            phase, noise_val, last = 0.0, 0.0, -1
            for i in range(n):
                t = i / n
                f = f0 + (f1 - f0) * t
                phase += f / self.rate
                if f == 0:
                    v = 0.0
                elif wave == "square":
                    v = 1.0 if phase % 1 < 0.5 else -1.0
                elif wave == "tri":
                    v = 4 * abs(phase % 1 - 0.5) - 1
                else:  # noise: 주파수에 맞춰 값을 바꾸는 샘플 앤 홀드 노이즈
                    if int(phase) != last:
                        last = int(phase)
                        noise_val = random.uniform(-1, 1)
                    v = noise_val
                sample = int(v * (1 - t) ** 1.5 * volume * 32767)
                for _ in range(self.channels):
                    buf.append(sample)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        snd = self.sounds.get(name)
        if snd:
            snd.play()


# ---------------------------------------------------------------------------
# 배경: 바다 + 스크롤되는 섬
# ---------------------------------------------------------------------------
class Island:
    def __init__(self, y):
        self.x = random.randint(-40, WIDTH + 40)
        self.y = y
        self.radius = random.randint(50, 120)
        # 불규칙한 외곽선을 가진 다각형
        n = 14
        self.points = []
        for i in range(n):
            a = i / n * math.tau
            r = self.radius * random.uniform(0.7, 1.15)
            self.points.append((math.cos(a) * r, math.sin(a) * r * 0.8))

    def update(self):
        self.y += SCROLL_SPEED

    def draw(self, surf):
        sand = [(self.x + px * 1.08, self.y + py * 1.08) for px, py in self.points]
        land = [(self.x + px, self.y + py) for px, py in self.points]
        inner = [(self.x + px * 0.55, self.y + py * 0.55) for px, py in self.points]
        pygame.draw.polygon(surf, SAND, sand)
        pygame.draw.polygon(surf, LAND, land)
        pygame.draw.polygon(surf, LAND_DARK, inner)


class Background:
    def __init__(self):
        self.offset = 0
        self.islands = [Island(random.randint(-HEIGHT, HEIGHT)) for _ in range(4)]
        self.waves = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(60)]

    def update(self):
        self.offset = (self.offset + SCROLL_SPEED) % 40
        for isl in self.islands:
            isl.update()
        self.islands = [i for i in self.islands if i.y - i.radius < HEIGHT + 20]
        while len(self.islands) < 4:
            self.islands.append(Island(-random.randint(150, 500)))
        self.waves = [(x, (y + SCROLL_SPEED * 1.3) % HEIGHT) for x, y in self.waves]

    def draw(self, surf):
        surf.fill(SEA)
        for y in range(-40, HEIGHT, 40):
            pygame.draw.rect(surf, SEA_DARK, (0, y + self.offset, WIDTH, 20))
        for x, y in self.waves:
            pygame.draw.line(surf, (60, 100, 150), (x, y), (x + 8, y), 1)
        for isl in self.islands:
            isl.draw(surf)


# ---------------------------------------------------------------------------
# 이펙트
# ---------------------------------------------------------------------------
class Particle:
    def __init__(self, x, y, color, speed=4, life=30, size=3):
        a = random.uniform(0, math.tau)
        s = random.uniform(0.5, speed)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * s, math.sin(a) * s
        self.color = color
        self.life = self.max_life = random.randint(life // 2, life)
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surf):
        r = max(1, int(self.size * self.life / self.max_life))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


def explode(particles, x, y, big=False):
    count = 60 if big else 20
    for _ in range(count):
        color = random.choice((YELLOW, ORANGE, RED, WHITE))
        particles.append(Particle(x, y, color, speed=7 if big else 4,
                                  life=50 if big else 30, size=5 if big else 3))


# ---------------------------------------------------------------------------
# 탄환
# ---------------------------------------------------------------------------
class Bullet:
    def __init__(self, x, y, vx, vy, color, radius, damage=1):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.radius = radius
        self.damage = damage
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if not (-20 < self.x < WIDTH + 20 and -20 < self.y < HEIGHT + 20):
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), max(1, self.radius - 2))


class SweetPotato(Bullet):
    """플레이어 탄: 진행 방향으로 회전하는 고구마"""
    _sprite = None
    _rotated = {}

    def __init__(self, x, y, vx, vy):
        super().__init__(x, y, vx, vy, ORANGE, 4)
        deg = int(round(-(math.degrees(math.atan2(vy, vx)) + 90)))
        self.image = self.rotated(deg)

    @classmethod
    def base_sprite(cls):
        if cls._sprite is None:
            s = pygame.Surface((12, 26), pygame.SRCALPHA)
            skin, dark = (176, 62, 98), (120, 36, 70)
            pygame.draw.ellipse(s, skin, (1, 3, 10, 20))
            pygame.draw.polygon(s, skin, [(3, 6), (6, 0), (9, 6)])        # 앞쪽 끝
            pygame.draw.polygon(s, dark, [(4, 20), (6, 26), (8, 20)])     # 뒤쪽 꼬리
            pygame.draw.ellipse(s, (255, 214, 90), (3, 2, 6, 5))          # 잘린 단면(속살)
            for py in (9, 13, 17):                                        # 껍질 줄무늬
                pygame.draw.line(s, dark, (3, py), (5, py + 1), 1)
            pygame.draw.line(s, (220, 120, 150), (8, 8), (8, 16), 1)      # 하이라이트
            cls._sprite = s
        return cls._sprite

    @classmethod
    def rotated(cls, deg):
        if deg not in cls._rotated:
            cls._rotated[deg] = pygame.transform.rotate(cls.base_sprite(), deg)
        return cls._rotated[deg]

    def draw(self, surf):
        surf.blit(self.image, self.image.get_rect(center=(int(self.x), int(self.y))))


# ---------------------------------------------------------------------------
# 플레이어
# ---------------------------------------------------------------------------
class Player:
    SPEED = 5
    SLOW_SPEED = 2.2
    HITBOX = 4
    MAX_POWER = 4  # 총알 수 = 2 ** power → 2, 4, 8, 16발
    SPREAD = {2: 0.0, 4: 0.35, 8: 0.8, 16: 1.4}  # 부채꼴 전체 각도(라디안)

    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT - 100
        self.power = 1
        self.lives = 3
        self.bombs = 3
        self.cooldown = 0
        self.invincible = 120
        self.tilt = 0

    def update(self, keys, bullets):
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        speed = self.SLOW_SPEED if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else self.SPEED
        if dx and dy:
            speed *= 0.7071
        self.x = clamp(self.x + dx * speed, 16, WIDTH - 16)
        self.y = clamp(self.y + dy * speed, 20, HEIGHT - 20)
        self.tilt += (dx - self.tilt) * 0.2

        if self.cooldown > 0:
            self.cooldown -= 1
        shot = False
        if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and self.cooldown == 0:
            self.shoot(bullets)
            self.cooldown = 6
            shot = True
        if self.invincible > 0:
            self.invincible -= 1
        return shot

    @property
    def shot_count(self):
        return 2 ** self.power

    def shoot(self, bullets):
        n = self.shot_count
        spread = self.SPREAD[n]
        gap = 8 if n == 2 else 2.5
        for i in range(n):
            k = i - (n - 1) / 2
            a = -math.pi / 2 + (k * spread / (n - 1) if n > 1 else 0)
            bullets.append(SweetPotato(self.x + k * gap, self.y - 20,
                                       math.cos(a) * 12, math.sin(a) * 12))

    def draw(self, surf, frame):
        """춘식이 얼굴 모양 비행기"""
        if self.invincible > 0 and (frame // 4) % 2:
            return
        x, y = int(self.x), int(self.y)
        lean = int(self.tilt * 3)
        fur = (247, 210, 150)
        line = (110, 72, 40)
        pink = (255, 170, 170)

        # 그림자
        pygame.draw.circle(surf, (10, 25, 50), (x + 20, y + 26), 16)
        # 엔진 불꽃 (얼굴 아래쪽)
        flame = random.randint(8, 14)
        pygame.draw.polygon(surf, ORANGE, [(x - 6, y + 15), (x + 6, y + 15), (x, y + 15 + flame)])
        pygame.draw.polygon(surf, YELLOW, [(x - 3, y + 15), (x + 3, y + 15), (x, y + 10 + flame)])
        # 귀
        for side in (-1, 1):
            outer = [(x + side * 16, y - 4), (x + side * 13 + lean, y - 22), (x + side * 3, y - 14)]
            inner = [(x + side * 13, y - 7), (x + side * 12 + lean, y - 17), (x + side * 6, y - 13)]
            pygame.draw.polygon(surf, fur, outer)
            pygame.draw.polygon(surf, line, outer, 2)
            pygame.draw.polygon(surf, pink, inner)
        # 얼굴 (살짝 납작한 동그라미)
        face = pygame.Rect(x - 18, y - 16, 36, 32)
        pygame.draw.ellipse(surf, fur, face)
        pygame.draw.ellipse(surf, line, face, 2)
        # 눈 (점 눈)
        pygame.draw.circle(surf, BLACK, (x - 7 + lean, y - 2), 3)
        pygame.draw.circle(surf, BLACK, (x + 7 + lean, y - 2), 3)
        pygame.draw.circle(surf, WHITE, (x - 6 + lean, y - 3), 1)
        pygame.draw.circle(surf, WHITE, (x + 8 + lean, y - 3), 1)
        # 볼터치
        pygame.draw.ellipse(surf, pink, (x - 16 + lean, y + 2, 7, 4))
        pygame.draw.ellipse(surf, pink, (x + 9 + lean, y + 2, 7, 4))
        # 코와 ω 모양 입
        pygame.draw.circle(surf, line, (x + lean, y + 3), 2)
        pygame.draw.arc(surf, line, (x - 5 + lean, y + 2, 6, 6), math.pi, math.tau, 2)
        pygame.draw.arc(surf, line, (x - 1 + lean, y + 2, 6, 6), math.pi, math.tau, 2)

    def draw_hitbox(self, surf):
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.HITBOX + 1)
        pygame.draw.circle(surf, RED, (int(self.x), int(self.y)), self.HITBOX)


# ---------------------------------------------------------------------------
# 적
# ---------------------------------------------------------------------------
class Enemy:
    radius = 14
    hp = 1
    score = 100
    color = RED

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.t = 0
        self.alive = True
        self.flash = 0
        self.hp = type(self).hp

    def hit(self, dmg):
        self.hp -= dmg
        self.flash = 3
        return self.hp <= 0

    def offscreen(self):
        return self.y > HEIGHT + 60 or self.x < -80 or self.x > WIDTH + 80

    def update(self, game):
        self.t += 1
        if self.flash:
            self.flash -= 1
        self.move(game)
        if self.offscreen():
            self.alive = False

    def move(self, game):
        pass

    def fire_at(self, game, speed=3.5, spread=0, count=1):
        base = angle_to((self.x, self.y), (game.player.x, game.player.y))
        for i in range(count):
            a = base + (i - (count - 1) / 2) * spread
            game.enemy_bullets.append(
                Bullet(self.x, self.y, math.cos(a) * speed, math.sin(a) * speed, PURPLE, 5))

    def body_color(self):
        return WHITE if self.flash else self.color


class Drone(Enemy):
    """사인파를 그리며 내려오는 소형기"""
    hp = 2
    score = 100
    color = (220, 80, 80)

    def __init__(self, x, y):
        super().__init__(x, y)
        self.base_x = x
        self.phase = random.uniform(0, math.tau)

    def move(self, game):
        self.y += 2.5
        self.x = self.base_x + math.sin(self.t * 0.05 + self.phase) * 60
        if self.t % 90 == 45 and self.y < HEIGHT * 0.6:
            self.fire_at(game)

    def draw(self, surf):
        c = self.body_color()
        x, y = self.x, self.y
        pygame.draw.polygon(surf, c, [(x, y + 14), (x - 14, y - 8), (x, y - 2), (x + 14, y - 8)])
        pygame.draw.circle(surf, YELLOW, (int(x), int(y)), 4)


class Diver(Enemy):
    """플레이어를 향해 돌진하는 적"""
    hp = 3
    score = 150
    color = (240, 140, 60)

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx, self.vy = 0, 3
        self.locked = False

    def move(self, game):
        if not self.locked and self.y > 120:
            a = angle_to((self.x, self.y), (game.player.x, game.player.y))
            self.vx, self.vy = math.cos(a) * 6, max(2, math.sin(a) * 6)
            self.locked = True
        self.x += self.vx
        self.y += self.vy

    def draw(self, surf):
        c = self.body_color()
        x, y = self.x, self.y
        a = math.atan2(self.vy, self.vx)
        pts = []
        for da, r in ((0, 16), (2.5, 12), (math.pi, 6), (-2.5, 12)):
            pts.append((x + math.cos(a + da) * r, y + math.sin(a + da) * r))
        pygame.draw.polygon(surf, c, pts)
        pygame.draw.circle(surf, WHITE, (int(x), int(y)), 3)


class Turret(Enemy):
    """섬 위에 고정되어 배경과 함께 스크롤되는 포대"""
    hp = 6
    score = 300
    color = (130, 130, 140)
    radius = 16

    def move(self, game):
        self.y += SCROLL_SPEED
        if self.t % 80 == 0 and 0 < self.y < HEIGHT * 0.75:
            self.fire_at(game, speed=3, spread=0.25, count=3)

    def draw(self, surf, player=None):
        c = self.body_color()
        x, y = int(self.x), int(self.y)
        pygame.draw.rect(surf, (80, 80, 90), (x - 16, y - 16, 32, 32), border_radius=4)
        pygame.draw.circle(surf, c, (x, y), 11)
        if player is not None:
            a = angle_to((x, y), (player.x, player.y))
            pygame.draw.line(surf, (50, 50, 60), (x, y),
                             (x + math.cos(a) * 18, y + math.sin(a) * 18), 5)


class Carrier(Enemy):
    """천천히 내려오며 탄막을 뿌리는 중형기 (파워업 드랍)"""
    hp = 25
    score = 1000
    color = (110, 150, 200)
    radius = 30

    def move(self, game):
        if self.y < 150:
            self.y += 1.5
        else:
            self.y += 0.4
        if self.t % 50 == 0:
            for i in range(10):
                a = i / 10 * math.tau + self.t * 0.02
                game.enemy_bullets.append(
                    Bullet(self.x, self.y, math.cos(a) * 2.5, math.sin(a) * 2.5, PURPLE, 5))

    def draw(self, surf):
        c = self.body_color()
        x, y = int(self.x), int(self.y)
        pygame.draw.polygon(surf, c, [(x - 40, y - 10), (x + 40, y - 10), (x + 24, y + 22), (x - 24, y + 22)])
        pygame.draw.rect(surf, (70, 90, 130), (x - 14, y - 24, 28, 40), border_radius=6)
        pygame.draw.circle(surf, RED if self.t % 30 < 15 else ORANGE, (x, y), 7)


class Boss(Enemy):
    hp = 400
    score = 10000
    color = (160, 70, 160)
    radius = 50

    def __init__(self, x, y, level):
        super().__init__(x, y)
        self.hp = self.max_hp = 300 + level * 150
        self.level = level
        self.pattern = 0

    def offscreen(self):
        return False

    def move(self, game):
        if self.y < 140:
            self.y += 1
            return
        self.x = WIDTH / 2 + math.sin(self.t * 0.012) * 140
        self.pattern = (self.t // 300) % 3
        if self.pattern == 0 and self.t % 8 == 0:
            a = self.t * 0.15
            for k in range(3):
                b = a + k * math.tau / 3
                game.enemy_bullets.append(
                    Bullet(self.x, self.y, math.cos(b) * 3, math.sin(b) * 3, PURPLE, 5))
        elif self.pattern == 1 and self.t % 40 == 0:
            self.fire_at(game, speed=4, spread=0.18, count=5 + self.level)
        elif self.pattern == 2 and self.t % 60 == 0:
            for i in range(24):
                a = i / 24 * math.tau
                game.enemy_bullets.append(
                    Bullet(self.x, self.y, math.cos(a) * 2.2, math.sin(a) * 2.2, RED, 6))

    def draw(self, surf):
        c = self.body_color()
        x, y = int(self.x), int(self.y)
        pygame.draw.polygon(surf, (90, 40, 100), [(x - 90, y - 20), (x + 90, y - 20), (x + 60, y + 30), (x - 60, y + 30)])
        pygame.draw.ellipse(surf, c, (x - 50, y - 45, 100, 90))
        pygame.draw.circle(surf, (60, 20, 70), (x, y), 22)
        glow = 150 + int(math.sin(self.t * 0.1) * 100)
        pygame.draw.circle(surf, (255, glow, 60), (x, y), 14)
        for side in (-1, 1):
            pygame.draw.rect(surf, (70, 70, 80), (x + side * 70 - 8, y - 5, 16, 30))


class PowerUp:
    def __init__(self, x, y, kind):
        self.x, self.y = x, y
        self.kind = kind  # 'P' 파워, 'B' 폭탄, '1' 라이프
        self.t = 0
        self.alive = True

    def update(self):
        self.t += 1
        self.y += 1.5
        self.x += math.sin(self.t * 0.08) * 1.2
        if self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, surf, font):
        color = {'P': ORANGE, 'B': CYAN, '1': GREEN}[self.kind]
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 12)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 12, 2)
        txt = font.render(self.kind, True, BLACK)
        surf.blit(txt, txt.get_rect(center=(int(self.x), int(self.y))))


# ---------------------------------------------------------------------------
# 게임
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 256)
        pygame.init()
        pygame.display.set_caption("SKY STRIKE")
        self.sfx = Sfx()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.small = pygame.font.SysFont("consolas", 14, bold=True)
        self.big = pygame.font.SysFont("consolas", 48, bold=True)
        self.background = Background()
        self.high_score = 0
        self.state = "title"
        self.frame = 0
        self.reset()

    def reset(self):
        self.player = Player()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.particles = []
        self.powerups = []
        self.score = 0
        self.level = 1
        self.stage_timer = 0
        self.boss = None
        self.shake = 0
        self.bomb_flash = 0
        self.message = ""
        self.message_timer = 0

    # ---------------- 적 출현 ----------------
    def spawn_enemies(self):
        t = self.stage_timer
        if self.boss:
            return
        if t > 0 and t % 3600 == 0:  # 약 60초마다 보스
            self.boss = Boss(WIDTH / 2, -80, self.level)
            self.enemies.append(self.boss)
            self.show_message("WARNING!")
            self.sfx.play("warning")
            return

        rate = max(20, 60 - self.level * 6)
        if t % rate == 0:
            r = random.random()
            if r < 0.5:
                x = random.randint(80, WIDTH - 80)
                for i in range(random.randint(3, 5)):
                    self.enemies.append(Drone(x, -30 - i * 40))
            elif r < 0.8:
                self.enemies.append(Diver(random.randint(40, WIDTH - 40), -30))
            else:
                isl = next((i for i in self.background.islands if -150 < i.y < -10), None)
                if isl and 20 < isl.x < WIDTH - 20:
                    self.enemies.append(Turret(isl.x, isl.y))
                else:
                    self.enemies.append(Turret(random.randint(40, WIDTH - 40), -30))
        if t % 900 == 450:
            self.enemies.append(Carrier(random.randint(100, WIDTH - 100), -50))

    def show_message(self, text, frames=120):
        self.message = text
        self.message_timer = frames

    # ---------------- 갱신 ----------------
    def use_bomb(self):
        if self.player.bombs <= 0:
            return
        self.player.bombs -= 1
        self.sfx.play("bomb")
        self.bomb_flash = 20
        self.shake = 20
        for b in self.enemy_bullets:
            self.particles.append(Particle(b.x, b.y, PURPLE, speed=2, life=15, size=2))
        self.enemy_bullets.clear()
        for e in self.enemies:
            if e.hit(20 if isinstance(e, Boss) else 10):
                self.kill_enemy(e)

    def kill_enemy(self, e):
        if not e.alive:
            return
        e.alive = False
        self.score += e.score
        big = isinstance(e, (Carrier, Boss))
        explode(self.particles, e.x, e.y, big=big)
        self.sfx.play("big_explode" if big else "explode")
        if big:
            self.shake = 25 if isinstance(e, Boss) else 10
        if isinstance(e, Carrier):
            self.powerups.append(PowerUp(e.x, e.y, random.choice("PPB")))
        elif isinstance(e, Boss):
            for _ in range(5):
                explode(self.particles, e.x + random.randint(-60, 60), e.y + random.randint(-40, 40), True)
            self.powerups.append(PowerUp(e.x, e.y, "1"))
            self.boss = None
            self.level += 1
            self.enemy_bullets.clear()
            self.show_message(f"STAGE {self.level}")
            self.sfx.play("stage")
        elif random.random() < 0.03:
            self.powerups.append(PowerUp(e.x, e.y, random.choice("PB")))

    def player_hit(self):
        p = self.player
        explode(self.particles, p.x, p.y, big=True)
        self.sfx.play("player_down")
        self.shake = 20
        p.lives -= 1
        p.power = max(1, p.power - 1)
        self.enemy_bullets.clear()
        if p.lives <= 0:
            self.state = "gameover"
            self.high_score = max(self.high_score, self.score)
        else:
            p.x, p.y = WIDTH / 2, HEIGHT - 100
            p.invincible = 150
            p.bombs = max(p.bombs, 2)

    def update(self):
        self.frame += 1
        self.background.update()
        for pt in self.particles:
            pt.update()
        self.particles = [pt for pt in self.particles if pt.life > 0]
        if self.shake:
            self.shake -= 1
        if self.bomb_flash:
            self.bomb_flash -= 1
        if self.message_timer:
            self.message_timer -= 1

        if self.state != "play":
            return

        self.stage_timer += 1
        self.spawn_enemies()

        keys = pygame.key.get_pressed()
        p = self.player
        if p.update(keys, self.bullets):
            self.sfx.play("shoot")

        for b in self.bullets:
            b.update()
        for b in self.enemy_bullets:
            b.update()
        for e in self.enemies:
            e.update(self)
        for pu in self.powerups:
            pu.update()

        # 플레이어 탄 vs 적
        for b in self.bullets:
            if not b.alive:
                continue
            for e in self.enemies:
                if e.alive and math.hypot(b.x - e.x, b.y - e.y) < e.radius + b.radius:
                    b.alive = False
                    self.particles.append(Particle(b.x, b.y, YELLOW, speed=2, life=10, size=2))
                    if e.hit(b.damage):
                        self.kill_enemy(e)
                    break

        # 적 / 적 탄 vs 플레이어
        if p.invincible == 0:
            hit = False
            for b in self.enemy_bullets:
                if math.hypot(b.x - p.x, b.y - p.y) < b.radius + p.HITBOX:
                    b.alive = False
                    hit = True
                    break
            if not hit:
                for e in self.enemies:
                    if e.alive and not isinstance(e, Turret) and \
                            math.hypot(e.x - p.x, e.y - p.y) < e.radius + p.HITBOX + 4:
                        hit = True
                        if not isinstance(e, Boss) and e.hit(5):
                            self.kill_enemy(e)
                        break
            if hit:
                self.player_hit()

        # 아이템 획득
        for pu in self.powerups:
            if math.hypot(pu.x - p.x, pu.y - p.y) < 24:
                pu.alive = False
                if pu.kind == "P":
                    if p.power < p.MAX_POWER:
                        p.power += 1
                        self.show_message(f"x{p.shot_count} SHOT!", 60)
                    else:
                        self.score += 500
                    self.sfx.play("powerup")
                elif pu.kind == "B":
                    p.bombs = min(p.bombs + 1, 5)
                    self.sfx.play("item")
                else:
                    p.lives += 1
                    self.sfx.play("powerup")
                self.score += 50

        self.bullets = [b for b in self.bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        self.powerups = [pu for pu in self.powerups if pu.alive]

    # ---------------- 그리기 ----------------
    def draw_text(self, text, font, color, center):
        shadow = font.render(text, True, BLACK)
        surf = font.render(text, True, color)
        self.view.blit(shadow, shadow.get_rect(center=(center[0] + 2, center[1] + 2)))
        self.view.blit(surf, surf.get_rect(center=center))

    def draw_hud(self):
        v = self.view
        v.blit(self.font.render(f"SCORE {self.score:08d}", True, WHITE), (10, 8))
        v.blit(self.small.render(f"HI {max(self.high_score, self.score):08d}", True, YELLOW), (10, 30))
        stage = self.small.render(f"STAGE {self.level}", True, CYAN)
        v.blit(stage, (WIDTH - stage.get_width() - 10, 10))
        for i in range(self.player.lives):
            x = WIDTH - 20 - i * 18
            pygame.draw.polygon(v, WHITE, [(x, HEIGHT - 30), (x - 7, HEIGHT - 16), (x + 7, HEIGHT - 16)])
        for i in range(self.player.bombs):
            pygame.draw.circle(v, CYAN, (16 + i * 18, HEIGHT - 22), 6)
            pygame.draw.circle(v, WHITE, (16 + i * 18, HEIGHT - 22), 6, 1)
        p = self.player
        pw = self.small.render(f"SHOT x{p.shot_count:<2} {'#' * p.power}{'-' * (p.MAX_POWER - p.power)}",
                               True, ORANGE)
        v.blit(pw, (WIDTH // 2 - pw.get_width() // 2, HEIGHT - 28))

        if self.boss:
            ratio = max(0, self.boss.hp / self.boss.max_hp)
            pygame.draw.rect(v, (60, 20, 20), (40, 52, WIDTH - 80, 8))
            pygame.draw.rect(v, RED, (40, 52, (WIDTH - 80) * ratio, 8))
            pygame.draw.rect(v, WHITE, (40, 52, WIDTH - 80, 8), 1)

    def draw(self):
        self.view = pygame.Surface((WIDTH, HEIGHT))
        self.background.draw(self.view)

        if self.state in ("play", "pause", "gameover"):
            for e in self.enemies:
                if isinstance(e, Turret):
                    e.draw(self.view, self.player)
            for e in self.enemies:
                if not isinstance(e, Turret):
                    e.draw(self.view)
            for pu in self.powerups:
                pu.draw(self.view, self.small)
            for b in self.bullets:
                b.draw(self.view)
            if self.state != "gameover":
                self.player.draw(self.view, self.frame)
            for b in self.enemy_bullets:
                b.draw(self.view)
            if self.state == "play":
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    self.player.draw_hitbox(self.view)

        for pt in self.particles:
            pt.draw(self.view)

        if self.bomb_flash:
            flash = pygame.Surface((WIDTH, HEIGHT))
            flash.fill(WHITE)
            flash.set_alpha(self.bomb_flash * 10)
            self.view.blit(flash, (0, 0))

        if self.state in ("play", "pause", "gameover"):
            self.draw_hud()

        if self.message_timer and self.state == "play":
            color = RED if self.message.startswith("WARN") and (self.frame // 10) % 2 else YELLOW
            self.draw_text(self.message, self.big, color, (WIDTH // 2, HEIGHT // 2 - 60))

        if self.state == "title":
            self.draw_text("SKY STRIKE", self.big, YELLOW, (WIDTH // 2, HEIGHT // 3))
            if (self.frame // 30) % 2 == 0:
                self.draw_text("PRESS ENTER", self.font, WHITE, (WIDTH // 2, HEIGHT // 2))
            lines = ["ARROWS/WASD : MOVE", "Z/SPACE : SHOT", "X : BOMB",
                     "SHIFT : SLOW MOVE", "P/ESC : PAUSE"]
            for i, line in enumerate(lines):
                self.draw_text(line, self.small, CYAN, (WIDTH // 2, HEIGHT // 2 + 60 + i * 24))
            if self.high_score:
                self.draw_text(f"HI SCORE {self.high_score}", self.font, YELLOW, (WIDTH // 2, HEIGHT - 80))
        elif self.state == "pause":
            self.draw_text("PAUSED", self.big, WHITE, (WIDTH // 2, HEIGHT // 2))
        elif self.state == "gameover":
            self.draw_text("GAME OVER", self.big, RED, (WIDTH // 2, HEIGHT // 2 - 40))
            self.draw_text(f"SCORE {self.score}", self.font, WHITE, (WIDTH // 2, HEIGHT // 2 + 20))
            if (self.frame // 30) % 2 == 0:
                self.draw_text("PRESS ENTER", self.font, YELLOW, (WIDTH // 2, HEIGHT // 2 + 60))

        ox = random.randint(-self.shake, self.shake) // 2 if self.shake else 0
        oy = random.randint(-self.shake, self.shake) // 2 if self.shake else 0
        self.screen.fill(BLACK)
        self.screen.blit(self.view, (ox, oy))
        pygame.display.flip()

    # ---------------- 루프 ----------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_RETURN and self.state in ("title", "gameover"):
            self.reset()
            self.state = "play"
            self.show_message("STAGE 1")
        elif event.key in (pygame.K_p, pygame.K_ESCAPE):
            if self.state == "play":
                self.state = "pause"
            elif self.state == "pause":
                self.state = "play"
        elif event.key == pygame.K_x and self.state == "play":
            self.use_bomb()

    def run(self):
        while True:
            for event in pygame.event.get():
                self.handle_event(event)
            if self.state != "pause":
                self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
