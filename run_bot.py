import pygame
import zmq
import sys
from bot import Bot
from board import TestBoard
from tet_utils.minos import Mino

clock = pygame.time.Clock()

class GameEmu:
    def __init__(self):
        self.board = None
        self.queue = None
        self.mino = None

    def update(self, game_state):
        self.board = TestBoard(game_state["grid"])
        self.queue = game_state["queue"]
        self.mino = Mino(game_state["mino_type"], 3, self.board.h//2)

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
    dt = clock.tick(30)

    game_state = socket.recv_json()
    if game_state["state"] == "started" and not started:
        game = GameEmu()
        game.update(game_state)
        bot = Bot(game, 200+100*index)
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