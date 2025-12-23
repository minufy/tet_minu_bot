from minos import Mino, BIT_SHAPES
from weights import up, down
from collections import deque
from utils import print_bitgrid, grid_to_bitgrid, BOARD_W, FULL_ROW, timer
from functools import lru_cache

SEARCH_DEPTH = 4
SEARCH_COUNT = 15

DANGER_HEIGHT = 6
MAX_LEN_INPUTS = 4

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
    3: 35,
    2: 30,
    1: 0,
    0: 0
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

INPUTS = {
    "softdrop": (0, 1, 0),
    "right": (1, 0, 0),
    "chargeright": (1, 0, 0),
    "left": (-1, 0, 0),
    "chargeleft": (-1, 0, 0),
    "cw": (0, 0, 1),
    "ccw": (0, 0, -1),
    "180": (0, 0, 2),
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
    def __init__(self, game, think_time):
        self.game = game
        self.queue = [self.game.mino.type]+self.game.queue[:]
        self.last_queue = []
        self.inputs = []
        self.weights_upstack = up
        self.weights_downstack = down
        self.think_time = think_time
        self.think_timer = 0
        self.handling = game.handling
        self.hold_type = ""
        self.first_held = False
        self.search_depth = SEARCH_DEPTH
        self.search_count = SEARCH_COUNT

    def set_weights(self, up, down):
        self.weights_upstack = up
        self.weights_downstack = down

    def sync(self):
        print("syncing..")
        self.queue = [self.game.mino.type]+self.game.queue[:]
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
            visited = set()
            q = deque()
            q.append(((3, len(bitgrid)//2-4, 0), (False, 0), []))
            hold = mino_0 if mino_type == mino_1 else None
            while q:
                (x, y, r), (rotated, moved), inputs = q.popleft()
                if len(inputs) > MAX_LEN_INPUTS:
                    continue

                mino = Mino(mino_type, x, y, r)
                temp_bitgrid = list(bitgrid)
                self.soft_drop(mino, temp_bitgrid)
                self.place(mino, temp_bitgrid)

                tuple_bitgrid = tuple(temp_bitgrid[len(bitgrid)//2-4:])

                blocked = mino.move(0, -1, bitgrid) == False
                moves.append(Move(mino_type, sum(self.get_scores(tuple_bitgrid, blocked, mino_type)), temp_bitgrid, hold, inputs))
                self.line_clear(temp_bitgrid)

                move_states = []
                if len(inputs) > 1:
                    move_states.append("softdrop")
                if not rotated:
                    for key in MINO_ROTATIONS[mino_type]:
                        move_states.append((key))
                if moved < 2:
                    move_states.append("chargeright")
                    move_states.append("chargeleft")
                    move_states.append("right")
                    move_states.append("left")
                
                for d in move_states:
                    new_mino = Mino(mino_type, x, y, r)
                    dx, dy, dr = INPUTS[d]
                    if dr:
                        new_mino.rotate(dr, bitgrid)
                        
                    rep = 1
                    if d.startswith("charge") or d == "softdrop":
                        rep = len(bitgrid)
                    for _ in range(rep):
                        if new_mino.move(dx, dy, bitgrid) == False:
                            break
                    
                    xyr = (new_mino.x, new_mino.y, new_mino.rotation)
                    if xyr in visited:
                        continue
                    visited.add(xyr)

                    if y:
                        q.append((xyr, (False, 0), inputs+[d]))
                    else:
                        q.append((xyr, (dr != 0, moved+abs(dx)), inputs+[d]))

        return moves
 
    def move_mino(self, mino, x, y, bitgrid, charge):
        rep = 1
        if charge:
            rep = len(bitgrid)
        for _ in range(rep):
            if mino.move(x, y, bitgrid) == False:
                break
            
    def execute_move(self, move):
        if move.hold:
            self.input("hold", 0)
            self.hold_type = move.hold

        inputs = move.inputs
        for d in inputs:
            time = 0
            if d.startswith("charge") or d == "softdrop":
                time = self.handling["das"]+self.handling["arr"]*4
            self.input(d, time)

        self.input("harddrop", 0)

    @lru_cache(maxsize=1000)
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
    
    def get_tspin_potential(self, bitgrid, mino_type):
        if "T" not in self.queue+[self.hold_type] or mino_type == "T":
            return 0
        count = 0
        h = len(bitgrid)
        for x in range(BOARD_W-3+1):
            for y in range(h-2):
                row_1 = (bitgrid[y]>>x) & 0b111
                row_2 = (bitgrid[y+1]>>x) & 0b111
                row_3 = (bitgrid[y+2]>>x) & 0b111

                if row_1 == 0b100 or row_1 == 0b001:
                    if row_2 == 0b000:
                        if row_3 == 0b101:
                            count += 1
        return count
    
    def get_tspin_lines(self, bitgrid, blocked, mino_type):
        if not blocked or mino_type != "T":
            return 0
        return self.get_lines(bitgrid)

    @lru_cache(maxsize=1000)
    def get_scores(self, bitgrid, blocked, mino_type):
        lines = LINES[self.get_mode(bitgrid)][self.get_lines(bitgrid)]
        lines += TSPIN_LINES[self.get_tspin_lines(bitgrid, blocked, mino_type)]
        change_rate = self.get_change_rate(bitgrid)
        holes = self.get_holes(bitgrid)
        tspin_potential = self.get_tspin_potential(bitgrid, mino_type)
        height_sum = sum(self.get_heights(bitgrid))/BOARD_W

        weights = self.get_weights(bitgrid)
        lines *= weights["lines"]
        change_rate *= weights["change_rate"]
        holes *= weights["holes"]
        tspin_potential *= weights["tspin_potential"]
        height_sum *= weights["height_sum"]
        
        return lines, change_rate, holes, tspin_potential, height_sum
    
    def beam_search(self, bitgrid):
        beam = [SearchState(tuple(bitgrid), self.hold_type, 0)]

        for depth in range(self.search_depth+1):
            next_beam = []
            for state in beam:
                mino_0 = self.queue[depth]
                mino_1 = None
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
    
    def think(self, bitgrid):
        if len(self.queue) >= max(self.search_depth, 2)+1:
            move = self.beam_search(bitgrid)
            if move:
                self.execute_move(move)
                if move.hold and not self.first_held:
                    self.first_held = True
                    self.queue.pop(0)
                self.queue.pop(0)
        else:
            self.sync()

    def update(self, dt):
        if len(self.game.queue) == 11:
            bag = self.game.queue[-7:]
            if self.last_queue != bag:
                self.last_queue = bag
                self.queue += bag

        self.think_timer += dt
        if self.think_timer >= self.think_time:
            self.think_timer = 0
            if self.inputs == []:
                self.think(grid_to_bitgrid(self.game.board.grid))

        if self.inputs: 
            if self.inputs[0].down_event == None:
                self.inputs[0].timer += dt

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