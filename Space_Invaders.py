import pygame
import sys
import random
from pygame import mixer

# Starting pygame
pygame.init()
pygame.display.set_caption('Space Invaders')

# Constant Variables
screen_width = 700
screen_height = 700

clock = pygame.time.Clock()
screen = pygame.display.set_mode((screen_width, screen_height))

enemy_laser = pygame.USEREVENT + 1
pygame.time.set_timer(enemy_laser, 800)

shape = [
    '  xxxxxxx',
    ' xxxxxxxxx',
    'xxxxxxxxxxx',
    'xxxxxxxxxxx',
    'xxxxxxxxxxx',
    'xxx     xxx',
    'xx       xx']


class Enemy(pygame.sprite.Sprite):
    def __init__(self, color, x, y):
        super().__init__()
        image_path = 'Space Invaders Sprites/' + color + '.png'
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))

        if color == 'red':
            self.value = 100
        elif color == 'green':
            self.value = 200
        else:
            self.value = 300

    def update(self, direction):
        self.rect.x += direction


class Bonus(pygame.sprite.Sprite):
    def __init__(self, side):
        super().__init__()
        self.image = pygame.image.load('Space Invaders Sprites/extra.png').convert_alpha()

        self.bonus_sound = pygame.mixer.Sound('Sounds/ufo_highpitch.wav')
        self.bonus_sound.set_volume(0.2)

        self.last_play_time = 0

        if side == 'right':
            x = screen_width + 50
            self.speed = -3
        else:
            self.speed = 3
            x = -50

        self.rect = self.image.get_rect(topleft=(x, 80))

    def update(self):
        self.rect.x += self.speed

        current_time = pygame.time.get_ticks()
        if current_time - self.last_play_time >= 150:
            if self.rect.right > 0 and self.rect.left < screen_width:
                self.bonus_sound.play()
                self.last_play_time = current_time
            else:
                self.bonus_sound.stop()


class Block(pygame.sprite.Sprite):
    def __init__(self, size, color, x, y):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, x_value, speed):
        super().__init__()
        self.image = pygame.image.load('Space Invaders Sprites/player.png').convert_alpha()
        self.rect = self.image.get_rect(midbottom=pos)
        self.speed = speed
        self.max_x_value = x_value
        self.ready_to_shoot = True
        self.shoot_time = 0
        self.shoot_cooldown = 1000

        self.lasers = pygame.sprite.Group()
        self.laser = pygame.mixer.Sound('Sounds/shoot.wav')
        self.laser.set_volume(0.3)

    def player_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        elif keys[pygame.K_LEFT]:
            self.rect.x -= self.speed

        if keys[pygame.K_SPACE]:
            self.shoot()

    def shoot_timer(self):
        current_time = pygame.time.get_ticks()
        if not self.ready_to_shoot and current_time - self.shoot_time >= self.shoot_cooldown:
            self.ready_to_shoot = True

    def constraint(self):
        if self.rect.left <= 0:
            self.rect.left = 0
        elif self.rect.right >= self.max_x_value:
            self.rect.right = self.max_x_value

    def shoot(self):
        if self.ready_to_shoot:
            self.lasers.add(Laser(self.rect.center, direction=-1))
            self.ready_to_shoot = False
            self.shoot_time = pygame.time.get_ticks()
            self.laser.play()

    def update(self):
        self.player_input()
        self.constraint()
        self.shoot_timer()
        self.lasers.update()


class Laser(pygame.sprite.Sprite):
    def __init__(self, pos, speed=8, direction=1):
        super().__init__()
        self.image = pygame.Surface((6, 14))
        self.image.fill('Cyan')
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed * direction
        self.max_y = screen_height

    def delete_laser(self):
        if self.rect.y <= -50 or self.rect.y >= self.max_y + 50:
            self.kill()

    def update(self):
        self.rect.y += self.speed


