import pygame
import zmq
from bot import Bot
from test_board import TestBoard
from test_minos import TestMino

clock = pygame.time.Clock()

class GameEmu:
    def __init__(self):
        self.board = None
        self.queue = None
        self.mino = None

    def update(self, game_state):
        self.board = TestBoard(game_state["grid"])
        self.queue = game_state["queue"]
        self.mino = TestMino(game_state["mino_type"], 3, self.board.h//2)

context = zmq.Context()
print("connecting..")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
socket.send_json({"events": []})

game = GameEmu()
game_state = socket.recv_json()
game.update(game_state)
bot = Bot(game, 1)

while True:
    dt = clock.tick(30)
    events = bot.get_events()
    socket.send_json({"events": events})
     
    game_state = socket.recv_json()
    game.update(game_state)
    bot.update(dt)