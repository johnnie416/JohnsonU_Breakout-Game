import pygame
import random
import sys
import json
import array

# --- Game setup ---
pygame.init()
pygame.mixer.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Johnson U. Breakout - Epic Portfolio Edition")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 150, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
PURPLE = (200, 0, 200)

# Fonts
FONT = pygame.font.SysFont("Arial", 24)
BIG_FONT = pygame.font.SysFont("Arial", 48)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# High score file
HIGH_SCORE_FILE = "high_score.json"

# --- Embedded Sound Effects ---
def make_sound(freq=440, duration_ms=100, volume=0.5):
    framerate = 44100
    n_samples = int(framerate * duration_ms / 1000)
    buf = array.array("h", [int(32767 * volume * ((i % int(framerate/freq)) < int(framerate/(freq*2)))*2-1) for i in range(n_samples)])
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

PADDLE_HIT_SOUND = make_sound(600, 50, 0.5)  # short pop
BRICK_HIT_SOUND = make_sound(400, 100, 0.5)  # longer blip

# --- Utility Functions ---
def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return json.load(f).get("high_score", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as f:
        json.dump({"high_score": score}, f)

def draw_text(text, font, color, x, y, center=False):
    label = font.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    SCREEN.blit(label, rect)

# --- Classes ---
class Paddle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = 120
        self.height = 15
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)
        self.speed = 8

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

    def enlarge(self):
        self.width = min(self.width + 40, 200)
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(midtop=self.rect.midtop)

    def shrink(self):
        self.width = max(self.width - 40, 60)
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(RED)
        self.rect = self.image.get_rect(midtop=self.rect.midtop)

class Ball(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (7, 7), 7)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed_x = random.choice([-speed, speed])
        self.speed_y = -speed
        self.default_speed = speed

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x *= -1
        if self.rect.top <= 0:
            self.speed_y *= -1



    def reset(self):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed_x = random.choice([-self.default_speed, self.default_speed])
        self.speed_y = -self.default_speed

class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((70, 20))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.kind = kind
        if kind == "life":
            self.image.fill(GREEN)
        elif kind == "enlarge":
            self.image.fill(BLUE)
        elif kind == "shrink":
            self.image.fill(RED)
        elif kind == "slow":
            self.image.fill(YELLOW)
        elif kind == "multi":
            self.image.fill(PURPLE)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# --- Particle Class for Background and Trail ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, size, color, speed):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color + (150,), (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.bottom = 0
            self.rect.x = random.randint(0, SCREEN_WIDTH)

# --- Functions ---
def create_bricks(level):
    bricks = pygame.sprite.Group()
    colors = [RED, ORANGE, GREEN, BLUE, PURPLE]
    rows = 4 + level
    cols = 10
    for row in range(rows):
        for col in range(cols):
            brick = Brick(10 + col * 78, 50 + row * 30, random.choice(colors))
            bricks.add(brick)
    return bricks

def choose_difficulty():
    options = [
        {"label": "Easy (Slow ball, 5 lives)", "speed": 3, "lives": 5},
        {"label": "Normal (Default, 3 lives)", "speed": 4, "lives": 3},
        {"label": "Hard (Fast ball, 2 lives)", "speed": 6, "lives": 2},
    ]
    selected = 0
    choosing = True
    while choosing:
        SCREEN.fill(BLACK)
        draw_text("Johnson U. Breakout", BIG_FONT, WHITE, SCREEN_WIDTH // 2, 150, True)
        draw_text("Choose Difficulty", FONT, WHITE, SCREEN_WIDTH // 2, 200, True)
        for i, opt in enumerate(options):
            color = GREEN if i == selected else WHITE
            draw_text(opt["label"], FONT, color, SCREEN_WIDTH // 2, 250 + i * 50, True)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return options[selected]
            if event.type == pygame.MOUSEMOTION:
                mx, my = pygame.mouse.get_pos()
                for i, opt in enumerate(options):
                    text_rect = FONT.render(opt["label"], True, WHITE).get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 50))
                    if text_rect.collidepoint(mx, my):
                        selected = i
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i, opt in enumerate(options):
                    text_rect = FONT.render(opt["label"], True, WHITE).get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 50))
                    if text_rect.collidepoint(mx, my):
                        return options[i]