class GameLogic:
    def __init__(self):
        # Setting up the player
        player_sprite = Player((screen_width / 2, screen_height), screen_width, 5)
        self.player = pygame.sprite.GroupSingle(player_sprite)

        # Setting up the health system
        self.lives = 3
        self.lives_surface = pygame.image.load('Space Invaders Sprites/player.png').convert_alpha()
        self.lives_x_pos = screen_width - (self.lives_surface.get_size()[0] * 2 + 20)

        # Setting up the score
        self.score = 0
        self.font = pygame.font.Font('Minecraft copy 2.ttf', 30)

        # Setting up the obstacles
        self.shape = shape
        self.obstacle_size = 6
        self.obstacles = pygame.sprite.Group()
        self.obstacle_num = 4
        self.obstacle_x_positions = [num * (screen_width / self.obstacle_num) for num in range(self.obstacle_num)]
        self.create_more_obstacles(*self.obstacle_x_positions, x_start=screen_width / 15, y_start=550)

        # Setting up the enemies
        self.enemies = pygame.sprite.Group()
        self.create_enemies(rows=6, cols=8)
        self.enemy_direction = 1
        self.enemy_lasers = pygame.sprite.Group()

        self.bonus = pygame.sprite.GroupSingle()
        self.bonus_spawn_time = random.randint(400, 800)

        # Setting up the stars
        self.stars = pygame.sprite.Group()
        self.create_stars()

        self.laser = pygame.mixer.Sound('Sounds/laser.wav')
        self.laser.set_volume(0.2)

        self.explosion = pygame.mixer.Sound('Sounds/explosion.wav')
        self.explosion.set_volume(0.4)

        self.obstacle_hit = pygame.mixer.Sound('Sounds/vibrating-thud-39536 copy.mp3')
        self.obstacle_hit.set_volume(0.8)

        self.player_hit = pygame.mixer.Sound('Sounds/hurt_c_08-102842 copy.mp3')
        self.player_hit.set_volume(0.8)

        self.player_death = pygame.mixer.Sound('Sounds/videogame-death-sound-43894 copy.mp3')
        self.player_death.set_volume(1)

        self.player_win = pygame.mixer.Sound('Sounds/winsquare-6993.mp3')
        self.player_win.set_volume(1)

    def create_obstacle(self, x_start, y_start, offset_x):
        for row_index, row in enumerate(self.shape):
            for col_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + col_index * self.obstacle_size + offset_x
                    y = y_start + row_index * self.obstacle_size
                    obstacle = Block(self.obstacle_size, (241, 79, 80), x, y)
                    self.obstacles.add(obstacle)

    def create_more_obstacles(self, *offset, x_start, y_start, ):
        for offset_x in offset:
            self.create_obstacle(x_start, y_start, offset_x)

    def create_enemies(self, rows, cols, x_distance=60, y_distance=48, x_offset=120, y_offset=100):
        for row_index, row in enumerate(range(rows)):
            for col_index, col in enumerate(range(cols)):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset

                if row == 0:
                    enemy_sprites = Enemy('yellow', x, y)
                elif 1 <= row_index <= 2:
                    enemy_sprites = Enemy('green', x, y)
                else:
                    enemy_sprites = Enemy('red', x, y)

                self.enemies.add(enemy_sprites)

    def check_enemy_position(self):
        every_enemy = self.enemies.sprites()
        for enemy in every_enemy:
            if enemy.rect.right >= screen_width:
                self.enemy_direction = -1
                self.check_enemy_down_position(2)
            elif enemy.rect.left <= 0:
                self.enemy_direction = 1
                self.check_enemy_down_position(2)

    def check_enemy_down_position(self, y_distance):
        every_enemy = self.enemies.sprites()
        if self.enemies:
            for enemy in every_enemy:
                enemy.rect.y += y_distance

    def enemy_shooting(self):
        every_enemy = self.enemies.sprites()
        if self.enemies:
            random_enemy = random.choice(every_enemy)
            laser_sprite = Laser(random_enemy.rect.center, speed=6)
            self.enemy_lasers.add(laser_sprite)
            self.laser.play()

    def bonus_enemy_timer(self):
        self.bonus_spawn_time -= 1
        if self.bonus_spawn_time <= 0:
            self.bonus.add(Bonus(random.choice(['right', 'left'])))
            self.bonus_spawn_time = random.randint(400, 800)

    def collision_detection(self):

        # Collisions with the player laser
        if self.player.sprite.lasers:
            for laser in self.player.sprite.lasers:

                # Collisions with the player laser and the obstacles
                if pygame.sprite.spritecollide(laser, self.obstacles, True):
                    laser.kill()
                    self.obstacle_hit.play()

                # Collisions with the player laser and the enemies
                enemies_hit = pygame.sprite.spritecollide(laser, self.enemies, True)
                if enemies_hit:
                    laser.kill()
                    self.explosion.play()
                    for enemy in enemies_hit:
                        self.score += enemy.value

                # Collisions with the bonus enemy
                if pygame.sprite.spritecollide(laser, self.bonus, True):
                    laser.kill()
                    self.explosion.play()
                    self.score += 500

        # Collisions with the enemy lasers
        if self.enemy_lasers:
            for laser in self.enemy_lasers:

                # Collisions with the enemy laser and the obstacle
                if pygame.sprite.spritecollide(laser, self.obstacles, True):
                    laser.kill()
                    self.obstacle_hit.play()

                # Collisions with the enemy laser and the player
                if pygame.sprite.spritecollide(laser, self.player, False):
                    laser.kill()
                    self.player_hit.play()
                    self.lives -= 1
                    if self.lives <= 0:
                        self.player_death.play()
                        defeat(self.score)

        # Collisions with the enemies and the obstacles
        if self.enemies:
            for enemy in self.enemies:

                # Collisions with the enemy and the obstacles
                pygame.sprite.spritecollide(enemy, self.obstacles, True)

                # Collisions with the enemy and the player
                if pygame.sprite.spritecollide(enemy, self.player, False):
                    self.player_death.play()
                    defeat(self.score)

    def display_lives(self):
        for live in range(self.lives - 1):
            x = self.lives_x_pos + (live * (self.lives_surface.get_size()[0] + 10))
            screen.blit(self.lives_surface, (x, 8))

    def display_score(self):
        score_surface = self.font.render(f'Score: {self.score}', False, 'White')
        score_rect = score_surface.get_rect(topleft=(10, 10))
        screen.blit(score_surface, score_rect)

    def create_stars(self):
        for _ in range(100):
            star = Star()
            self.stars.add(star)

    def display_bg(self):
        self.stars.update()
        self.stars.draw(screen)

    def display_victory_screen(self):
        if not self.enemies.sprites():
            self.player_win.play()
            victory(self.score)

    def game_update(self):
        self.player.update()
        self.enemies.update(self.enemy_direction)
        self.bonus.update()
        self.enemy_lasers.update()

        self.bonus_enemy_timer()
        self.collision_detection()
        self.check_enemy_position()

        self.player.sprite.lasers.draw(screen)
        self.player.draw(screen)
        self.obstacles.draw(screen)
        self.enemies.draw(screen)
        self.enemy_lasers.draw(screen)
        self.bonus.draw(screen)
        self.display_lives()
        self.display_score()
        self.display_victory_screen()


