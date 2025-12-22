import time
from minos import Mino, BIT_SHAPES
from weights import up, down
from collections import deque
from utils import grid_to_bitgrid, BOARD_W, FULL_ROW

SEARCH_DEPTH = 0
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
    def __init__(self, mino, score, bitgrid, hold):
        self.mino = mino
        self.score = score
        self.bitgrid = bitgrid
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
        self.bitgrid = grid_to_bitgrid(self.game.board.grid)
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
        self.bitgrid = grid_to_bitgrid(self.game.board.grid)
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

    def get_mode(self, bitgrid):
        if max(self.get_heights(bitgrid)) < DANGER_HEIGHT:
            return "upstack"
        return "downstack"

    def get_weights(self, bitgrid):
        mode = self.get_mode(bitgrid)
        if mode == "upstack":
            return self.weights_upstack
        return self.weights_downstack

    def place(self, mino, bitgrid):
        bit_shape = BIT_SHAPES[mino.type][str(mino.rotation)]
        for i, row in enumerate(bit_shape):
            if row == 0: 
                continue
        
            target_y = mino.y + i
            
            if 0 <= target_y < len(bitgrid):
                if mino.x >= 0:
                    placed_row = row << mino.x
                else:
                    placed_row = row >> abs(mino.x)
                
                bitgrid[target_y] |= placed_row

    def soft_drop(self, mino, bitgrid):
        for _ in range(len(bitgrid)):
            if mino.move(0, 1, bitgrid) == False:
                break

    def find_moves(self, mino_0, mino_1, bitgrid):
        mino_types = [mino_0]
        if mino_1:
            mino_types.append(mino_1)
        moves = []
        heights = self.get_heights(bitgrid)
        # mino = Mino("", 0, 0, 0) 
        for mino_type in mino_types:
            for r in [0, 1, 2, 3]:
                for x in range(-2, BOARD_W-1):
                    for y in range(len(bitgrid)//2-4, len(bitgrid)-heights[x]-2):
                        mino = Mino(mino_type, x, y, r)
                        new_bitgrid = bitgrid.copy()
                        
                        if mino.check_collison(new_bitgrid):
                            continue
                        
                        self.soft_drop(mino, new_bitgrid)
                        self.place(mino, new_bitgrid)
                        blocked = not mino.move(0, -1, new_bitgrid)
                        score = sum(self.get_scores(new_bitgrid, blocked, mino.type))
                        self.line_clear(new_bitgrid)
                        
                        hold = None
                        if mino_type != mino_0:
                            hold = mino_0
                        
                        moves.append(Move(mino, score, new_bitgrid, hold))
        return moves
 
    def move_mino(self, mino, x, y, bitgrid, charge):
        rep = 1
        if charge:
            rep = len(bitgrid)
        for _ in range(rep):
            if mino.move(x, y, bitgrid) == False:
                break
    
    def check_input(self, inputs, move, bitgrid):
        new_bitgrid = bitgrid.copy()
        mino = Mino(move.mino.type, 3, len(new_bitgrid)//2-4, 0)
        for i, d in inputs:
            charge = (d >= self.handling["das"])
            if i == "cw":
                mino.rotate(1, new_bitgrid)
            elif i == "ccw":
                mino.rotate(-1, new_bitgrid)
            elif i == "180":
                mino.rotate(2, new_bitgrid)
            elif i == "right":
                self.move_mino(mino, 1, 0, new_bitgrid, charge)
            elif i == "left":
                self.move_mino(mino, -1, 0, new_bitgrid, charge)
            elif i == "softdrop":
                self.move_mino(mino, 0, 1, new_bitgrid, True)
        self.soft_drop(mino, new_bitgrid)
        self.place(mino, new_bitgrid)
        self.line_clear(new_bitgrid)
        return new_bitgrid
    
    def find_inputs(self, move, bitgrid):
        q = deque()
        q.append(([]))
        v = set()
        res_inputs = []
        while q:
            inputs = q.popleft()
            
            b = self.check_input(inputs, move, bitgrid)
            mb = move.bitgrid
            if b == mb:
                if res_inputs == [] or len(inputs) < len(res_inputs):
                    res_inputs = inputs
                continue

            tb = tuple(b)
            if tb in v:
                continue
            v.add(tb)
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

    def execute_move(self, move, bitgrid):
        if move.hold:
            self.input("hold", ADDITIONAL_INPUT_MS)
            self.hold_type = move.hold
            
        inputs = self.find_inputs(move, bitgrid)
        for i, d in inputs:
            self.input(i, d)

        self.input("harddrop", ADDITIONAL_INPUT_MS)

    def get_heights(self, bitgrid):
        heights = [0]*BOARD_W
        board_h = len(bitgrid)
        for y, row in enumerate(bitgrid):
            height = board_h-y
            for x in range(BOARD_W):
                if heights[x] == 0:
                    if row & (1<<x):
                        heights[x] = height
        return heights
    
    def get_lines(self, bitgrid):
        count = 0
        for y, row in enumerate(bitgrid):
            if row == FULL_ROW:
                count += 1
        return count

    def get_holes(self, bitgrid):
        holes = 0 
        block_mask = 0
        for row in bitgrid:
            row_holes = block_mask & ~row
            holes += bin(row_holes & FULL_ROW).count("1")
            block_mask |= row
        return holes

    def get_change_rate(self, bitgrid):
        heights = self.get_heights(bitgrid)
        diffs = []
        for i in range(BOARD_W-1):
            diffs.append(abs(heights[i]-heights[i+1]))
        change_rate = sum(diffs)/BOARD_W
        return change_rate
    
    def get_tspins(self, bitgrid, blocked, mino_type):
        if not blocked:
            return 0
        if mino_type != "T":
            return 0
        return self.get_lines(bitgrid)

    def get_scores(self, bitgrid, blocked, mino_type):
        lines = LINES[self.get_mode(bitgrid)][self.get_lines(bitgrid)]+TSPIN_LINES[self.get_tspins(bitgrid, blocked, mino_type)]
        change_rate = self.get_change_rate(bitgrid)
        holes = self.get_holes(bitgrid)

        weights = self.get_weights(bitgrid)
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
        return self.search_moves(self.queue[depth], move.hold or mino_1, move.bitgrid, depth) 

    def search_moves(self, mino_0, mino_1, bitgrid, depth):
        moves = self.find_moves(mino_0, mino_1, bitgrid)
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
            moves = self.search_moves(self.queue[0], self.hold_type or self.queue[1], self.bitgrid, 0)
            if moves:
                move = moves[-1]
                self.execute_move(move, self.bitgrid)
                self.place(move.mino, self.bitgrid)
                self.line_clear(self.bitgrid)
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

        if grid_to_bitgrid(self.game.board.grid) == self.bitgrid:
            self.think_timer += dt
            if self.think_timer >= self.think_time:
                self.think_timer = 0
                self.think()
        elif self.inputs == []:
            self.sync()

    def line_clear(self, bitgrid):
        for y, row in enumerate(bitgrid):
            if row == FULL_ROW:
                bitgrid.pop(y)
                bitgrid.insert(0, 0)

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