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


SCREEN_WIDTH = SCREEN_HEIGHT = 700
GAME_SCREEN_WIDTH = 450
SCROLL_THRESH = 200
FPS = 60
GRAVITY = 1
scroll = 0
bg_scroll = 0

pygame.init()
screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
screen = pygame.display.set_mode(screen_size)

MAX_PLATFORMS = 10
MAX_SURIKENS = 2

SKY_COLOR = pygame.Color((127, 199, 255))
LIGHT_BLUE_COLOR = pygame.Color((93, 155, 155))
SAKURA_COLOR = pygame.Color((255, 209, 220))
INSIDE_BTN_COLOR = pygame.Color(229, 228, 226)
FRAME_BTN_COLOR = pygame.Color(93, 155, 155)

class Player:
    def __init__(self, x, y):
        self.image = pygame.transform.scale(player_image, (45, 45))
        self.width = 25
        self.height = 40
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
        if self.rect.right + dx > GAME_SCREEN_WIDTH:
            dx = GAME_SCREEN_WIDTH - self.rect.right

        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery:
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = -20

        if self.rect.bottom + dy > SCREEN_HEIGHT:
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


class SpriteSheet:
    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame, width, height, scale, color):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), ((frame * width), 0, width, height))
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        image.set_colorkey(color)
        return image


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, moving):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(platform_image, (width, 50))
        self.moving = moving
        self.move_counter = random.randint(0, 50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):

        if self.moving == True:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed

        if self.move_counter >= 150 or self.rect.left < 0 or self.rect.right > GAME_SCREEN_WIDTH:
            self.direction *= -1
            self.move_counter = 0

        self.rect.y += scroll

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, y, sprite_sheet, scale, enemy_speed=2):
        pygame.sprite.Sprite.__init__(self)

        self.animation_list = []
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.enemy_speed = enemy_speed
        self.direction = random.choice([-1, 1])
        if self.direction == 1:
            self.flip = True
        else:
            self.flip = False

        animation_steps = 8
        for animation in range(animation_steps):
            image = sprite_sheet.get_image(animation, 32, 32, scale, (0, 0, 0))
            image = pygame.transform.flip(image, self.flip, False)
            image.set_colorkey((0, 0, 0))
            self.animation_list.append(image)

        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect()

        if self.direction == 1:
            self.rect.x = 0
        else:
            self.rect.x = GAME_SCREEN_WIDTH

        self.rect.y = y

    def update(self, scroll):

        ANIMATION_COOLDOWN = 50

        self.image = self.animation_list[self.frame_index]

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0

        self.rect.x += self.direction * self.enemy_speed
        self.rect.y += scroll

        if self.rect.right < 0 or self.rect.left > GAME_SCREEN_WIDTH:
            if self.direction == 1:
                self.rect.x = 0
            else:
                self.rect.x = GAME_SCREEN_WIDTH

        if self.rect.bottom > SCREEN_HEIGHT:
            self.kill()

    def suriken_kill_counter(self, other_x, other_y):
        if self.rect.x - 10 <= other_x <= self.rect.right - 10 and \
                self.rect.y <= other_y <= self.rect.bottom:
            self.kill()
            return 1
        return 0


