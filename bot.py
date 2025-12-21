from test_board import TestBoard
from test_minos import MINO_SHAPES, TestMino
from weights import up, down

SEARCH_DEPTH = 1
SEARCH_COUNT = 2

DANGER_HEIGHT = 7

LINE_TABLE = {
    "upstack": {
        0: 0,
        1: -4,
        2: -3,
        3: -2,
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

class Move:
    def __init__(self, mino, score, board, hold):
        self.mino = mino
        self.score = score
        self.board = board
        self.hold = hold

class Input:
    def __init__(self, key, time):
        self.hold_time = time
        self.hold_timer = 0
        self.down_event = f"keydown.{key}"
        self.up_event = f"keyup.{key}"
    
    def update(self, dt):
        self.hold_timer += dt

class Bot:
    def __init__(self, game, think_time):
        self.game = game
        self.board = TestBoard(self.game.board.grid)
        self.queue = [self.game.mino.type]+self.game.queue.copy()
        self.last_queue = []
        self.inputs = []
        self.weights_upstack = up
        self.weights_downstack = down
        self.think_time = think_time
        self.think_timer = 0
        self.hold_type = None
        self.held = False
        self.depth = SEARCH_DEPTH
        self.best_count = SEARCH_COUNT

    def sync(self):
        self.board = TestBoard(self.game.board.grid)
        self.queue = [self.game.mino.type]+self.game.queue.copy()
        self.last_queue = []

    def restart(self):
        self.sync()
        self.inputs = []
        self.think_timer = 0
        self.hold_type = None
        self.held = False
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

    # def set_weights(self, weights_upstack, weights_donwstack):
    #     self.weights_upstack = weights_upstack
    #     self.weights_downstack = weights_donwstack

    def place(self, mino, board):
        for y, row in enumerate(MINO_SHAPES[mino.type][str(mino.rotation)]):
            for x, dot in enumerate(row):
                if dot:
                    board.grid[mino.y+y][mino.x+x] = mino.type

    def hard_drop(self, mino, board):
        for _ in range(board.h):
            if mino.move(0, 1, board) == False:
                self.place(mino, board)
                break

    def find_moves(self, mino_0, mino_1, grid):
        mino_types = [mino_0]
        if mino_1:
            mino_types.append(mino_1)
        moves = []
        for mino_type in mino_types:
            for r in [0, 1, 2, 3]:
                for x in range(-2, self.board.w-1):
                    mino = TestMino(mino_type, x, self.game.board.h//2-4, r)
                    board = TestBoard(grid)

                    if mino.check_collison(board):
                        continue
                    
                    self.hard_drop(mino, board)
                    score = sum(self.get_scores(board))
                    self.line_clear(board)
                    
                    hold = None
                    if mino_type != mino_0:
                        hold = mino_0
                    
                    moves.append(Move(mino, score, board, hold))
        return moves
 
    def exectue_move(self, move):
        if move.hold:
            self.input("hold", 1)
            self.hold_type = move.hold
            
        if move.mino.rotation == 1:
            self.input("cw", 1)
        elif move.mino.rotation == 3:
            self.input("ccw", 1)
        elif move.mino.rotation == 2:
            self.input("180", 1)

        x = 3
        for _ in range(self.board.w):
            if move.mino.x == x:
                break
            elif move.mino.x > x:
                x += 1
                self.input("right", 1)
            else:
                x -= 1
                self.input("left", 1)
             
        self.input("harddrop", 1)

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
            for y in range(board.h):
                if board.grid[y][x] != " ":
                    block = True
                elif block and board.grid[y][x] == " ":
                    holes += 1
                    # break
        return holes

    def get_change_rate(self, board):
        heights = self.get_heights(board)
        diffs = []
        for i in range(board.w-1):
            diffs.append(abs(heights[i]-heights[i+1]))
        change_rate = sum(diffs)/board.w
        return change_rate

    def get_scores(self, board):
        lines = LINE_TABLE[self.get_mode(board)][self.get_lines(board)]
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
            
        new_moves = sorted(moves[-self.best_count:], key=lambda x: sum([move.score for move in self.research(depth+1, x)]))
        if new_moves:
            return new_moves
        return []
    
    def think(self):
        if len(self.queue) >= max(SEARCH_DEPTH, 2):
            moves = self.search_moves(self.queue[0], self.hold_type or self.queue[1], self.board, 0)
            if moves:
                move = moves[-1]
                self.exectue_move(move)
                self.place(move.mino, self.board)
                self.line_clear(self.board)
                if move.hold and not self.held:
                    self.held = True
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

        if self.inputs:
            self.inputs[0].update(dt)

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
            current_input = self.inputs[0]
            if current_input.down_event:
                events.append(current_input.down_event)
                current_input.down_event = None
            
            if current_input.hold_timer > current_input.hold_time:
                events.append(current_input.up_event)
                self.inputs.pop(0)

        return events