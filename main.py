import pygame
import os
import sys
import random
import sqlite3


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


SCREEN_WIDTH = 700
pygame.init()
screen_size = (SCREEN_WIDTH, SCREEN_WIDTH)
screen = pygame.display.set_mode(screen_size)

SCROLL_THRESH = 200
FPS = 60
GRAVITY = 1
MAX_PLATFORMS = 7
scroll = 0
bg_scroll = 0

player_image = load_image("ninja.png")
platform_image = load_image("platform.png")
back_img = load_image("startback.png")
inf_back_img = load_image("background.png")
game_over_screen = load_image("gameover.jpg")
clock = pygame.time.Clock()


def draw_background(bg_scroll):
    screen.blit(inf_back_img, (0, 0 + bg_scroll))
    screen.blit(inf_back_img, (0, -600 + bg_scroll))


class Player:
    def __init__(self, x, y):
        self.image = pygame.transform.scale(player_image, (85, 85))
        self.width = 85
        self.height = 85
        self.max_x = 400
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.vel_y = 0
        self.flip = False

    def move(self):
        dx = 0
        dy = 0
        scroll = 0

        key = pygame.key.get_pressed()
        if key[pygame.K_a] or key[pygame.K_LEFT]:
            dx = -10
            self.flip = True
        if key[pygame.K_RIGHT] or key[pygame.K_d]:
            dx = 10
            self.flip = False

        self.vel_y += GRAVITY
        dy += self.vel_y

        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > 400:
            dx = 400 - self.rect.right

        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery:
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = -20

        if self.rect.bottom + dy > SCREEN_WIDTH:
            dy = 0
            self.vel_y = -20

        if self.rect.top <= SCROLL_THRESH:
            if self.vel_y < 0:
                scroll = -dy

        self.rect.x += dx
        self.rect.y += dy + scroll

        return scroll

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))

    def get_bottom(self):
        return self.rect.bottom


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(platform_image, (100, 50))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        self.rect.y += scroll
        if self.rect.top > SCREEN_WIDTH:
            self.kill()


