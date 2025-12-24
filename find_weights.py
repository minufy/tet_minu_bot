import pygame
pygame.init()

import multiprocessing as mp
import random
from bot import Bot
from tet_utils.game import Game
from utils import print_bitgrid, BOARD_W

class Test:
    def __init__(self, game, bot, prev_weights=None, prev_weights_downstack=None):
        self.game = game
        self.bot = bot
        self.prev_weights = prev_weights
        self.set()

    def set(self):
        one = 0.05
        weights = {
            "lines": random.random()+one,
            "change_rate": -random.random()+one,
            "holes": -random.random()+one,
            "tspin_potential": random.random()*1.5+one,
            "max_height": -random.random()+one,
        }
        if self.prev_weights:
            self.weights = self.prev_weights
            for weight in self.weights:
                self.weights[weight] += (weights[weight]-self.weights[weight])*RATE
        else:
            self.weights = weights

        for weight in self.weights:
            self.weights[weight] = round(self.weights[weight], 3)

        self.bot.set_weights(self.weights)
            
class Result:
    def __init__(self, score, weights):
        self.score = score
        self.weights = weights

RATE = 0.3
TEST_DEPTH = 10
TEST_COUNT = 3
TEST_DURATION = 10000

def run_game(bot, game):
    for _ in range(TEST_DURATION):
        for event in bot.get_events():
            type, key = event.split(".")
            if type == "keydown":
                game.keydown(key)
            if type == "keyup":
                game.keyup(key)

        game.update(1)
        bot.update(1)
        
        # print_bitgrid(bot.bitgrid, BOARD_W)
        # test.update(1)

def run_test(args):
    i, prev_result = args
    handling = {
        "das": 50,
        "arr": 0,
        "sdf": 0
    }
    game = Game(handling)
    bot = Bot(game, 0)
    test = Test(game, bot, prev_result.weights)
    
    run_game(bot, game)
    score = game.attack 
    print(f"{i+1}/{TEST_COUNT}")
    print(f"score: {score}")
    return Result(score, test.weights)

def run(prev_result, depth=0):
    print(f"> depth: {depth}")
    if depth > TEST_DEPTH:
        return prev_result
    
    results = [prev_result]
    args = [(i, prev_result) for i in range(TEST_COUNT)]
    with mp.Pool(processes=3) as pool:
        new_results = pool.map(run_test, args)
    results += new_results
        
    results.sort(key=lambda x: x.score)
    return run(results[-1], depth+1)

if __name__ == "__main__":
    mp.freeze_support()
    
    result = run(Result(0, None, None))
    with open("weights.py", "a") as file:
        file.writelines("\n")
        file.writelines(f"# score: {result.score}\n")
        file.writelines(f"up = {result.weights_upstack}\n")
        file.writelines(f"down = {result.weights_downstack}\n")