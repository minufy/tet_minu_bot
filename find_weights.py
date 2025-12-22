import pygame
pygame.init()

import multiprocessing as mp
from bot import Bot
from tet_utils.game import Game
import random

class Test:
    def __init__(self, game, bot, prev_weights_upstack=None, prev_weights_downstack=None):
        self.game = game
        self.bot = bot
        self.prev_weights_upstack = prev_weights_upstack
        self.prev_weights_downstack = prev_weights_downstack
        self.set()

    def set(self):
        weights_upstack = {
            "lines": random.random(),
            "change_rate": -random.random(),
            "holes": -random.random(),
        }
        weights_downstack = {
            "lines": random.random(),
            "change_rate": -random.random(),
            "holes": -random.random(),
        }

        if self.prev_weights_upstack:
            self.weights_upstack = self.prev_weights_upstack
            for weight in self.weights_upstack:
                self.weights_upstack[weight] += (weights_upstack[weight]-self.weights_upstack[weight])*RATE
        else:
            self.weights_upstack = weights_upstack

        if self.prev_weights_downstack:
            self.weights_downstack = self.prev_weights_downstack
            for weight in self.weights_downstack:
                self.weights_downstack[weight] += (weights_downstack[weight]-self.weights_downstack[weight])*RATE
        else:
            self.weights_downstack = weights_downstack

        for weight in self.weights_upstack:
            self.weights_upstack[weight] = round(self.weights_upstack[weight], 3)
        for weight in self.weights_downstack:
            self.weights_downstack[weight] = round(self.weights_downstack[weight], 3)

        self.bot.set_weights(self.weights_upstack, self.weights_downstack)
            
class Result:
    def __init__(self, score, weights_upstack, weights_downstack):
        self.score = score
        self.weights_upstack = weights_upstack
        self.weights_downstack = weights_downstack

RATE = 0.3
TEST_DEPTH = 10
TEST_COUNT = 3
TEST_DURATION = 1500

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
        # test.update(1)

def run_test(args):
    i, prev_result = args
    game = Game({
        "das": 117,
        "arr": 0,
        "sdf": 0
    })
    bot = Bot(game, 1)
    test = Test(game, bot, prev_result.weights_upstack, prev_result.weights_downstack)
    
    run_game(bot, game)
    # score = game.attack
    score = game.attack+sum(bot.get_scores(game.board))
    print(f"{i+1}/{TEST_COUNT}")
    print(f"score: {score}")
    return Result(score, test.weights_upstack, test.weights_downstack)

def run(prev_result, depth=0):
    print(f"depth: {depth}")
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