class Suriken(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(sur_img, (20, 20))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.y -= 15
        if self.rect.top < 0:
            self.kill()

tutorial_image = load_image("tutorial.jpg")
player_image = load_image("ninja.png")
platform_image = load_image("platform.png")
back_img = load_image("startback.png")
inf_back_img = load_image("background.png")
game_over_sc = load_image("gameover.jpg")
sur_img = load_image("suriken.png")
bird_hunt_bg = load_image("birds_hunt.jpg")
enemy_sheet_img = load_image("bird.png")
enemy_sheet = SpriteSheet(enemy_sheet_img)

player = Player(SCREEN_WIDTH // 3, SCREEN_WIDTH - 200)
platform_group = pygame.sprite.Group()
surikens_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
clock = pygame.time.Clock()


def draw_background(bg_scroll):
    screen.blit(inf_back_img, (0, 0 + bg_scroll))
    screen.blit(inf_back_img, (0, -700 + bg_scroll))


def terminate():
    pygame.quit()
    sys.exit()


def empty_groups():
    surikens_group.empty()
    platform_group.empty()
    enemy_group.empty()


def start_screen():
    intro_text = [" Играть ",
                  " Обучение ",
                  " Бесконечный режим ",
                  " Выйти "]
    buttons = []
    name = "Скрытый клинок: Путь ниндзя"

    empty_groups()

    fon = pygame.transform.scale(load_image('menu.png'), screen_size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 50)

    font_n = pygame.font.Font(None, 60)
    rend_n = font_n.render(name, 1, SKY_COLOR)
    intro_rect_m = rend_n.get_rect()
    intro_rect_m.center = (SCREEN_WIDTH // 2, 20)
    screen.blit(rend_n, intro_rect_m)

    text_coord = 300
    for line in intro_text:
        string_rendered = font.render(line, 1, LIGHT_BLUE_COLOR)
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += 50

        pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect)
        pygame.draw.rect(screen, LIGHT_BLUE_COLOR, intro_rect, 4)

        screen.blit(string_rendered, intro_rect)
        buttons.append(intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONUP:
                if buttons[0].left <= event.pos[0] <= buttons[0].right and \
                        buttons[0].top <= event.pos[1] <= buttons[0].bottom:
                    levels_screen()
                if buttons[1].left <= event.pos[0] <= buttons[1].right and \
                        buttons[1].top <= event.pos[1] <= buttons[1].bottom:
                    training_screen()
                if buttons[2].left <= event.pos[0] <= buttons[2].right and \
                        buttons[2].top <= event.pos[1] <= buttons[2].bottom:
                    infinity_game()
                if buttons[3].left <= event.pos[0] <= buttons[3].right and \
                        buttons[3].top <= event.pos[1] <= buttons[3].bottom:
                    terminate()
        pygame.display.flip()
        clock.tick(FPS)


def levels_screen():
    con = sqlite3.connect('data\statistic')
    cur = con.cursor()
    levels = cur.execute('SELECT * FROM Statistic').fetchone()
    empty_groups()
    intro_text = [" 1 ", " 2 ", " 3 ", " 4 "]
    buttons = []
    name = " Выберите уровень "
    back_btn = "Назад"
    fon = pygame.transform.scale(load_image('levels.jpg'), screen_size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 100)

    font_n = pygame.font.Font(None, 100)
    rend_n = font_n.render(name, 1, SKY_COLOR)
    intro_rect_m = rend_n.get_rect()
    intro_rect_m.x = 30
    intro_rect_m.y = 20
    screen.blit(rend_n, intro_rect_m)

    rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
    intro_rect_b = rend_n.get_rect()
    intro_rect_b.x = 20
    intro_rect_b.y = 550
    intro_rect_b.width = 225
    pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
    pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
    screen.blit(rend, intro_rect_b)

    text_coord = 150
    for line in intro_text:
        string_rendered = font.render(line, 1, LIGHT_BLUE_COLOR)
        intro_rect = string_rendered.get_rect()
        text_coord += 60
        intro_rect.right = text_coord
        intro_rect.y = 300
        text_coord += 60

        pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect)
        pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect, 4)

        screen.blit(string_rendered, intro_rect)
        buttons.append(intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    start_screen()

                if buttons[0].left <= event.pos[0] <= buttons[0].right and \
                        buttons[0].top <= event.pos[1] <= buttons[0].bottom:
                    level1()

                if buttons[1].left <= event.pos[0] <= buttons[1].right and \
                        buttons[1].top <= event.pos[1] <= buttons[1].bottom and levels[2] == 1:
                    level2()

                if buttons[2].left <= event.pos[0] <= buttons[2].right and \
                        buttons[2].top <= event.pos[1] <= buttons[2].bottom and levels[3] == 1:
                    level3()

                if buttons[3].left <= event.pos[0] <= buttons[3].right and \
                        buttons[3].top <= event.pos[1] <= buttons[3].bottom and levels[4] == 1:
                    level4()

        pygame.display.flip()
        clock.tick(FPS)


def level1():
    con = sqlite3.connect('data\statistic')
    cur = con.cursor()

    score = 0
    bg_scroll = 0
    platform = Platform(150, SCREEN_HEIGHT - 100, 200, False)
    platform_group.add(platform)

    run = True
    while run:

        clock.tick(FPS)

        scroll = player.move()

        bg_scroll += scroll

        if bg_scroll >= 700:
            bg_scroll = 0

        draw_background(bg_scroll)

        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(80, 100)
            p_x = random.randint(0, 450 - p_w)
            p_y = platform.rect.y - random.randint(80, 100)
            p_type = random.randint(1, 2)
            if p_type == 1 and score > 300:
                p_moving = True
            else:
                p_moving = False
            platform = Platform(p_x, p_y, p_w, p_moving)
            platform_group.add(platform)

        if scroll > 0:
            score += 1

        platform_group.update(scroll)
        platform_group.draw(screen)
        player.draw()

        pygame.draw.rect(screen, SAKURA_COLOR, (450, 0, 250, 700))

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Уровень 1", 1, LIGHT_BLUE_COLOR)
        lvl_rect = rend.get_rect()
        lvl_rect.center = (575, 40)
        screen.blit(rend, lvl_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Цель: 2000", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 100)
        screen.blit(rend, intro_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Счёт:  {score}", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 160)
        screen.blit(rend, intro_rect)

        back_btn = " Назад "
        font = pygame.font.Font(None, 50)
        rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
        intro_rect_b = rend.get_rect()
        intro_rect_b.top = 650
        intro_rect_b.x = 570
        intro_rect_b.width = 125
        pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
        pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
        screen.blit(rend, intro_rect_b)

        if player.rect.top >= SCREEN_HEIGHT - 80:
            game_over_screen(score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if score >= 2000:
                cur.execute('UPDATE Statistic SET Level2 = 1 WHERE id = 1')
                con.commit()
                con.close()
                game_over_screen(score, False, True)

            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    levels_screen()
        pygame.display.update()


def level2():
    con = sqlite3.connect('data\statistic')
    cur = con.cursor()
    score = 0
    enemy_time = 0
    platform = Platform(100, 600, 250, False)
    platform_group.add(platform)
    bg_scroll = 0

    run = True
    while run:
        enemy_time += 1
        clock.tick(FPS)
        scroll = player.move()

        bg_scroll += scroll
        if bg_scroll >= 700:
            bg_scroll = 0

        draw_background(bg_scroll)

        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(80, 100)
            p_x = random.randint(0, 450 - p_w)
            p_y = platform.rect.y - random.randint(80, 100)
            p_type = random.randint(1, 2)
            if p_type == 1 and score > 100:
                p_moving = True
            else:
                p_moving = False
            platform = Platform(p_x, p_y, p_w, p_moving)
            platform_group.add(platform)

        if len(enemy_group) == 0 and enemy_time > 50 and score > 250:
            enemy = Enemy(100, enemy_sheet, 1.5)
            enemy_group.add(enemy)

        enemy_group.update(scroll)
        platform_group.update(scroll)

        if scroll > 0:
            score += 1

        platform_group.draw(screen)
        enemy_group.draw(screen)
        player.draw()

        if player.rect.top >= SCREEN_HEIGHT - 80:
            game_over_screen(score)

        if pygame.sprite.spritecollide(player, enemy_group, False):
            game_over_screen(score, False, False)

        if score >= 1200:
            cur.execute('UPDATE Statistic SET Level3 = 1 WHERE id = 1')
            con.commit()
            con.close()
            game_over_screen(score, False, True)

        pygame.draw.rect(screen, SAKURA_COLOR, (450, 0, 250, 700))

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Уровень 2", 1, LIGHT_BLUE_COLOR)
        lvl_rect = rend.get_rect()
        lvl_rect.center = (575, 40)
        screen.blit(rend, lvl_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Цель: 1200", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 100)
        screen.blit(rend, intro_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Счёт:  {score}", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 160)
        screen.blit(rend, intro_rect)

        back_btn = " Назад "
        font = pygame.font.Font(None, 50)
        rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
        intro_rect_b = rend.get_rect()
        intro_rect_b.top = 650
        intro_rect_b.x = 570
        intro_rect_b.width = 125
        pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
        pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
        screen.blit(rend, intro_rect_b)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    levels_screen()

        pygame.display.update()


def level3():
    con = sqlite3.connect('data\statistic')
    cur = con.cursor()
    score = 0
    enemy_time = 0
    bg_scroll = 0
    platform = Platform(100, 600, 250, False)
    platform_group.add(platform)

    run = True
    while run:
        enemy_time += 1
        clock.tick(FPS)
        scroll = player.move()
        bg_scroll += scroll

        if bg_scroll >= 700:
            bg_scroll = 0

        draw_background(bg_scroll)

        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(80, 100)
            p_x = random.randint(0, 450 - p_w)
            p_y = platform.rect.y - random.randint(80, 100)
            p_type = random.randint(1, 2)
            if p_type == 1 and score > 300:
                p_moving = True
            else:
                p_moving = False
            platform = Platform(p_x, p_y, p_w, p_moving)
            platform_group.add(platform)

        if len(enemy_group) == 0 and enemy_time > 150:
            enemy = Enemy(100, enemy_sheet, 1.5)
            enemy_group.add(enemy)

        if pygame.key.get_pressed()[pygame.K_SPACE] and len(surikens_group) < 2:
            suriken = Suriken(player.rect.x, player.rect.y)
            surikens_group.add(suriken)

        for suriken in surikens_group:
            if pygame.sprite.spritecollide(suriken, enemy_group, True):
                enemy_time = 0

        platform_group.update(scroll)
        surikens_group.update()
        enemy_group.update(scroll)

        if scroll > 0:
            score += 1

        surikens_group.draw(screen)
        platform_group.draw(screen)
        enemy_group.draw(screen)
        player.draw()

        if score >= 1200:
            cur.execute('UPDATE Statistic SET Level4 = 1 WHERE id = 1')
            con.commit()
            con.close()
            game_over_screen(score, False, True)

        if player.rect.top >= SCREEN_HEIGHT - 80:
            game_over_screen(score)

        if pygame.sprite.spritecollide(player, enemy_group, False):
            game_over_screen(score, False, False)

        pygame.draw.rect(screen, SAKURA_COLOR, (450, 0, 250, 700))

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Уровень 3", 1, LIGHT_BLUE_COLOR)
        lvl_rect = rend.get_rect()
        lvl_rect.center = (575, 40)
        screen.blit(rend, lvl_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Цель: 1200", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 100)
        screen.blit(rend, intro_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Счёт:  {score}", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 160)
        screen.blit(rend, intro_rect)

        back_btn = " Назад "
        font = pygame.font.Font(None, 50)
        rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
        intro_rect_b = rend.get_rect()
        intro_rect_b.top = 650
        intro_rect_b.x = 570
        intro_rect_b.width = 125
        pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
        pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
        screen.blit(rend, intro_rect_b)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    levels_screen()

        pygame.display.update()


def level4():
    player.rect.y = 0
    player.vel_y = 0
    MAX_SURIKENS = 2
    score = 0
    god_mode = False
    img = pygame.transform.scale(bird_hunt_bg, (450, 700))
    for en in range(1, 3):
        p_w = random.randint(80, 100)
        p_x = random.randint(0, 450 - p_w)
        p_y = SCREEN_WIDTH - 50 * en
        platform = Platform(p_x, p_y, p_w, True)
        platform_group.add(platform)

    run = True
    while run:

        clock.tick(FPS)
        player.move()

        draw_background(0)
        screen.blit(img, (0, 0))

        if len(enemy_group) < 5:
            y_pos = random.randint(100, 400)
            enemy_speed = random.randint(2, 5)
            enemy = Enemy(y_pos, enemy_sheet, 1.5, enemy_speed)
            enemy_group.add(enemy)

        if pygame.key.get_pressed()[pygame.K_SPACE] and len(surikens_group) < MAX_SURIKENS:
            suriken = Suriken(player.rect.x, player.rect.y)
            surikens_group.add(suriken)

        for suriken in surikens_group:
            for enemy in enemy_group:
                score += enemy.suriken_kill_counter(suriken.rect.x, suriken.rect.y)

        enemy_group.update(0)
        platform_group.update(0)
        surikens_group.update()

        platform_group.draw(screen)
        enemy_group.draw(screen)
        surikens_group.draw(screen)
        player.draw()

        if score >= 100:
            game_over_screen(score, False, True)

        if player.rect.top >= SCREEN_HEIGHT - 80:
            game_over_screen(score)

        pygame.draw.rect(screen, SAKURA_COLOR, (450, 0, 250, 700))

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Уровень 4", 1, LIGHT_BLUE_COLOR)
        lvl_rect = rend.get_rect()
        lvl_rect.center = (575, 40)
        screen.blit(rend, lvl_rect)

        font = pygame.font.Font(None, 40)
        rend = font.render(f"Цель: 100 птиц", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 100)
        screen.blit(rend, intro_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Счёт:  {score}", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.center = (575, 160)
        screen.blit(rend, intro_rect)

        back_btn = " Назад "
        font = pygame.font.Font(None, 50)
        rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
        intro_rect_b = rend.get_rect()
        intro_rect_b.top = 650
        intro_rect_b.x = 570
        intro_rect_b.width = 125
        pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
        pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
        screen.blit(rend, intro_rect_b)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    levels_screen()

            if pygame.key.get_pressed()[pygame.K_g]:
                if god_mode:
                    MAX_SURIKENS = 100
                else:
                    MAX_SURIKENS = 2
                god_mode = not god_mode

        pygame.display.update()


def game_over_screen(score, inf_lev=False, win=False):
    empty_groups()
    player.rect.x, player.rect.y = SCREEN_WIDTH // 3, SCREEN_HEIGHT - 200

    bg = pygame.transform.scale(load_image('gameover.jpg'), screen_size)
    screen.blit(bg, (0, 0))

    if not win:
        text = "Вы проиграли"
    else:
        text = "Вы прошли уровень"

    font = pygame.font.Font(None, 75)
    rend = font.render(text, 1, SKY_COLOR)
    intro_rect = rend.get_rect()
    intro_rect.center = (SCREEN_WIDTH // 2, 40)
    screen.blit(rend, intro_rect)

    if inf_lev:
        back_btn = " Меню "
    else:
        back_btn = " К уровням "
    font = pygame.font.Font(None, 60)
    rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
    intro_rect_b = rend.get_rect()
    intro_rect_b.center = (SCREEN_WIDTH // 2, 400)
    pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
    pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
    screen.blit(rend, intro_rect_b)

    font = pygame.font.Font(None, 80)
    score_text = f" Счёт: {score} "
    rend = font.render(score_text, 1, LIGHT_BLUE_COLOR)
    score_rect = rend.get_rect()
    score_rect.center = (SCREEN_WIDTH // 2, 300)
    pygame.draw.rect(screen, INSIDE_BTN_COLOR, score_rect)
    pygame.draw.rect(screen, FRAME_BTN_COLOR, score_rect, 4)
    screen.blit(rend, score_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    if inf_lev:
                        start_screen()
                    else:
                        levels_screen()

        pygame.display.flip()
        clock.tick(FPS)


def training_screen():
    bg = pygame.transform.scale(tutorial_image, screen_size)
    screen.blit(bg, (0, 0))
    font = pygame.font.Font(None, 100)
    text = "Управление"
    rend = font.render(text, 1, SKY_COLOR)
    intro_rect = rend.get_rect()
    intro_rect.x = 150
    intro_rect.y = 20
    screen.blit(rend, intro_rect)

    font = pygame.font.Font(None, 30)
    text = "Чтобы двигаться влево/вправо используйте клавиши w/a или <-/->."
    rend = font.render(text, 1, SKY_COLOR)
    intro_rect = rend.get_rect()
    intro_rect.x = 20
    intro_rect.y = 100
    screen.blit(rend, intro_rect)

    font = pygame.font.Font(None, 25)
    text = "На 3 и 4 уровне вам будут доступны сюрикены."
    rend = font.render(text, 1, SKY_COLOR)
    intro_rect = rend.get_rect()
    intro_rect.x = 20
    intro_rect.y = 150
    screen.blit(rend, intro_rect)

    font = pygame.font.Font(None, 25)
    text = "Чтобы их использовать используйте пробел"
    rend = font.render(text, 1, SKY_COLOR)
    intro_rect = rend.get_rect()
    intro_rect.x = 20
    intro_rect.y = 180
    screen.blit(rend, intro_rect)

    font = pygame.font.Font(None, 50)
    back_btn = "Назад"
    rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
    intro_rect_b = rend.get_rect()
    intro_rect_b.x = 20
    intro_rect_b.y = 550
    intro_rect_b.width = 225
    pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
    pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
    screen.blit(rend, intro_rect_b)

    screen.blit(rend, intro_rect_b)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    start_screen()

        pygame.display.flip()
        clock.tick(FPS)


def infinity_game():
    con = sqlite3.connect('data\statistic')
    cur = con.cursor()
    high_score = int(cur.execute('SELECT High_score FROM Statistic WHERE id = 1').fetchone()[0])
    score = 0
    d = 0
    platform = Platform(100, 600, 250, False)
    platform_group.add(platform)
    bg_scroll = 0

    run = True
    while run:
        d += 1
        clock.tick(FPS)
        scroll = player.move()
        bg_scroll += scroll

        if bg_scroll >= 700:
            bg_scroll = 0

        draw_background(bg_scroll)

        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(80, 100)
            p_x = random.randint(0, 450 - p_w)
            p_y = platform.rect.y - random.randint(80, 100)
            p_type = random.randint(1, 2)
            if p_type == 1 and score > 300:
                p_moving = True
            else:
                p_moving = False
            platform = Platform(p_x, p_y, p_w, p_moving)
            platform_group.add(platform)

        if len(enemy_group) == 0 and d > 150 and score > 2000:
            enemy = Enemy(100, enemy_sheet, 1.5)
            enemy_group.add(enemy)

        if pygame.key.get_pressed()[pygame.K_SPACE] and len(surikens_group) < 2:
            suriken = Suriken(player.rect.x, player.rect.y)
            surikens_group.add(suriken)

        platform_group.update(scroll)
        surikens_group.update()
        enemy_group.update(scroll)

        if scroll > 0:
            score += 1

        surikens_group.draw(screen)
        platform_group.draw(screen)
        enemy_group.draw(screen)
        player.draw()

        if player.rect.top >= SCREEN_HEIGHT - 80:
            game_over_screen(score, True)

        if pygame.sprite.spritecollide(player, enemy_group, False):
            game_over_screen(score, True)

        for suriken in surikens_group:
            if pygame.sprite.spritecollide(suriken, enemy_group, False):
                d = 0
                enemy_group.empty()

        pygame.draw.rect(screen, SAKURA_COLOR, (450, 0, 250, 700))

        font = pygame.font.Font(None, 32)
        rend = font.render(f"Бесконечный уровень", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.top = 20
        intro_rect.x = 450
        screen.blit(rend, intro_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Счёт: {score}", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.top = 70
        intro_rect.x = 500
        screen.blit(rend, intro_rect)

        font = pygame.font.Font(None, 50)
        rend = font.render(f"Рекорд: {high_score}", 1, LIGHT_BLUE_COLOR)
        intro_rect = rend.get_rect()
        intro_rect.top = 130
        intro_rect.x = 450
        screen.blit(rend, intro_rect)

        back_btn = " Назад"
        font = pygame.font.Font(None, 50)
        rend = font.render(back_btn, 1, LIGHT_BLUE_COLOR)
        intro_rect_b = rend.get_rect()
        intro_rect_b.x = 570
        intro_rect_b.y = 650
        intro_rect_b.width = 125
        pygame.draw.rect(screen, INSIDE_BTN_COLOR, intro_rect_b)
        pygame.draw.rect(screen, FRAME_BTN_COLOR, intro_rect_b, 4)
        screen.blit(rend, intro_rect_b)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONUP:
                if intro_rect_b.left <= event.pos[0] <= intro_rect_b.right and \
                        intro_rect_b.top <= event.pos[1] <= intro_rect_b.bottom:
                    start_screen()

            if score > high_score:
                cur.execute('UPDATE Statistic SET High_score = ? WHERE id = 1', (score,))
                con.commit()

        pygame.display.update()
    con.close()


def main():
    pygame.init()
    pygame.display.set_caption('СКРЫТЫЙ КЛИНОК: ПУТЬ НИНДЗЯ')
    start_screen()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((0, 0, 0))
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
