import pygame
import random
import math
import sys
from datetime import datetime

pygame.init()

# ========== KONFIGURASI ==========
WIDTH, HEIGHT = 1024, 768
FPS = 60
DIFFICULTY = 5  # 1-10, makin tinggi makin sadis

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DARK CORRIDOR V2")
clock = pygame.time.Clock()

# ========== WARNA ==========
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)

# ========== PLAYER ==========
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 3
        self.radius = 15
        self.health = 100
        self.godmode = False
        self.flashlight = True
        self.facing = 0  # 0=atas, 1=kanan, 2=bawah, 3=kiri

    def move(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -self.speed
            self.facing = 0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = self.speed
            self.facing = 2
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -self.speed
            self.facing = 3
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = self.speed
            self.facing = 1

        # Biar ga tembus tembok (simulasi)
        self.x = max(20, min(WIDTH-20, self.x + dx))
        self.y = max(20, min(HEIGHT-20, self.y + dy))

    def draw(self):
        # Badan
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)
        # Arah hadap
        dirs = [(0, -20), (20, 0), (0, 20), (-20, 0)]
        dx, dy = dirs[self.facing]
        pygame.draw.line(screen, RED, (self.x, self.y), (self.x+dx, self.y+dy), 5)

# ========== MUSUH AI ==========
class Enemy:
    def __init__(self, player):
        self.player = player
        self.x = random.randint(50, WIDTH-50)
        self.y = random.randint(50, HEIGHT-50)
        self.radius = 12
        self.speed = 1.2 + (DIFFICULTY * 0.15)
        self.detection_range = 200 + (DIFFICULTY * 10)
        self.attack_cooldown = 0

    def update(self):
        dx = self.player.x - self.x
        dy = self.player.y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.detection_range:
            if dist > 30:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
            else:
                # SERANG PLAYER
                if self.attack_cooldown <= 0:
                    if not self.player.godmode:
                        self.player.health -= 10 + (DIFFICULTY * 2)
                    self.attack_cooldown = 30  # frame cooldown

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def draw(self):
        # Semakin dekat, semakin merah
        dist = math.hypot(self.player.x - self.x, self.player.y - self.y)
        intensity = max(0, min(255, 255 - (dist / 5)))
        color = (intensity, 0, 0)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)

# ========== JUMP SCARE SYSTEM ==========
class JumpScare:
    def __init__(self):
        self.active = False
        self.timer = 0
        self.triggered = False

    def trigger(self):
        if not self.triggered:
            self.active = True
            self.timer = 45  # 0.75 detik
            self.triggered = True

    def update(self):
        if self.active:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False
                self.triggered = False

    def draw(self):
        if self.active:
            # Layar merah + teks "GET OUT!"
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((255, 0, 0))
            screen.blit(overlay, (0, 0))

            font = pygame.font.Font(None, 120)
            text = font.render("GET OUT!", True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))

# ========== GENERASI MAP RANDOM ==========
def generate_map():
    # Simulasi koridor gelap dengan titik-titik "ruang"
    rooms = []
    for _ in range(10 + DIFFICULTY):
        x = random.randint(50, WIDTH-50)
        y = random.randint(50, HEIGHT-50)
        w = random.randint(60, 180)
        h = random.randint(60, 180)
        rooms.append((x, y, w, h))
    return rooms

# ========== MAIN GAME ==========
def main():
    player = Player()
    enemies = [Enemy(player) for _ in range(3 + DIFFICULTY)]
    jumpscare = JumpScare()
    map_rooms = generate_map()
    running = True
    cheat_console = False
    cheat_text = ""
    font = pygame.font.Font(None, 36)

    # Timer jump scare random
    scare_timer = random.randint(120, 300)

    while running:
        clock.tick(FPS)
        screen.fill(BLACK)

        # ========== INPUT ==========
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:  # Cheat console
                    cheat_console = not cheat_console
                if event.key == pygame.K_BACKQUOTE:  # ~
                    cheat_console = True

                if cheat_console:
                    if event.key == pygame.K_RETURN:
                        # Eksekusi cheat
                        if cheat_text == "god":
                            player.godmode = not player.godmode
                        elif cheat_text == "light":
                            player.flashlight = not player.flashlight
                        elif cheat_text == "killall":
                            enemies.clear()
                        elif cheat_text.startswith("tp "):
                            try:
                                _, x, y = cheat_text.split()
                                player.x = int(x)
                                player.y = int(y)
                            except:
                                pass
                        cheat_text = ""
                        cheat_console = False
                    elif event.key == pygame.K_BACKSPACE:
                        cheat_text = cheat_text[:-1]
                    else:
                        cheat_text += event.unicode

        # ========== UPDATE ==========
        player.move(keys)

        # Update musuh
        for enemy in enemies[:]:
            enemy.update()
            # Musuh mati kalo kejauhan (opsional)
            if math.hypot(player.x - enemy.x, player.y - enemy.y) > 800:
                enemies.remove(enemy)

        # Spawn musuh baru kalo kurang
        while len(enemies) < (3 + DIFFICULTY):
            enemies.append(Enemy(player))

        # Jump scare random
        scare_timer -= 1
        if scare_timer <= 0 and not jumpscare.active:
            if random.random() < 0.3:  # 30% chance
                jumpscare.trigger()
            scare_timer = random.randint(150, 400)

        jumpscare.update()

        # ========== DRAW ==========
        # Gambar ruangan (koridor gelap)
        for room in map_rooms:
            x, y, w, h = room
            pygame.draw.rect(screen, GRAY, (x, y, w, h), 2)
            # Efek "gelap" di tepi (simulasi senter)
            if player.flashlight:
                flash_x = player.x + random.randint(-15, 15)
                flash_y = player.y + random.randint(-15, 15)
                for i in range(3):
                    alpha = 50 - i*15
                    rad = 150 - i*30
                    surf = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (255, 255, 200, alpha), (rad, rad), rad)
                    screen.blit(surf, (flash_x-rad, flash_y-rad))

        # Gambar player & musuh
        player.draw()
        for enemy in enemies:
            enemy.draw()

        # Jump scare
        jumpscare.draw()

        # HUD
        health_text = font.render(f"HP: {player.health}", True, WHITE)
        screen.blit(health_text, (20, 20))

        enemy_text = font.render(f"Enemies: {len(enemies)}", True, RED)
        screen.blit(enemy_text, (20, 60))

        if player.godmode:
            god_text = font.render("GODMODE ON", True, (0, 255, 0))
            screen.blit(god_text, (WIDTH-200, 20))

        # Cheat console
        if cheat_console:
            pygame.draw.rect(screen, BLACK, (50, HEIGHT-80, WIDTH-100, 50))
            pygame.draw.rect(screen, WHITE, (50, HEIGHT-80, WIDTH-100, 50), 2)
            text_surf = font.render(cheat_text, True, WHITE)
            screen.blit(text_surf, (60, HEIGHT-70))

        pygame.display.flip()

        # Game Over
        if player.health <= 0:
            screen.fill(BLACK)
            font_big = pygame.font.Font(None, 80)
            over = font_big.render("YOU DIED", True, RED)
            screen.blit(over, (WIDTH//2 - over.get_width()//2, HEIGHT//2 - 50))
            pygame.display.flip()
            pygame.time.delay(3000)
            running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