class Star(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((2, 2))
        self.image.fill('white')
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, screen_width)
        self.rect.y = random.randint(0, screen_height)

    def update(self):
        self.rect.y += 0.5
        if self.rect.y > screen_height:
            self.rect.y = 0
            self.rect.x = random.randint(0, screen_width)


class Retro:
    def __init__(self):
        self.overlay = pygame.image.load('screen_overlay.png').convert_alpha()
        self.overlay = pygame.transform.scale(self.overlay, (screen_width, screen_height))

    def draw_lines(self):
        line_height = 3
        line_num = int(screen_height / line_height)
        for line in range(line_num):
            y_pos = line * line_height
            pygame.draw.line(self.overlay, 'Black', (0, y_pos), (screen_width, y_pos), 1)

    def draw(self):
        self.overlay.set_alpha(random.randint(70, 90))
        self.draw_lines()
        screen.blit(self.overlay, (0, 0))


def victory_screen(score):
    title_font = pygame.font.Font('Minecraft copy 2.ttf', 50)
    title_color = 'White'

    title = title_font.render(f' You Won!', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2) - 200))
    screen.blit(title, title_rect)

    title = title_font.render(f' Your Score: {score}', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2)))
    screen.blit(title, title_rect)

    title = title_font.render(f' Press Space To Replay', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2) + 200))
    screen.blit(title, title_rect)


def victory(score):
    pygame.mixer.music.stop()

    logic = GameLogic()
    screen_overlay = Retro()

    while True:
        screen.fill((30, 30, 30))

        screen_overlay.draw()
        logic.display_bg()

        victory_screen(score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_loop()

        pygame.display.update()
        clock.tick(60)


def defeat_screen(score):
    title_font = pygame.font.Font('Minecraft copy 2.ttf', 50)
    title_color = 'White'

    title = title_font.render(f' You Died!', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2) - 200))
    screen.blit(title, title_rect)

    title = title_font.render(f' Your Score: {score}', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2)))
    screen.blit(title, title_rect)

    title = title_font.render(f' Press Space To Replay', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2) + 200))
    screen.blit(title, title_rect)


def defeat(score):
    pygame.mixer.music.stop()

    logic = GameLogic()
    screen_overlay = Retro()

    while True:
        screen.fill((30, 30, 30))

        screen_overlay.draw()
        logic.display_bg()

        defeat_screen(score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_loop()

        pygame.display.flip()
        clock.tick(60)


def menu_screen():
    title_font = pygame.font.Font('Minecraft copy 2.ttf', 50)
    title_color = 'White'

    title = title_font.render(f' Space Invaders', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2) - 200))
    screen.blit(title, title_rect)

    title = title_font.render(f' Press Space To Play', False, title_color)
    title_rect = title.get_rect(center=((screen_width / 2), (screen_height / 2)))
    screen.blit(title, title_rect)


def player_quit(logic):
    for event in pygame.event.get():

        # Checking if the game window is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == enemy_laser:
            logic.enemy_shooting()


def update_game(logic, screen_overlay):
    screen.fill((30, 30, 30))

    logic.game_update()

    screen_overlay.draw()
    logic.display_bg()

    pygame.display.flip()
    clock.tick(60)


def game_loop():
    logic = GameLogic()
    screen_overlay = Retro()

    mixer.music.load('Sounds/music.wav')
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.2)

    while True:
        player_quit(logic)
        update_game(logic, screen_overlay)


def main():
    logic = GameLogic()
    screen_overlay = Retro()

    while True:
        screen.fill((30, 30, 30))

        screen_overlay.draw()
        logic.display_bg()

        menu_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_loop()

        pygame.display.flip()
        clock.tick(60)


main()
