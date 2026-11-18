import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
import random
import math
import sys

# ============================================================
# NEON VOID V2 (FIXED)
# ============================================================

pygame.init()

try:
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except:
    SOUND_AVAILABLE = False


# ============================================================
# CONFIG
# ============================================================

WIDTH = 900
HEIGHT = 700
FPS = 60

TITLE = "NEON VOID // SPACE SHOOTER"


# ============================================================
# COLORS
# ============================================================

BLACK = (4, 3, 12)
DARK_PURPLE = (12, 5, 28)
PURPLE = (170, 50, 255)
CYAN = (0, 240, 255)
PINK = (255, 25, 160)
BLUE = (60, 120, 255)
YELLOW = (255, 235, 50)
ORANGE = (255, 100, 20)
GREEN = (60, 255, 130)
WHITE = (255, 255, 255)

ENEMY_COLORS = [
    PINK,
    PURPLE,
    ORANGE,
    GREEN
]


# ============================================================
# SCREEN
# ============================================================

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)

clock = pygame.time.Clock()


# ============================================================
# FONTS
# ============================================================

font_title = pygame.font.SysFont("consolas", 72, bold=True)
font_big = pygame.font.SysFont("consolas", 44, bold=True)
font_medium = pygame.font.SysFont("consolas", 26, bold=True)
font_small = pygame.font.SysFont("consolas", 18, bold=True)


# ============================================================
# SOUND
# ============================================================

def make_sound(freq, duration, volume=0.15):

    if not SOUND_AVAILABLE:
        return None

    sample_rate = 44100
    samples = int(sample_rate * duration)

    buffer = bytearray()

    for i in range(samples):

        t = i / sample_rate
        fade = 1 - i / samples
        value = math.sin(2 * math.pi * freq * t)
        sample = int(value * volume * fade * 32767)

        buffer += int(sample).to_bytes(2, "little", signed=True)

    try:
        return pygame.mixer.Sound(buffer=bytes(buffer))
    except:
        return None


SOUND_SHOOT = make_sound(900, 0.05, 0.12)
SOUND_HIT = make_sound(180, 0.08, 0.18)
SOUND_EXPLOSION = make_sound(90, 0.25, 0.25)


def play(sound):
    if sound:
        try:
            sound.play()
        except:
            pass


# ============================================================
# GLOW HELPERS
# ============================================================

def glow_circle(surface, color, x, y, radius, strength=80):

    for i in range(4, 0, -1):

        r = radius + i * 8
        alpha = int(strength * (1 - i / 5))

        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (r, r), r)

        surface.blit(glow, (x - r, y - r), special_flags=pygame.BLEND_RGBA_ADD)


def glow_line(surface, color, start, end, width=3):

    for i in range(3, 0, -1):

        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(glow, (*color, 40), start, end, width + i * 4)

        surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    pygame.draw.line(surface, color, start, end, width)


# ============================================================
# STAR
# ============================================================

class Star:

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.speed = random.uniform(30, 220)
        self.size = random.choice([1, 1, 1, 2, 2, 3])
        self.color = random.choice([WHITE, CYAN, PURPLE, PINK])

    def update(self, dt):
        self.y += self.speed * dt
        if self.y > HEIGHT:
            self.reset()
            self.y = -5

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


stars = [Star() for _ in range(180)]


# ============================================================
# PARTICLE
# ============================================================

class Particle:

    def __init__(self, x, y, color):

        self.x = x
        self.y = y

        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, 350)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.life = random.uniform(0.3, 0.8)
        self.max_life = self.life

        self.color = color
        self.size = random.randint(2, 5)

    def update(self, dt):

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.vx *= 0.96
        self.vy *= 0.96

        self.life -= dt

    def draw(self, surface):

        if self.life <= 0:
            return

        alpha = int(255 * self.life / self.max_life)
        size = max(1, int(self.size * self.life / self.max_life))

        glow = pygame.Surface((size * 8, size * 8), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, alpha), (size * 4, size * 4), size * 3)

        surface.blit(glow, (self.x - size * 4, self.y - size * 4), special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)


