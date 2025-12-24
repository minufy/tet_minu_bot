import pygame
pygame.init()

import sys
from bot import Bot
from tet_utils.game import Game
from minos import *
from utils import *

SCREEN_W = 1280
SCREEN_H = 720
UNIT = 24

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

clock = pygame.time.Clock()

handling = {
    "das": 117,
    "arr": 0,
    "sdf": 0
}
game = Game(handling, None)
bot = Bot(game, 1)

keys_to_code = {
    pygame.K_LSHIFT: "hold",
    pygame.K_UP: "cw",
    pygame.K_LCTRL: "ccw",
    pygame.K_a: "180",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
    pygame.K_SPACE: "harddrop",
    pygame.K_DOWN: "softdrop",
}

bot_active = True
while True:
    screen.fill("#333333")
     
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                bot_active = not bot_active
            if event.key == pygame.K_r:
                game.restart()
                # game.restart(time.time())
                bot.restart()
            if event.key == pygame.K_k:
                game.add_garbage(4)
            if event.key in keys_to_code:
                game.keydown(keys_to_code[event.key])
        if event.type == pygame.KEYUP:
            if event.key in keys_to_code:
                game.keyup(keys_to_code[event.key])
                
    for event in bot.get_events():
        type, key = event.split(".")
        if type == "keydown":
            game.keydown(key)
        if type == "keyup":
            game.keyup(key)

    game.draw(screen, UNIT)
    draw_hud(screen, bot, game)

    dt = clock.tick(120)

    if bot_active:
        bot.update(dt)
    game.update(dt)
    # print_bitgrid(grid_to_bitgrid(game.board.grid), BOARD_W)
    # print(bot.get_tspin_potential(grid_to_bitgrid(game.board.grid), None))
    # print(bot.get_scores(grid_to_bitgrid(game.board.grid), False, "T"))

    game.get_garbage()

    pygame.display.update()