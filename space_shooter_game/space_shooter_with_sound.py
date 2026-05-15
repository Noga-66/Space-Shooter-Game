import pygame
import random
import math
import sys
import os
import numpy as np

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter - play Now!")
clock = pygame.time.Clock()
FPS = 60

# ── Colors ──────────────────────────────────────────────────────
DEEP_SPACE   = (5,   5,  20)
NEBULA_PURP  = (80,  30, 120, 60)
NEBULA_BLUE  = (20,  60, 140, 50)
SHIP_BODY    = (180, 220, 255)
SHIP_ACCENT  = (80,  160, 255)
ENGINE_GLOW  = (100, 200, 255)
FLAME_ORNG   = (255, 140,  30)
FLAME_YEL    = (255, 220,  50)
ENEMY_RED    = (220,  50,  50)
ENEMY_DARK   = (140,  20,  20)
ENEMY_GLOW   = (255, 100,  80)
BULLET_CLR   = (120, 255, 200)
ENEMY_BULL   = (255,  80,  80)
PLANET_HIGH  = (100, 150, 220)
PLANET_DARK  = (30,   60, 120)
RING_CLR     = (180, 150,  80)
ASTEROID_CLR = (120, 100,  80)
ASTEROID_HI  = (160, 140, 110)
ASTEROID_DK  = (70,   55,  40)
HUD_GREEN    = (80,  255, 160)
HUD_RED      = (255,  80,  80)
HUD_CYAN     = (80,  220, 255)
WHITE        = (255, 255, 255)
YELLOW       = (255, 220,  50)


# ══════════════════════════════════════════════════════════════════
# ── SOUND MANAGER ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════
class SoundManager:
    """
    يدعم ملفات صوت خارجية (.wav / .mp3 / .ogg).
    لو مفيش ملفات، يشتغل بصمت من غير أخطاء.

    ضع ملفاتك في نفس مجلد اللعبة بالأسماء دي:
      shoot.wav        ← صوت إطلاق النار
      explosion.wav    ← صوت انفجار الأعداء
      bg_music.mp3     ← موسيقى خلفية (أو .ogg)

    مصادر مجانية مقترحة:
      • https://freesound.org   (ابحث عن: laser shoot, space explosion, space music)
      • https://opengameart.org
    """

    SOUND_FILES = {
        "shoot":     ["shoot_wav.mp3", "shoot.wav", "shoot.mp3", "shoot.ogg", "laser.wav"],
        "explosion": ["explosion_wav.mp3", "explosion.wav", "explosion.mp3", "explosion.ogg", "boom.wav"],
    }
    MUSIC_FILES = ["bg_music_mp3.mp3", "bg_music.mp3", "bg_music.ogg", "music.mp3", "music.ogg"]

    def __init__(self):
        self.sounds  = {}
        self.enabled = True
        self._load_sounds()
        self._load_music()

    def _find_file(self, names):
        """ابحث عن أول ملف موجود من قايمة الأسماء."""
        for name in names:
            if os.path.isfile(name):
                return name
        return None

    def _load_sounds(self):
        for key, names in self.SOUND_FILES.items():
            path = self._find_file(names)
            if path:
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(0.5)
                    self.sounds[key] = snd
                    print(f"[Sound] Loaded '{key}' ← {path}")
                except Exception as e:
                    print(f"[Sound] Failed to load '{key}': {e}")
            else:
                print(f"[Sound] '{key}' not found — running silently for this sound.")

    def _load_music(self):
        path = self._find_file(self.MUSIC_FILES)
        if path:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)   # loop forever
                print(f"[Sound] Music loaded ← {path}")
            except Exception as e:
                print(f"[Sound] Music failed: {e}")
        else:
            print("[Sound] No background music file found — running silently.")

    def play(self, key):
        if not self.enabled:
            return
        snd = self.sounds.get(key)
        if snd:
            snd.play()

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
        return self.enabled


