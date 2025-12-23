import pygame
pygame.init()
import zmq
import sys
from bot import Bot
from minos import Mino

class Board:
    def __init__(self, grid):
        self.grid = grid

clock = pygame.time.Clock()

class GameEmu:
    def __init__(self):
        self.board = None
        self.queue = None
        self.mino = None
        self.handling = None

    def update(self, game_state):
        self.board = Board(game_state["grid"])
        self.queue = game_state["queue"]
        self.mino = Mino(game_state["mino_type"], 3, len(self.board.grid)//2-4)
        self.handling = game_state["handling"]
        self.hold_type = game_state["hold_mino_type"]

index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
print(f"starting bot {index}")

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
socket.send_json({
    "events": [],
    "index": index
})

game = None
bot = None

started = False

while True:
    dt = clock.tick(60)

    game_state = socket.recv_json()
    if game_state["state"] == "started" and not started:
        game = GameEmu()
        game.update(game_state)
        bot = Bot(game, 400)
        # bot = Bot(game, 200+100*index)
        started = True

    if started:    
        events = bot.get_events()
        socket.send_json({
            "events": events,
            "index": index
        })
        
        game.update(game_state)
        bot.update(dt)
    else:
        socket.send_json({
            "events": [],
            "index": index
        })