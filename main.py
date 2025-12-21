import pygame
pygame.init()

import sys
from bot import Bot
from tet_utils.game import Game
from tet_utils.minos import *

SCREEN_W = 1280
SCREEN_H = 720
UNIT = 24

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

clock = pygame.time.Clock()

game = Game({
    "das": 117,
    "arr": 0,
    "sdf": 0
})
bot = Bot(game, 1)

while True:
    screen.fill("#333333")
     
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                game.restart()
                bot.restart()

    for event in bot.get_events():
        type, key = event.split(".")
        if type == "keydown":
            game.keydown(key)
        if type == "keyup":
            game.keyup(key)

    game.draw(screen, UNIT)
    # draw_hud(screen, bot, game)

    dt = clock.tick(120)

    game.update(dt)
    bot.update(dt)
    # print(bot.get_scores(game.board))

    pygame.display.update()