# ── Star ────────────────────────────────────────────────────────
class Star:
    def __init__(self):
        self.reset(random.randint(0, WIDTH))

    def reset(self, x=WIDTH):
        self.x = x
        self.y = random.randint(0, HEIGHT)
        self.size = random.choice([1, 1, 2, 2, 3])
        self.speed = self.size * 0.5
        self.bright = random.randint(150, 255)
        self.off = random.uniform(0, math.pi * 2)

    def update(self):
        self.x -= self.speed
        if self.x < 0:
            self.reset()

    def draw(self, surf, t):
        b = max(100, min(255, self.bright + int(30 * math.sin(t * 2 + self.off))))
        pygame.draw.circle(surf, (b, b, min(255, b+20)), (int(self.x), int(self.y)), self.size)


# ── Nebula surface ───────────────────────────────────────────────
def make_nebula():
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for _ in range(6):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        rx, ry = random.randint(80,200), random.randint(60,150)
        color = random.choice([NEBULA_PURP, NEBULA_BLUE])
        blob = pygame.Surface((rx*2, ry*2), pygame.SRCALPHA)
        for step in range(5,0,-1):
            a = color[3] // step
            pygame.draw.ellipse(blob, (*color[:3], a),
                (rx - rx*step//5, ry - ry*step//5, rx*step//5*2, ry*step//5*2))
        surf.blit(blob, (x-rx, y-ry))
    return surf


# ── Draw helpers ─────────────────────────────────────────────────
def draw_planet(surf, cx, cy, r):
    pygame.draw.circle(surf, PLANET_DARK, (cx, cy), r)
    for i in range(r, 0, -1):
        ratio = i / r
        c = tuple(int(PLANET_HIGH[j]*ratio + PLANET_DARK[j]*(1-ratio)) for j in range(3))
        pygame.draw.circle(surf, c, (cx - r//5, cy - r//5), i)
    rs = pygame.Surface((r*4, r*2), pygame.SRCALPHA)
    pygame.draw.ellipse(rs, (*RING_CLR, 180), (0, r//2, r*4, r))
    pygame.draw.circle(rs, (0,0,0,0), (r*2, r), r)
    surf.blit(rs, (cx - r*2, cy - r))

def draw_ship(surf, x, y, t):
    fl = 20 + int(10 * math.sin(t * 8))
    fw = 8  + int(4  * math.sin(t * 10))
    fp = [(x-14,y),(x-14-fl,y-fw//2),(x-14-fl*3//4,y),(x-14-fl,y+fw//2)]
    pygame.draw.polygon(surf, FLAME_YEL, fp)
    ip = [(x-14,y),(x-14-fl*2//3,y-fw//4),(x-14-fl*2//3,y+fw//4)]
    pygame.draw.polygon(surf, FLAME_ORNG, ip)
    hp = [(x+30,y),(x+10,y-14),(x-20,y-18),(x-14,y-6),(x-14,y+6),(x-20,y+18),(x+10,y+14)]
    pygame.draw.polygon(surf, SHIP_BODY, hp)
    pygame.draw.polygon(surf, SHIP_ACCENT, hp, 2)
    pygame.draw.ellipse(surf, ENGINE_GLOW,     (x+5, y-7, 18, 14))
    pygame.draw.ellipse(surf, (200,240,255),   (x+8, y-5, 12, 10))
    pygame.draw.rect(surf,   SHIP_ACCENT,      (x+26, y-2, 10, 4))

def draw_enemy(surf, x, y, t):
    wb = int(4 * math.sin(t * 3 + x))
    pts = [(x-25,y+wb),(x-5,y-18+wb),(x+15,y-10+wb),(x+20,y+wb),(x+15,y+10+wb),(x-5,y+18+wb)]
    pygame.draw.polygon(surf, ENEMY_RED, pts)
    pygame.draw.polygon(surf, ENEMY_DARK, pts, 2)
    gr = 6 + int(2 * math.sin(t * 5))
    pygame.draw.circle(surf, ENEMY_GLOW, (x+5, y+wb), gr)
    pygame.draw.circle(surf, (255,220,200), (x+5, y+wb), gr-2)
    pygame.draw.rect(surf, ENEMY_DARK, (x+20, y-2+wb, 12, 4))

def draw_asteroid(surf, x, y, r, angle):
    pts = []
    for i in range(9):
        a = angle + (2*math.pi/9)*i
        dist = r * (0.7 + 0.3 * math.sin(a*3 + angle))
        pts.append((x + dist*math.cos(a), y + dist*math.sin(a)))
    pygame.draw.polygon(surf, ASTEROID_CLR, pts)
    pygame.draw.polygon(surf, ASTEROID_DK,  pts, 2)
    pygame.draw.circle(surf, ASTEROID_HI, (int(x - r*0.2), int(y - r*0.2)), max(2, r//4))

def draw_hud(surf, score, health, lives, font_big, font_sm, sound_on):
    surf.blit(font_big.render(f"SCORE  {score:05d}", True, HUD_CYAN), (20, 15))
    surf.blit(font_sm.render("HP", True, HUD_GREEN), (WIDTH-160, 18))
    pygame.draw.rect(surf, (40,40,40),  (WIDTH-135, 20, 110, 14), border_radius=4)
    bw = int(110 * max(0, health) / 100)
    col = HUD_GREEN if health > 40 else YELLOW if health > 20 else HUD_RED
    pygame.draw.rect(surf, col, (WIDTH-135, 20, bw, 14), border_radius=4)
    for i in range(lives):
        lx = 20 + i * 30
        lpts = [(lx+15,300),(lx+5,288),(lx-5,286),(lx-15,288),(lx-15,300)]
        npts = [(p[0], p[1]-285) for p in lpts]
        pygame.draw.polygon(surf, HUD_RED, npts)
    blen = 20
    for cx,cy,sx,sy in [(0,0,1,1),(WIDTH,0,-1,1),(0,HEIGHT,1,-1),(WIDTH,HEIGHT,-1,-1)]:
        pygame.draw.line(surf, HUD_CYAN, (cx,cy), (cx+sx*blen,cy), 2)
        pygame.draw.line(surf, HUD_CYAN, (cx,cy), (cx,cy+sy*blen), 2)
    sound_icon = "♪ ON" if sound_on else "♪ OFF"
    sound_col  = HUD_GREEN if sound_on else HUD_RED
    surf.blit(font_sm.render(sound_icon, True, sound_col), (WIDTH - 55, HEIGHT - 24))
    ctrl = font_sm.render("WASD/ARROWS: Move  SPACE: Fire  M: Sound  ESC: Exit", True, (100,100,140))
    surf.blit(ctrl, (WIDTH//2 - ctrl.get_width()//2, HEIGHT - 24))


# ── Game objects ─────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x, self.y = 150, HEIGHT//2
        self.speed = 5
        self.health = 100
        self.lives  = 3
        self.score  = 0
        self.shoot_cd = 0
        self.inv_timer = 0

    def update(self, keys):
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.x += self.speed
        self.x = max(40,  min(WIDTH - 40,  self.x))
        self.y = max(30,  min(HEIGHT - 30, self.y))
        if self.shoot_cd > 0: self.shoot_cd -= 1
        if self.inv_timer > 0: self.inv_timer -= 1

    def shoot(self):
        if self.shoot_cd == 0:
            self.shoot_cd = 14
            return Bullet(self.x + 35, self.y, 12, BULLET_CLR, 1)
        return None

    def hit(self, dmg=20):
        if self.inv_timer == 0:
            self.health -= dmg
            self.inv_timer = 60
            return True
        return False

    def rect(self):
        return pygame.Rect(self.x - 25, self.y - 12, 50, 24)

    def draw(self, surf, t):
        if self.inv_timer > 0 and (self.inv_timer // 6) % 2 == 0:
            return
        draw_ship(surf, self.x, self.y, t)


class Enemy:
    def __init__(self, x=None, y=None):
        self.x = x if x else WIDTH + 50
        self.y = y if y else random.randint(60, HEIGHT - 60)
        self.speed  = random.uniform(1.2, 2.5)
        self.hp     = 2
        self.shoot_cd = random.randint(60, 150)
        self.amplitude = random.uniform(30, 80)
        self.freq      = random.uniform(0.02, 0.05)
        self.base_y    = self.y

    def update(self, t):
        self.x -= self.speed
        self.y  = self.base_y + self.amplitude * math.sin(self.freq * self.x + t)
        self.y  = max(40, min(HEIGHT - 40, self.y))
        if self.shoot_cd > 0: self.shoot_cd -= 1

    def shoot(self):
        if self.shoot_cd == 0:
            self.shoot_cd = random.randint(80, 160)
            return Bullet(self.x - 10, self.y, -7, ENEMY_BULL, -1)
        return None

    def rect(self):
        return pygame.Rect(self.x - 22, self.y - 16, 44, 32)

    def draw(self, surf, t):
        draw_enemy(surf, int(self.x), int(self.y), t)


class Asteroid:
    def __init__(self):
        self.x     = WIDTH + random.randint(20, 80)
        self.y     = random.randint(40, HEIGHT - 40)
        self.r     = random.randint(14, 32)
        self.speed = random.uniform(1.0, 2.5)
        self.angle = random.uniform(0, math.pi*2)
        self.spin  = random.uniform(-0.03, 0.03)
        self.hp    = self.r // 10

    def update(self):
        self.x     -= self.speed
        self.angle += self.spin

    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)

    def draw(self, surf):
        draw_asteroid(surf, int(self.x), int(self.y), self.r, self.angle)


class Bullet:
    def __init__(self, x, y, speed, color, owner):
        self.x, self.y = x, y
        self.speed  = speed
        self.color  = color
        self.owner  = owner
        self.active = True

    def update(self):
        self.x += self.speed
        if self.x > WIDTH + 20 or self.x < -20:
            self.active = False

    def rect(self):
        return pygame.Rect(self.x - 9, self.y - 3, 18, 6)

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, (self.x-9, self.y-3, 18, 6), border_radius=3)
        light = tuple(min(255, c+60) for c in self.color)
        pygame.draw.rect(surf, light, (self.x-7, self.y-1, 10, 2), border_radius=2)


class Explosion:
    def __init__(self, x, y, big=False):
        self.x, self.y = x, y
        self.particles = []
        n = 20 if big else 10
        for _ in range(n):
            a = random.uniform(0, math.pi*2)
            s = random.uniform(1, 5 if big else 3)
            r = random.randint(3, 8 if big else 5)
            c = random.choice([FLAME_YEL, FLAME_ORNG, (255,200,100),(255,100,30)])
            self.particles.append([self.x, self.y, math.cos(a)*s, math.sin(a)*s, r, c, 1.0])
        self.done = False

    def update(self):
        alive = False
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]
            p[2] *= 0.92; p[3] *= 0.92
            p[6] -= 0.04
            if p[6] > 0: alive = True
        self.done = not alive

    def draw(self, surf):
        for p in self.particles:
            if p[6] <= 0: continue
            alpha = int(p[6] * 255)
            s = pygame.Surface((p[4]*2, p[4]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p[5], alpha), (p[4], p[4]), p[4])
            surf.blit(s, (int(p[0]-p[4]), int(p[1]-p[4])))


# ── Screens ──────────────────────────────────────────────────────
def draw_overlay(surf, title, subtitle, font_big, font_sm, color=WHITE):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    t = font_big.render(title, True, color)
    s = font_sm.render(subtitle, True, (180, 180, 220))
    surf.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 50))
    surf.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 + 10))


# ── Main game loop ───────────────────────────────────────────────
def main():
    font_big = pygame.font.SysFont("Courier New", 28, bold=True)
    font_sm  = pygame.font.SysFont("Courier New", 18)

    nebula  = make_nebula()
    stars   = [Star() for _ in range(180)]

    # ── تهيئة الصوت ──────────────────────────────────────────────
    sounds = SoundManager()

    player     = Player()
    enemies    = []
    asteroids  = []
    bullets    = []
    explosions = []

    enemy_spawn_cd  = 90
    ast_spawn_cd    = 120
    t = 0.0

    state = "playing"

    while True:
        dt = clock.tick(FPS) / 1000.0
        t += dt

        # ── Events ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_m:
                    # M: وقف / تشغيل الصوت
                    on = sounds.toggle()
                    print(f"[Sound] {'ON' if on else 'OFF'}")
                if state != "playing" and event.key == pygame.K_r:
                    main()

        keys = pygame.key.get_pressed()

        if state == "playing":
            player.update(keys)

            # إطلاق النار
            if keys[pygame.K_SPACE]:
                b = player.shoot()
                if b:
                    bullets.append(b)
                    sounds.play("shoot")          # ← صوت الطلقة

            # Spawn enemies
            enemy_spawn_cd -= 1
            if enemy_spawn_cd <= 0:
                enemies.append(Enemy())
                enemy_spawn_cd = max(40, 100 - player.score // 200)

            # Spawn asteroids
            ast_spawn_cd -= 1
            if ast_spawn_cd <= 0:
                asteroids.append(Asteroid())
                ast_spawn_cd = random.randint(80, 160)

            for e in enemies:
                e.update(t)
                b = e.shoot()
                if b: bullets.append(b)

            for a in asteroids:
                a.update()

            for b in bullets:
                b.update()

            # ── Collisions ──────────────────────────────────────
            prect = player.rect()

            # طلقات اللاعب → أعداء
            for b in bullets:
                if b.owner != 1 or not b.active: continue
                for e in enemies:
                    if b.rect().colliderect(e.rect()):
                        b.active = False
                        e.hp -= 1
                        if e.hp <= 0:
                            explosions.append(Explosion(e.x, e.y, big=True))
                            sounds.play("explosion")   # ← صوت الانفجار
                            e.x = -999
                            player.score += 100

            # طلقات اللاعب → كويكبات
            for b in bullets:
                if b.owner != 1 or not b.active: continue
                for a in asteroids:
                    if b.rect().colliderect(a.rect()):
                        b.active = False
                        a.hp -= 1
                        explosions.append(Explosion(a.x, a.y))
                        sounds.play("explosion")       # ← صوت الانفجار
                        if a.hp <= 0:
                            a.x = -999
                            player.score += 30

            # طلقات الأعداء → اللاعب
            for b in bullets:
                if b.owner != -1 or not b.active: continue
                if b.rect().colliderect(prect):
                    b.active = False
                    player.hit(20)
                    explosions.append(Explosion(player.x, player.y))

            # اصطدام مباشر بالعدو
            for e in enemies:
                if e.rect().colliderect(prect):
                    player.hit(30)
                    explosions.append(Explosion(e.x, e.y, big=True))
                    sounds.play("explosion")
                    e.x = -999

            # اصطدام بكويكب
            for a in asteroids:
                if a.rect().colliderect(prect):
                    player.hit(25)
                    explosions.append(Explosion(a.x, a.y, big=True))
                    sounds.play("explosion")
                    a.x = -999

            # ── Cleanup ─────────────────────────────────────────
            bullets    = [b for b in bullets    if b.active]
            enemies    = [e for e in enemies    if e.x > -100]
            asteroids  = [a for a in asteroids  if a.x > -100]

            for ex in explosions: ex.update()
            explosions = [ex for ex in explosions if not ex.done]

            if player.health <= 0:
                state = "dead"
            if player.score >= 3000:
                state = "win"

        # ── Draw ────────────────────────────────────────────────
        screen.fill(DEEP_SPACE)
        screen.blit(nebula, (0, 0))

        for s in stars:
            s.update()
            s.draw(screen, t)

        draw_planet(screen, 680, 130, 65)

        for a in asteroids:
            a.draw(screen)
        for b in bullets:
            b.draw(screen)
        for e in enemies:
            e.draw(screen, t)
        for ex in explosions:
            ex.draw(screen)

        player.draw(screen, t)
        draw_hud(screen, player.score, player.health, player.lives, font_big, font_sm, sounds.enabled)

        if state == "dead":
            draw_overlay(screen, "GAME OVER", "Press R to Restart  |  ESC to Exit", font_big, font_sm, HUD_RED)
        elif state == "win":
            draw_overlay(screen, "YOU WIN!", f"Score: {player.score}  |  Press R to Restart", font_big, font_sm, YELLOW)

        pygame.display.flip()


if __name__ == "__main__":
    main()