# --- Main Game Loop ---
def main():
    high_score = load_high_score()
    settings = choose_difficulty()
    ball_speed = settings["speed"]
    lives = settings["lives"]

    paddle = Paddle()
    ball = Ball(ball_speed)
    balls = pygame.sprite.Group()
    balls.add(ball)

    all_sprites = pygame.sprite.Group()
    all_sprites.add(paddle, ball)

    level = 1
    bricks = create_bricks(level)
    powerups = pygame.sprite.Group()
    global particles
    particles = pygame.sprite.Group()

    # Pre-fill background particles
    for _ in range(50):
        p = Particle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), 4, WHITE, random.uniform(0.5, 1.5))
        particles.add(p)

    score = 0
    running = True
    paused = False

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused

        if paused:
            SCREEN.fill(BLACK)
            draw_text("PAUSED", BIG_FONT, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, True)
            pygame.display.flip()
            continue

        all_sprites.update()
        powerups.update()
        particles.update()

        # Ball collisions
        for ball in balls:
            if pygame.sprite.collide_rect(ball, paddle):
                ball.speed_y *= -1
                PADDLE_HIT_SOUND.play()

            hit_bricks = pygame.sprite.spritecollide(ball, bricks, True)
            if hit_bricks:
                ball.speed_y *= -1
                score += len(hit_bricks) * 10
                BRICK_HIT_SOUND.play()
                if random.random() < 0.2:
                    power = random.choice(["life", "enlarge", "shrink", "slow", "multi"])
                    p = PowerUp(ball.rect.centerx, ball.rect.centery, power)
                    powerups.add(p)
                    all_sprites.add(p)

            if ball.rect.bottom >= SCREEN_HEIGHT:
                lives -= 1
                ball.reset()
                if lives == 0:
                    running = False

        # Paddle collects powerups
        for power in pygame.sprite.spritecollide(paddle, powerups, True):
            if power.kind == "life":
                lives += 1
            elif power.kind == "enlarge":
                paddle.enlarge()
            elif power.kind == "shrink":
                paddle.shrink()
            elif power.kind == "slow":
                for b in balls:
                    b.speed_x = max(-3, min(b.speed_x, 3))
                    b.speed_y = max(-3, min(b.speed_y, 3))
            elif power.kind == "multi":
                new_ball = Ball(ball_speed)
                new_ball.rect.center = paddle.rect.center
                balls.add(new_ball)
                all_sprites.add(new_ball)

        if not bricks:
            level += 1
            ball.reset()
            bricks = create_bricks(level)
            all_sprites.add(bricks)

        # Draw everything
        SCREEN.fill(BLACK)
        particles.draw(SCREEN)
        all_sprites.draw(SCREEN)
        bricks.draw(SCREEN)
        draw_text(f"Score: {score}", FONT, WHITE, 10, 10)
        draw_text(f"Lives: {lives}", FONT, WHITE, SCREEN_WIDTH - 120, 10)
        draw_text(f"Level: {level}", FONT, WHITE, SCREEN_WIDTH // 2 - 30, 10)
        draw_text(f"High Score: {high_score}", FONT, WHITE, SCREEN_WIDTH // 2 + 80, 10)
        pygame.display.flip()

    # Game over screen
    if score > high_score:
        save_high_score(score)
        high_score = score

    while True:
        SCREEN.fill(BLACK)
        particles.update()
        particles.draw(SCREEN)
        draw_text("GAME OVER", BIG_FONT, RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, True)
        draw_text(f"Your Score: {score}", FONT, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10, True)
        draw_text(f"High Score: {high_score}", FONT, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, True)
        draw_text("Thanks for playing Johnson U.'s Breakout!", FONT, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100, True)
        draw_text("Press ENTER to play again or ESC to quit", FONT, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150, True)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    main()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

# --- Run the game ---
if __name__ == "__main__":
    main()