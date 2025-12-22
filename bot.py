from minos import Mino, BIT_SHAPES, MINO_TYPES
from weights import up, down
from collections import deque
from utils import print_bitgrid, grid_to_bitgrid, BOARD_W, FULL_ROW, timer
from functools import lru_cache

SEARCH_DEPTH = 1
SEARCH_COUNT = 1

DANGER_HEIGHT = 11
MAX_LEN_INPUTS = 3

LINES = {
    "upstack": {
        0: 0,
        1: 1,
        2: 1,
        3: 1,
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

MINO_ROTATIONS = {
    "O": [],
    "I": ["cw"],
    "S": ["cw"],
    "Z": ["cw"],
    "T": ["cw", "ccw", "180"],
    "L": ["cw", "ccw", "180"],
    "J": ["cw", "ccw", "180"],
}

MINO_INPUTS = {}
def make_inputs(mino_type):
    q = deque()
    q.append((False, False, []))
    results = []
    while q:
        rotated, moved, inputs = q.popleft()
        if len(inputs) > MAX_LEN_INPUTS:
            continue
        results.append(inputs)
         
        if not rotated:
            for r in MINO_ROTATIONS[mino_type]:
                q.append((True, moved, inputs+[(r, "tap")]))
        if not moved:
            q.append((rotated, True, inputs+[("right", "tap")]))
            q.append((rotated, True, inputs+[("left", "tap")]))
            q.append((rotated, True, inputs+[("right", "das")]))
            q.append((rotated, True, inputs+[("left", "das")]))
            q.append((rotated, True, inputs+[("right", "das"), ("left", "tap")]))
            q.append((rotated, True, inputs+[("left", "das"), ("right", "tap")]))
            q.append((rotated, True, inputs+[("right", "tap"), ("right", "tap")]))
            q.append((rotated, True, inputs+[("left", "tap"), ("left", "tap")]))
        q.append((False, False, inputs+[("softdrop", "das")]))
    return results
        
for type in MINO_TYPES:
    MINO_INPUTS[type] = make_inputs(type)
    MINO_INPUTS[type].sort(key=lambda x: len(x))
    # print(len(MINO_INPUTS[type]))

TSPIN_LINES = {
    3: 12,
    2: 10,
    1: 6,
    0: 0
}

class Move:
    def __init__(self, mino_type, score, bitgrid, hold, inputs):
        self.mino_type = mino_type
        self.score = score
        self.bitgrid = bitgrid
        self.hold = hold
        self.inputs = inputs

class Input:
    def __init__(self, key, time):
        self.timer = 0
        self.time = time
        self.up_time = None
        self.key = key
        self.down_event = f"keydown.{key}"
        self.up_event = f"keyup.{key}"

class SearchState:
    def __init__(self, bitgrid, hold, score, first_move=None):
        self.bitgrid = bitgrid
        self.hold = hold
        self.score = score
        self.first_move = first_move

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
        self.search_depth = SEARCH_DEPTH
        self.search_count = SEARCH_COUNT

    def set_weights(self, up, down):
        self.weights_upstack = up
        self.weights_downstack = down

    def sync(self):
        print("syncing..")
        # print("GAME")
        # print_bitgrid(grid_to_bitgrid(self.game.board.grid), BOARD_W)
        # print("BOT")
        # print_bitgrid(self.bitgrid, BOARD_W)
        self.bitgrid = grid_to_bitgrid(self.game.board.grid)
        self.queue = [self.game.mino.type]+self.game.queue.copy()
        self.last_queue = []
        self.hold_type = self.game.hold_type

    def restart(self):
        self.sync()
        self.inputs = []
        self.think_timer = 0
        self.hold_type = ""
        self.first_held = False
        self.search_depth = SEARCH_DEPTH
        self.search_count = SEARCH_COUNT

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

    @lru_cache(maxsize=1000)
    def find_moves(self, mino_0, mino_1, bitgrid):
        mino_types = [mino_0]
        if mino_1:
            mino_types.append(mino_1)
        moves = []
        for mino_type in mino_types:
            v = set()
            results = MINO_INPUTS[mino_type]
            for inputs in results:
                _, drop_bitgrid = self.check_input(inputs, mino_type, list(bitgrid))
                                
                tuple_bitgrid = tuple(drop_bitgrid)
                if tuple_bitgrid in v:
                    continue
                v.add(tuple_bitgrid)

                lines = LINES[self.get_mode(drop_bitgrid)][self.get_lines(drop_bitgrid)]
                change_rate = self.get_change_rate(drop_bitgrid)
                holes = self.get_holes(drop_bitgrid)
                
                # print_bitgrid(drop_bitgrid, BOARD_W)

                weights = self.get_weights(bitgrid)
                lines *= weights["lines"] 
                change_rate *= weights["change_rate"]
                holes *= weights["holes"]

                score = lines+change_rate+holes
            
                self.line_clear(drop_bitgrid)
                
                hold = None
                if mino_type != mino_0:
                    hold = mino_0
                    
                move = Move(mino_type, score, drop_bitgrid, hold, inputs)
                moves.append(move)
        return moves
 
    def move_mino(self, mino, x, y, bitgrid, charge):
        rep = 1
        if charge:
            rep = len(bitgrid)
        for _ in range(rep):
            if mino.move(x, y, bitgrid) == False:
                break
    
    # @timer
    def check_input(self, inputs, mino_type, bitgrid):
        new_bitgrid = bitgrid.copy()
        mino = Mino(mino_type, 3, len(new_bitgrid)//2-4, 0)
        for i, d in inputs:
            charge = (d == "das")
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
                self.soft_drop(mino, new_bitgrid)
                
        drop_bitgrid = new_bitgrid.copy()
        self.soft_drop(mino, drop_bitgrid)
        self.place(mino, drop_bitgrid)
        
        self.place(mino, new_bitgrid)
        self.line_clear(new_bitgrid)
        
        return new_bitgrid, drop_bitgrid
    
    def execute_move(self, move):
        if move.hold:
            self.input("hold", 0)
            self.hold_type = move.hold
            # self.input("delay", self.think_time//10)
            
        inputs = move.inputs
        for i, d in inputs:
            time = 0 if d == "tap" else self.handling["das"]
            # self.input("delay", self.think_time//10)
            self.input(i, time)
 
        # if len(inputs) == 0:
        #     print("MOVE")
        #     print_bitgrid(move.bitgrid, BOARD_W)
        #     print("GAME")
        #     print_bitgrid(grid_to_bitgrid(self.game.board.grid), BOARD_W)

        self.input("harddrop", 0)

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
        first_block_y = [None]*BOARD_W
        for y, row in enumerate(bitgrid):
            row_holes = block_mask & ~row
            for x in range(10):
                if row_holes & (1<<x):
                    holes += 1
                    if first_block_y[x]:
                        holes += (y-first_block_y[x])
                if (row & (1<<x)) and first_block_y[x] == None:
                    first_block_y[x] = y
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
        lines = 0
        lines += LINES[self.get_mode(bitgrid)][self.get_lines(bitgrid)]
        lines += TSPIN_LINES[self.get_tspins(bitgrid, blocked, mino_type)]
        change_rate = self.get_change_rate(bitgrid)
        holes = self.get_holes(bitgrid)

        weights = self.get_weights(bitgrid)
        lines *= weights["lines"] 
        change_rate *= weights["change_rate"]
        holes *= weights["holes"]
        
        return lines, change_rate, holes

    def beam_search(self):
        beam = [SearchState(tuple(self.bitgrid), self.hold_type, 0)]

        for depth in range(self.search_depth+1):
            next_beam = []
            for state in beam:
                mino_0 = self.queue[depth]
                if depth+1 < len(self.queue):
                    mino_1 = state.hold or self.queue[depth+1]

                moves = self.find_moves(mino_0, mino_1, state.bitgrid)
                for move in moves:
                    score = state.score+move.score
                    first = move if depth == 0 else state.first_move
                    next_beam.append(SearchState(tuple(move.bitgrid), move.hold, score, first))
            
            next_beam.sort(key=lambda s: s.score, reverse=True)
            beam = next_beam[:self.search_count]

            if beam == []:
                break
        
        return beam[0].first_move if beam else None
    
    # @timer
    def think(self):
        if len(self.queue) >= max(self.search_depth, 2)+1:
            move = self.beam_search()
            if move:
                self.execute_move(move)
                self.bitgrid = move.bitgrid
                # print_bitgrid(self.bitgrid, BOARD_W)
                self.line_clear(self.bitgrid)
                if move.hold and not self.first_held:
                    self.first_held = True
                    self.queue.pop(0)
                self.queue.pop(0)
        else:
            self.sync()

    def update(self, dt):
        # print_bitgrid(self.bitgrid, BOARD_W)
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

        if self.inputs:
            if self.inputs[0].down_event == None:
                self.inputs[0].timer += dt

        # print()
        # for input in self.inputs:
        #     print(input.key, end=" ")

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
            current_input = self.inputs[0]
            if current_input.down_event:
                if current_input.key != "delay":
                    events.append(current_input.down_event)
                current_input.down_event = None
            
            if current_input.timer >= current_input.time:
                if current_input.key != "delay":
                    events.append(current_input.up_event)
                self.inputs.pop(0)
                
        return events