player = Player(SCREEN_WIDTH // 3, SCREEN_WIDTH - 200)

platform_group = pygame.sprite.Group()

for p in range(MAX_PLATFORMS):
    p_w = random.randint(50, 100)
    p_x = random.randint(0, 300 - p_w)
    p_y = p * random.randint(80, 90)
    platform = Platform(p_x, p_y, p_w)
    platform_group.add(platform)


def terminate():
    pygame.quit()
    sys.exit


def start_screen():
    intro_text = ["Играть",
                  "Обучение",
                  "Бесконечный режим",
                  "Выйти"]
    buttons = []
    name = "Скрытый клинок: Путь ниндзя"

    fon = pygame.transform.scale(load_image('menu.png'), screen_size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 50)

    font_n = pygame.font.Font(None, 60)
    rend_n = font_n.render(name, 1, pygame.Color((127, 199, 255)))
    intro_rect_m = rend_n.get_rect()
    intro_rect_m.top = 25
    screen.blit(rend_n, intro_rect_m)

    text_coord = 300
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color((93, 155, 155)))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += 50

        pygame.draw.rect(screen, pygame.Color(229, 228, 226), intro_rect)
        pygame.draw.rect(screen, pygame.Color(93, 155, 155), intro_rect, 4)

        screen.blit(string_rendered, intro_rect)
        buttons.append(intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONUP:
                if event.pos[0] >= buttons[0].x and event.pos[0] <= buttons[0].right and event.pos[1] >= buttons[0].top \
                        and event.pos[1] <= buttons[0].bottom:
                    levels_screen()
                if event.pos[0] >= buttons[1].x and event.pos[0] <= buttons[1].right and event.pos[1] >= buttons[1].top \
                        and event.pos[1] <= buttons[1].bottom:
                    training_screen()
                if event.pos[0] >= buttons[2].x and event.pos[0] <= buttons[2].right and event.pos[1] >= buttons[2].top \
                        and event.pos[1] <= buttons[2].bottom:
                    infinity_game()
                if event.pos[0] >= buttons[3].x and event.pos[0] <= buttons[3].right and event.pos[1] >= buttons[3].top \
                        and event.pos[1] <= buttons[3].bottom:
                    terminate()
        pygame.display.flip()
        clock.tick(FPS)


def level1():
    lev = True

    score = 0
    platform = Platform(400 // 2 - 100, 700 - 100, 100)
    platform_group.add(platform)

    bg_scroll = 0
    img = pygame.transform.scale(back_img, (400, 700))

    run = True
    while run:

        clock.tick(FPS)

        scroll = player.move()

        bg_scroll += scroll
        if bg_scroll >= 600:
            bg_scroll = 0

        draw_background(bg_scroll)
        pygame.draw.line(screen, (255, 255, 255), (0, SCROLL_THRESH), (700, SCROLL_THRESH))
        screen.blit(img, (0, 0))

        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(40, 60)
            p_x = random.randint(0, 400 - p_w)
            p_y = platform.rect.y - random.randint(80, 100)
            platform = Platform(p_x, p_y, p_w)
            platform_group.add(platform)

        if scroll > 0:
            score += 1

        platform_group.update(scroll)
        platform_group.draw(screen)
        player.draw()
        pygame.draw.rect(screen, pygame.Color(255, 209, 220), (400, 0, 300, 700))

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Счёт: {score}", 1, pygame.Color((93, 155, 155)))
        intro_rect = rend.get_rect()
        intro_rect.top = 70
        intro_rect.x = 420
        screen.blit(rend, intro_rect)

        back_btn = "Назад"
        font = pygame.font.Font(None, 50)
        rend = font.render(back_btn, 1, pygame.Color((93, 155, 155)))
        intro_rect_b = rend.get_rect()
        intro_rect_b.top = 650
        intro_rect_b.x = 570
        intro_rect_b.width = 125
        pygame.draw.rect(screen, pygame.Color(229, 228, 226), intro_rect_b)
        pygame.draw.rect(screen, pygame.Color(93, 155, 155), intro_rect_b, 4)
        screen.blit(rend, intro_rect_b)

        if player.rect.top >= 600:
            game_over_screen(lev)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if score >= 2000:
                game_over_screen_Levels()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.pos[0] >= intro_rect_b.x and event.pos[0] <= intro_rect_b.right and \
                        event.pos[1] >= intro_rect_b.top and event.pos[0] <= intro_rect_b.bottom:
                    levels_screen()
        pygame.display.update()


def level2():
    pass


def level3():
    pass


def level4():
    pass


def level5():
    pass


def game_over_screen(lev=False):
    lev = lev
    fon = pygame.transform.scale(load_image('gameover.jpg'), screen_size)
    screen.blit(fon, (0, 0))

    font = pygame.font.Font(None, 125)
    rend = font.render(f"Вы упали", 1, pygame.Color((127, 199, 255)))
    intro_rect = rend.get_rect()
    intro_rect.top = 20
    intro_rect.x = 175
    screen.blit(rend, intro_rect)

    if not lev:
        back_btn = "Меню"
        font = pygame.font.Font(None, 100)
    else:
        back_btn = "К уровням"
        font = pygame.font.Font(None, 60)

    rend = font.render(back_btn, 1, pygame.Color((93, 155, 155)))
    intro_rect_b = rend.get_rect()
    intro_rect_b.top = 400
    intro_rect_b.x = 200
    intro_rect_b.width = 250
    pygame.draw.rect(screen, pygame.Color(229, 228, 226), intro_rect_b)
    pygame.draw.rect(screen, pygame.Color(93, 155, 155), intro_rect_b, 4)
    screen.blit(rend, intro_rect_b)


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONUP:
                if event.pos[0] >= intro_rect_b.x and event.pos[0] <= intro_rect_b.right and \
                        event.pos[1] >= intro_rect_b.top and event.pos[0] <= intro_rect_b.bottom:
                    if not lev:
                        start_screen()
                    else:
                        levels_screen()

        pygame.display.flip()
        clock.tick(FPS)


def game_over_screen_Levels():
    fon = pygame.transform.scale(load_image('gameover.jpg'), screen_size)
    screen.blit(fon, (0, 0))

    font = pygame.font.Font(None, 125)
    rend = font.render(f"Вы упали", 1, pygame.Color((127, 199, 255)))
    intro_rect = rend.get_rect()
    intro_rect.top = 20
    intro_rect.x = 175
    screen.blit(rend, intro_rect)

    back_btn = "Меню"
    font = pygame.font.Font(None, 100)
    rend = font.render(back_btn, 1, pygame.Color((93, 155, 155)))
    intro_rect_b = rend.get_rect()
    intro_rect_b.top = 400
    intro_rect_b.x = 200
    intro_rect_b.width = 200
    pygame.draw.rect(screen, pygame.Color(229, 228, 226), intro_rect_b)
    pygame.draw.rect(screen, pygame.Color(93, 155, 155), intro_rect_b, 4)
    screen.blit(rend, intro_rect_b)

def training_screen():
    pass


def infinity_game():
    con = sqlite3.connect('data\statistic')
    cur = con.cursor()
    high_score = int(cur.execute('SELECT High_score FROM Statistic WHERE id = 1').fetchone()[0])

    score = 0
    platform = Platform(400 // 2 - 100, 700 - 100, 100)
    platform_group.add(platform)

    bg_scroll = 0
    img = pygame.transform.scale(back_img, (400, 700))

    run = True
    while run:

        clock.tick(FPS)

        scroll = player.move()

        bg_scroll += scroll
        if bg_scroll >= 600:
            bg_scroll = 0

        draw_background(bg_scroll)
        pygame.draw.line(screen, (255, 255, 255), (0, SCROLL_THRESH), (700, SCROLL_THRESH))
        screen.blit(img, (0, 0))

        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(40, 60)
            p_x = random.randint(0, 400 - p_w)
            p_y = platform.rect.y - random.randint(80, 100)
            platform = Platform(p_x, p_y, p_w)
            platform_group.add(platform)

        if scroll > 0:
            score += 1

        platform_group.update(scroll)
        platform_group.draw(screen)
        player.draw()
        pygame.draw.rect(screen, pygame.Color(255, 209, 220), (400, 0, 300, 700))

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Рекорд: {high_score}", 1, pygame.Color((93, 155, 155)))
        intro_rect = rend.get_rect()
        intro_rect.top = 20
        intro_rect.x = 420
        screen.blit(rend, intro_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Счёт: {score}", 1, pygame.Color((93, 155, 155)))
        intro_rect = rend.get_rect()
        intro_rect.top = 70
        intro_rect.x = 420
        screen.blit(rend, intro_rect)

        back_btn = "Назад"
        font = pygame.font.Font(None, 50)
        rend = font.render(back_btn, 1, pygame.Color((93, 155, 155)))
        intro_rect_b = rend.get_rect()
        intro_rect_b.top = 650
        intro_rect_b.x = 570
        intro_rect_b.width = 125
        pygame.draw.rect(screen, pygame.Color(229, 228, 226), intro_rect_b)
        pygame.draw.rect(screen, pygame.Color(93, 155, 155), intro_rect_b, 4)
        screen.blit(rend, intro_rect_b)

        if player.rect.top >= 600:
            game_over_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if score > high_score:
                cur.execute('UPDATE Statistic SET High_score = ? WHERE id = 1', (score,))
                con.commit()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.pos[0] >= intro_rect_b.x and event.pos[0] <= intro_rect_b.right and \
                        event.pos[1] >= intro_rect_b.top and event.pos[0] <= intro_rect_b.bottom:
                    start_screen()

        pygame.display.update()
    con.close()


def levels_screen():
    intro_text = ["1",
                  "2",
                  "3",
                  "4",
                  "5"]
    buttons = []
    name = "Выберите уровень"
    back_btn = "Назад"
    fon = pygame.transform.scale(load_image('levels.jpg'), screen_size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 100)

    font_n = pygame.font.Font(None, 100)
    rend_n = font_n.render(name, 1, pygame.Color((127, 199, 255)))
    intro_rect_m = rend_n.get_rect()
    intro_rect_m.top = 25
    screen.blit(rend_n, intro_rect_m)

    rend = font.render(back_btn, 1, pygame.Color((93, 155, 155)))
    intro_rect_b = rend_n.get_rect()
    intro_rect_b.top = 550
    intro_rect_b.width = 225
    pygame.draw.rect(screen, pygame.Color(229, 228, 226), intro_rect_b)
    pygame.draw.rect(screen, pygame.Color(93, 155, 155), intro_rect_b, 4)
    screen.blit(rend, intro_rect_b)

    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color((93, 155, 155)))
        intro_rect = string_rendered.get_rect()
        text_coord += 60
        intro_rect.right = text_coord
        intro_rect.y = 300
        text_coord += 60

        pygame.draw.rect(screen, pygame.Color(229, 228, 226), intro_rect)
        pygame.draw.rect(screen, pygame.Color(93, 155, 155), intro_rect, 4)

        screen.blit(string_rendered, intro_rect)
        buttons.append(intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.pos[0] >= intro_rect_b.x and event.pos[0] <= intro_rect_b.right and \
                        event.pos[1] >= intro_rect_b.top and event.pos[0] <= intro_rect_b.bottom:
                    start_screen()
                if event.pos[0] >= buttons[0].x and event.pos[0] <= buttons[0].right and \
                        event.pos[1] >= buttons[0].top and event.pos[0] <= buttons[0].bottom:
                    level1()
                if event.pos[0] >= buttons[1].x and event.pos[0] <= buttons[1].right and \
                        event.pos[1] >= buttons[1].top and event.pos[0] <= buttons[1].bottom:
                    level2()
                if event.pos[0] >= buttons[2].x and event.pos[0] <= buttons[2].right and \
                        event.pos[1] >= buttons[2].top and event.pos[0] <= buttons[2].bottom:
                    level3()
                if event.pos[0] >= buttons[3].x and event.pos[0] <= buttons[3].right and \
                        event.pos[1] >= buttons[3].top and event.pos[0] <= buttons[3].bottom:
                    level4()
                if event.pos[0] >= buttons[4].x and event.pos[0] <= buttons[4].right and \
                        event.pos[1] >= buttons[4].top and event.pos[0] <= buttons[4].bottom:
                    level5()
        pygame.display.flip()
        clock.tick(FPS)


start_screen()

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("black")

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