particles = []


def explosion(x, y, color, amount=35):
    for _ in range(amount):
        particles.append(Particle(x, y, color))


# ============================================================
# SHOCKWAVE
# ============================================================

class Shockwave:

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 5
        self.life = 0.45

    def update(self, dt):
        self.radius += 180 * dt
        self.life -= dt

    def draw(self, surface):

        if self.life <= 0:
            return

        alpha = int(255 * self.life / 0.45)

        ring = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self.color, alpha), (int(self.x), int(self.y)), int(self.radius), 3)

        surface.blit(ring, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


shockwaves = []


# ============================================================
# FLOATING SCORE TEXT  (new: gives clear visual proof a hit registered)
# ============================================================

class FloatingText:

    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 0.7
        self.max_life = 0.7

    def update(self, dt):
        self.y -= 45 * dt
        self.life -= dt

    def draw(self, surface):

        if self.life <= 0:
            return

        alpha = int(255 * self.life / self.max_life)
        img = font_small.render(self.text, True, self.color)
        img.set_alpha(alpha)
        surface.blit(img, (self.x - img.get_width() / 2, self.y))


floating_texts = []


# ============================================================
# BULLET
# ============================================================

class Bullet:

    def __init__(self, x, y, direction=-1):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = 720 if direction == -1 else 300

    @property
    def rect(self):
        # slightly more generous hitbox than the raw sprite so fast-moving
        # bullets don't feel like they "should have" hit but didn't
        return pygame.Rect(self.x - 5, self.y - 12, 10, 24)

    def update(self, dt):
        self.y += self.speed * self.direction * dt

    def draw(self, surface):
        glow_line(
            surface,
            CYAN if self.direction == -1 else PINK,
            (self.x, self.y - 10),
            (self.x, self.y + 10),
            3
        )


# ============================================================
# PLAYER
# ============================================================

class Player:

    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT - 100
        self.speed = 430
        self.width = 36
        self.height = 50
        self.cooldown = 0
        self.fire_rate = 0.14
        self.hp = 100
        self.invulnerable = 0
        self.engine = 0
        self.tilt = 0

    @property
    def rect(self):
        return pygame.Rect(
            self.x - self.width / 2,
            self.y - self.height / 2,
            self.width,
            self.height
        )

    def update(self, dt, keys):

        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        if dx or dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length

        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt

        self.x = max(30, min(WIDTH - 30, self.x))
        self.y = max(50, min(HEIGHT - 40, self.y))

        target_tilt = -dx * 20
        self.tilt += (target_tilt - self.tilt) * min(1, dt * 10)

        if self.cooldown > 0:
            self.cooldown -= dt
        if self.invulnerable > 0:
            self.invulnerable -= dt

        self.engine += dt * 20

    def shoot(self):

        if self.cooldown > 0:
            return None

        self.cooldown = self.fire_rate
        play(SOUND_SHOOT)

        return [
            Bullet(self.x - 10, self.y - 25),
            Bullet(self.x + 10, self.y - 25)
        ]

    def draw(self, surface):

        flame = 16 + math.sin(self.engine) * 5

        glow_circle(surface, ORANGE, self.x, self.y + 27 + flame / 2, 8, 100)

        pygame.draw.polygon(
            surface,
            ORANGE,
            [
                (self.x - 7, self.y + 20),
                (self.x + 7, self.y + 20),
                (self.x, self.y + 20 + flame)
            ]
        )

        points = [
            (self.x, self.y - 28),
            (self.x - 25, self.y + 22),
            (self.x - 8, self.y + 15),
            (self.x, self.y + 25),
            (self.x + 8, self.y + 15),
            (self.x + 25, self.y + 22)
        ]

        glow_circle(surface, CYAN, self.x, self.y, 18, 35)

        pygame.draw.polygon(surface, CYAN, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        glow_circle(surface, PURPLE, self.x, self.y - 5, 8, 90)

        pygame.draw.circle(surface, PURPLE, (int(self.x), int(self.y - 5)), 7)


# ============================================================
# ENEMY
# ============================================================

class Enemy:

    def __init__(self, wave):

        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(-150, -50)

        self.size = random.choice([25, 30, 38])
        self.color = random.choice(ENEMY_COLORS)
        self.speed = random.uniform(80, 140) + wave * 7
        self.phase = random.uniform(0, math.tau)

        self.hp = 2 if self.size >= 35 else 1
        self.angle = 0

    @property
    def rect(self):
        return pygame.Rect(
            self.x - self.size / 2,
            self.y - self.size / 2,
            self.size,
            self.size
        )

    def update(self, dt, time):
        self.y += self.speed * dt
        self.x += math.sin(time * 2 + self.phase) * 0.8
        self.angle += dt * 2

    def draw(self, surface):

        s = self.size
        points = []

        for i in range(8):

            angle = self.angle + i * math.tau / 8
            radius = s / 2 if i % 2 == 0 else s / 3

            points.append((
                self.x + math.cos(angle) * radius,
                self.y + math.sin(angle) * radius
            ))

        glow_circle(surface, self.color, self.x, self.y, s / 2, 65)

        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        pygame.draw.circle(
            surface,
            BLACK,
            (int(self.x), int(self.y)),
            max(3, int(s / 6))
        )


# ============================================================
# GAME
# ============================================================

class Game:

    def __init__(self):
        self.reset()

    def reset(self):

        self.player = Player()

        self.bullets = []
        self.enemies = []

        self.score = 0
        self.wave = 1
        self.time = 0
        self.spawn_timer = 0

        self.game_over = False
        self.paused = False
        self.started = False

        self.shake = 0

        particles.clear()
        shockwaves.clear()
        floating_texts.clear()

    # --------------------------------------------------------
    # SPAWN ENEMY
    # --------------------------------------------------------

    def spawn_enemy(self):
        self.enemies.append(Enemy(self.wave))

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(self, dt, keys, firing):

        if not self.started or self.game_over or self.paused:
            return

        self.time += dt
        self.wave = 1 + int(self.time / 15)

        # player
        self.player.update(dt, keys)

        # firing
        if firing:
            new_bullets = self.player.shoot()
            if new_bullets:
                self.bullets.extend(new_bullets)

        # spawn
        self.spawn_timer -= dt
        spawn_rate = max(0.25, 0.9 - self.wave * 0.05)

        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = spawn_rate

        # bullets
        for bullet in self.bullets:
            bullet.update(dt)

        self.bullets = [b for b in self.bullets if -30 < b.y < HEIGHT + 30]

        # enemies
        for enemy in self.enemies:
            enemy.update(dt, self.time)

        # ----------------------------------------------------
        # BULLET COLLISION
        # ----------------------------------------------------

        for bullet in self.bullets[:]:

            if bullet.direction != -1:
                continue

            for enemy in self.enemies[:]:

                if enemy.rect.colliderect(bullet.rect):

                    if bullet in self.bullets:
                        self.bullets.remove(bullet)

                    enemy.hp -= 1

                    play(SOUND_HIT)

                    explosion(bullet.x, bullet.y, enemy.color, 8)

                    if enemy.hp <= 0:

                        explosion(enemy.x, enemy.y, enemy.color, 40)

                        shockwaves.append(
                            Shockwave(enemy.x, enemy.y, enemy.color)
                        )

                        gained = 10 * self.wave
                        self.score += gained

                        floating_texts.append(
                            FloatingText(enemy.x, enemy.y, f"+{gained}", YELLOW)
                        )

                        self.shake = 7

                        play(SOUND_EXPLOSION)

                        if enemy in self.enemies:
                            self.enemies.remove(enemy)

                    break

        # ----------------------------------------------------
        # ENEMY VS PLAYER
        # ----------------------------------------------------

        if self.player.invulnerable <= 0:

            for enemy in self.enemies[:]:

                if enemy.rect.colliderect(self.player.rect):

                    if enemy in self.enemies:
                        self.enemies.remove(enemy)

                    self.damage_player(30)

        # ----------------------------------------------------
        # ENEMY BULLETS
        # ----------------------------------------------------

        for bullet in self.bullets[:]:

            if bullet.direction != 1:
                continue

            if self.player.rect.colliderect(bullet.rect):

                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                self.damage_player(15)

        # ----------------------------------------------------
        # REMOVE OFFSCREEN ENEMIES
        # ----------------------------------------------------

        self.enemies = [e for e in self.enemies if e.y < HEIGHT + 70]

        # ----------------------------------------------------
        # PARTICLES / SHOCKWAVES / FLOATING TEXT
        # ----------------------------------------------------

        for particle in particles:
            particle.update(dt)
        particles[:] = [p for p in particles if p.life > 0]

        for sw in shockwaves:
            sw.update(dt)
        shockwaves[:] = [w for w in shockwaves if w.life > 0]

        for ft in floating_texts:
            ft.update(dt)
        floating_texts[:] = [f for f in floating_texts if f.life > 0]

        if self.shake > 0:
            self.shake *= 0.88
            if self.shake < 0.5:
                self.shake = 0

    # --------------------------------------------------------
    # DAMAGE
    # --------------------------------------------------------

    def damage_player(self, damage):

        self.player.hp -= damage
        self.player.invulnerable = 1
        self.shake = 15

        explosion(self.player.x, self.player.y, CYAN, 20)

        play(SOUND_HIT)

        if self.player.hp <= 0:
            self.player.hp = 0
            self.game_over = True
            explosion(self.player.x, self.player.y, CYAN, 70)

    # --------------------------------------------------------
    # DRAW BACKGROUND
    # --------------------------------------------------------

    def draw_background(self, surface):

        surface.fill(BLACK)

        for y in range(0, HEIGHT, 5):

            ratio = y / HEIGHT

            color = (
                int(DARK_PURPLE[0] * (1 - ratio)),
                int(DARK_PURPLE[1] * (1 - ratio)),
                int(DARK_PURPLE[2] * (1 - ratio))
            )

            pygame.draw.rect(surface, color, (0, y, WIDTH, 5))

        for star in stars:
            star.update(1 / FPS)
            star.draw(surface)

        horizon = int(HEIGHT * 0.72)

        glow_circle(surface, PURPLE, WIDTH // 2, horizon, 90, 35)

        pygame.draw.circle(surface, ORANGE, (WIDTH // 2, horizon), 65)

        for i in range(5):

            y = horizon - 20 + i * 18

            pygame.draw.rect(
                surface,
                DARK_PURPLE,
                (WIDTH // 2 - 65, y, 130, 6)
            )

        grid_color = (70, 20, 110)

        for i in range(1, 10):

            y = horizon + i * i * 5

            if y < HEIGHT:
                pygame.draw.line(surface, grid_color, (0, y), (WIDTH, y), 1)

        for i in range(-8, 9):

            pygame.draw.line(
                surface,
                grid_color,
                (WIDTH // 2, horizon),
                (WIDTH // 2 + i * 100, HEIGHT),
                1
            )

    # --------------------------------------------------------
    # DRAW HUD
    # --------------------------------------------------------

    def draw_hud(self, surface):

        panel = pygame.Surface((WIDTH, 85), pygame.SRCALPHA)
        panel.fill((5, 3, 20, 190))
        surface.blit(panel, (0, 0))

        score_txt = font_medium.render(f"SCORE : {self.score:05d}", True, YELLOW)
        surface.blit(score_txt, (25, 18))

        wave_txt = font_small.render(f"WAVE : {self.wave:02d}", True, CYAN)
        surface.blit(wave_txt, (27, 53))

        label = font_small.render("HULL", True, WHITE)
        surface.blit(label, (WIDTH - 260, 18))

        bar_x = WIDTH - 260
        bar_y = 45
        bar_w = 220
        bar_h = 18

        pygame.draw.rect(surface, (40, 20, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=8)

        percentage = self.player.hp / 100

        if percentage > 0.5:
            hp_color = GREEN
        elif percentage > 0.25:
            hp_color = YELLOW
        else:
            hp_color = PINK

        pygame.draw.rect(
            surface,
            hp_color,
            (bar_x, bar_y, int(bar_w * percentage), bar_h),
            border_radius=8
        )

        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=8)

    # --------------------------------------------------------
    # START SCREEN
    # --------------------------------------------------------

    def draw_start(self, surface):

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 1, 12, 170))
        surface.blit(overlay, (0, 0))

        title = font_title.render("NEON VOID", True, CYAN)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 190))

        subtitle = font_medium.render("SPACE SHOOTER", True, PINK)
        surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 275))

        controls = font_small.render("WASD / ARROWS  •  SPACE TO FIRE", True, WHITE)
        surface.blit(controls, (WIDTH // 2 - controls.get_width() // 2, 350))

        press = font_medium.render("PRESS ANY KEY TO START", True, YELLOW)

        if int(pygame.time.get_ticks() / 500) % 2 == 0:
            surface.blit(press, (WIDTH // 2 - press.get_width() // 2, 420))

    # --------------------------------------------------------
    # GAME OVER
    # --------------------------------------------------------

    def draw_game_over(self, surface):

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 0, 15, 190))
        surface.blit(overlay, (0, 0))

        title = font_title.render("GAME OVER", True, PINK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 220))

        score_txt = font_big.render(f"SCORE : {self.score}", True, YELLOW)
        surface.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 315))

        restart = font_medium.render("PRESS R TO RESTART", True, CYAN)
        surface.blit(restart, (WIDTH // 2 - restart.get_width() // 2, 400))

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    def draw(self):

        world = pygame.Surface((WIDTH, HEIGHT))

        self.draw_background(world)

        for enemy in self.enemies:
            enemy.draw(world)

        for bullet in self.bullets:
            bullet.draw(world)

        for particle in particles:
            particle.draw(world)

        for sw in shockwaves:
            sw.draw(world)

        if not self.game_over:
            self.player.draw(world)

        for ft in floating_texts:
            ft.draw(world)

        offset_x = 0
        offset_y = 0

        if self.shake > 0:
            offset_x = random.randint(-int(self.shake), int(self.shake))
            offset_y = random.randint(-int(self.shake), int(self.shake))

        screen.fill(BLACK)
        screen.blit(world, (offset_x, offset_y))

        self.draw_hud(screen)

        if not self.started:
            self.draw_start(screen)

        elif self.paused:

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            pause = font_title.render("PAUSED", True, CYAN)
            screen.blit(
                pause,
                (
                    WIDTH // 2 - pause.get_width() // 2,
                    HEIGHT // 2 - pause.get_height() // 2
                )
            )

        elif self.game_over:
            self.draw_game_over(screen)


# ============================================================
# MAIN
# ============================================================

def main():

    game = Game()
    running = True
    firing = False

    while running:

        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                # FIX: any key starts the game, not just SPACE.
                # Previously, if the player pressed an arrow key first
                # (very natural instinct), game.started stayed False and
                # game.update() returned immediately every frame -- meaning
                # nothing ever spawned, moved, or scored, no matter how
                # long they played.
                if not game.started and not game.game_over:
                    game.started = True

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    firing = True

                elif event.key == pygame.K_p:
                    if game.started:
                        game.paused = not game.paused

                elif event.key == pygame.K_r:
                    if game.game_over:
                        game.reset()
                        game.started = True

            elif event.type == pygame.KEYUP:

                if event.key == pygame.K_SPACE:
                    firing = False

        keys = pygame.key.get_pressed()

        game.update(dt, keys, firing)
        game.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()