import time
from board import TestBoard
from tet_utils.minos import Mino, MINO_SHAPES
from weights import up, down
from collections import deque

SEARCH_DEPTH = 1
SEARCH_COUNT = 2

DANGER_HEIGHT = 11

LINES = {
    "upstack": {
        0: 0,
        1: -4,
        2: -4,
        3: -4,
        4: 10
    },
    "downstack": {
        0: 0,
        1: 1,
        2: 2,
        3: 3,
        4: 10
    },
}

TSPIN_LINES = {
    3: 12,
    2: 10,
    1: 6,
    0: 0
}

ADDITIONAL_INPUT_MS = 10

class Move:
    def __init__(self, mino, score, board, hold):
        self.mino = mino
        self.score = score
        self.board = board
        self.hold = hold

class Input:
    def __init__(self, key, duration):
        self.duration = duration
        self.up_time = None
        self.down_event = f"keydown.{key}"
        self.up_event = f"keyup.{key}"

class Bot:
    def __init__(self, game, handling, think_time):
        self.game = game
        self.board = TestBoard(self.game.board.grid)
        self.queue = [self.game.mino.type]+self.game.queue.copy()
        self.last_queue = []
        self.inputs = []
        self.weights_upstack = up
        self.weights_downstack = down
        self.think_time = think_time
        self.think_timer = 0
        self.handling = handling
        self.hold_type = ""
        self.first_held = False
        self.depth = SEARCH_DEPTH
        self.best_count = SEARCH_COUNT

    def set_weights(self, up, down):
        self.weights_upstack = up
        self.weights_downstack = down

    def sync(self):
        print("syncing..")
        self.board = TestBoard(self.game.board.grid)
        self.queue = [self.game.mino.type]+self.game.queue.copy()
        self.last_queue = []
        self.hold = self.game.hold_type

    def restart(self):
        self.sync()
        self.inputs = []
        self.think_timer = 0
        self.hold_type = ""
        self.first_held = False
        self.depth = SEARCH_DEPTH
        self.best_count = SEARCH_COUNT

    def get_mode(self, board):
        if max(self.get_heights(board)) < DANGER_HEIGHT:
            return "upstack"
        return "downstack"

    def get_weights(self, board):
        mode = self.get_mode(board)
        if mode == "upstack":
            return self.weights_upstack
        return self.weights_downstack

    def place(self, mino, board):
        for y, row in enumerate(MINO_SHAPES[mino.type][str(mino.rotation)]):
            for x, dot in enumerate(row):
                if dot:
                    board.grid[mino.y+y][mino.x+x] = mino.type

    def soft_drop(self, mino, board):
        for _ in range(board.h):
            if mino.move(0, 1, board) == False:
                break

    def find_moves(self, mino_0, mino_1, grid):
        mino_types = [mino_0]
        if mino_1:
            mino_types.append(mino_1)
        moves = []
        for mino_type in mino_types:
            for r in [0, 1, 2, 3]:
                for y in range(len(grid)//2-4, len(grid)-2):
                    for x in range(-2, len(grid[0])):
                        mino = Mino(mino_type, x, y, r)
                        board = TestBoard(grid)

                        if mino.check_collison(board):
                            continue
                        
                        self.soft_drop(mino, board)
                        self.place(mino, board)
                        blocked = not mino.move(0, -1, board)
                        score = sum(self.get_scores(board, blocked, mino.type))
                        self.line_clear(board)
                        
                        hold = None
                        if mino_type != mino_0:
                            hold = mino_0
                        
                        moves.append(Move(mino, score, board, hold))
        return moves
 
    def move_mino(self, mino, x, y, board, charge):
        rep = 1
        if charge:
            rep = board.h
        for _ in range(rep):
            if mino.move(x, y, board) == False:
                break
    
    def check_input(self, inputs, move, grid):
        board = TestBoard(grid)
        mino = Mino(move.mino.type, 3, board.h//2-4, 0)
        for i, d in inputs:
            charge = (d >= self.handling["das"])
            if i == "cw":
                mino.rotate(1, board)
            elif i == "ccw":
                mino.rotate(-1, board)
            elif i == "180":
                mino.rotate(2, board)
            elif i == "right":
                self.move_mino(mino, 1, 0, board, charge)
            elif i == "left":
                self.move_mino(mino, -1, 0, board, charge)
            elif i == "softdrop":
                self.move_mino(mino, 0, 1, board, True)
        self.soft_drop(mino, board)
        self.place(mino, board)
        self.line_clear(board)
        return board
    
    def bin(self, board):
        res = []
        for y in range(board.h):
            b = 0
            for x in range(board.w):
                if board.grid[y][x] != " ":
                    b += 2**x
            res.append(b)
        return tuple(res)

    def find_inputs(self, move, board):
        q = deque()
        q.append(([]))
        v = set()
        res_inputs = []
        while q:
            inputs = q.popleft()
            current_board = self.check_input(inputs, move, board.grid)
            
            b = self.bin(current_board)
            mb = self.bin(move.board)
            if b == mb:
                if res_inputs == [] or len(inputs) < len(res_inputs):
                    res_inputs = inputs
                continue

            if b in v:
                continue
            v.add(b)
            if len(inputs) > 5:
                continue
            
            q.append(inputs+[("cw", ADDITIONAL_INPUT_MS)])
            q.append(inputs+[("ccw", ADDITIONAL_INPUT_MS)])
            q.append(inputs+[("180", ADDITIONAL_INPUT_MS)])
            q.append(inputs+[("right", ADDITIONAL_INPUT_MS)])
            q.append(inputs+[("left", ADDITIONAL_INPUT_MS)])
            q.append(inputs+[("right", self.handling["das"]+ADDITIONAL_INPUT_MS)])
            q.append(inputs+[("left", self.handling["das"]+ADDITIONAL_INPUT_MS)])
            q.append(inputs+[("softdrop", ADDITIONAL_INPUT_MS)])

        return res_inputs

    def execute_move(self, move, board):
        if move.hold:
            self.input("hold", ADDITIONAL_INPUT_MS)
            self.hold_type = move.hold
            
        inputs = self.find_inputs(move, board)
        for i, d in inputs:
            self.input(i, d)

        self.input("harddrop", ADDITIONAL_INPUT_MS)

    def get_heights(self, board):
        heights = [0]*board.w
        for x in range(board.w):
            heights[x] = board.h
            for y in range(board.h):
                if board.grid[y][x] == " ":
                    heights[x] -= 1
                else:
                    break
        return heights
    
    def get_lines(self, board):
        count = 0
        for y in range(board.h):
            for x in range(board.w):
                if board.grid[y][x] == " ":
                    break
            else:
                count += 1
        return count
    
    def get_holes(self, board):
        holes = 0
        for x in range(board.w):
            block = False
            top_y = None
            for y in range(board.h):
                if board.grid[y][x] != " ":
                    block = True
                    top_y = y
                elif block and board.grid[y][x] == " ":
                    holes += 1
                    if top_y != None:
                        holes += y-top_y
                        top_y = None
        return holes
    
    def get_change_rate(self, board):
        heights = self.get_heights(board)
        diffs = []
        for i in range(board.w-1):
            diffs.append(abs(heights[i]-heights[i+1]))
        change_rate = sum(diffs)/board.w
        return change_rate
    
    def get_tspins(self, board, blocked, mino_type):
        if not blocked:
            return 0
        if mino_type != "T":
            return 0
        return self.get_lines(board)

    def get_scores(self, board, blocked, mino_type):
        lines = LINES[self.get_mode(board)][self.get_lines(board)]+TSPIN_LINES[self.get_tspins(board, blocked, mino_type)]
        change_rate = self.get_change_rate(board)
        holes = self.get_holes(board)

        weights = self.get_weights(board)
        lines *= weights["lines"] 
        change_rate *= weights["change_rate"]
        holes *= weights["holes"]
        
        return lines, change_rate, holes

    def research(self, depth, move):
        mino_1 = None
        if depth >= len(self.queue):
            return []
        if depth+1 < len(self.queue):
            mino_1 = self.queue[depth+1]
        return self.search_moves(self.queue[depth], move.hold or mino_1, move.board, depth) 

    def search_moves(self, mino_0, mino_1, board, depth):
        moves = self.find_moves(mino_0, mino_1, board.grid)
        moves.sort(key=lambda x: x.score)
        if depth >= self.depth:
            if moves:
                return moves
            else:
                return []
            
        new_moves = sorted(moves[-self.best_count:], key=lambda x: max([move.score for move in self.research(depth+1, x)]))
        if new_moves:
            return new_moves
        return []
    
    def think(self):
        if len(self.queue) >= max(SEARCH_DEPTH, 2):
            moves = self.search_moves(self.queue[0], self.hold_type or self.queue[1], self.board, 0)
            if moves:
                move = moves[-1]
                self.execute_move(move, self.board)
                self.place(move.mino, self.board)
                self.line_clear(self.board)
                if move.hold and not self.first_held:
                    self.first_held = True
                    self.queue.pop(0)
                self.queue.pop(0)

    def update(self, dt):
        if len(self.game.queue) == 11:
            bag = self.game.queue[-7:]
            if self.last_queue != bag:
                self.last_queue = bag
                self.queue += bag

        if self.game.board.grid == self.board.grid:
            self.think_timer += dt
            if self.think_timer >= self.think_time:
                self.think_timer = 0
                self.think()
        elif self.inputs == []:
            self.sync()

    def line_clear(self, board):
        for y in range(board.h):
            for x in range(board.w):
                if board.grid[y][x] == " ":
                    break
            else:
                board.grid.pop(y)
                board.grid.insert(0, [" "]*board.w)

    def input(self, key, time):
        self.inputs.append(Input(key, time))

    def get_events(self):
        events = []
        
        if self.inputs:
            time_ms = time.time()*1000
            current_input = self.inputs[0]
            if current_input.down_event:
                events.append(current_input.down_event)
                current_input.down_event = None
                current_input.up_time = time_ms+current_input.duration
            
            if time_ms >= current_input.up_time:
                # print(time_ms-current_input.up_time)
                events.append(current_input.up_event)
                self.inputs.pop(0)

        return events