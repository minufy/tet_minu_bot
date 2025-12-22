from utils import grid_to_bitgrid, FULL_ROW

I_OFFSETS = {
    "01": [[1, 0], [-2, 0], [-2, 1], [1, -2]],
    "10": [[-1, 0], [2, 0], [-1, 2], [2, -1]],
    "12": [[-1, 0], [2, 0], [-1, -2], [2, 1]],
    "21": [[-2, 0], [1, 0], [-2, -1], [1, 2]],
    "23": [[2, 0], [-1, 0], [2, -1], [-1, 2]],
    "32": [[1, 0], [-2, 0], [1, -2], [-2, 1]],
    "30": [[1, 0], [-2, 0], [1, 2], [-2, -1]],
    "03": [[-1, 0], [2, 0], [2, 1], [-1, -2]],
    "02": [[0, -1]],
    "13": [[1, 0]],
    "20": [[0, 1]],
    "31": [[-1, 0]],
}

JLTSZ_OFFSETS = {
    "01": [[-1, 0], [-1, -1], [0, 2], [-1, 2]],
    "10": [[1, 0], [1, 1], [0, -2], [1, -2]],
    "12": [[1, 0], [1, 1], [0, -2], [1, -2]],
    "21": [[-1, 0], [-1, -1], [0, 2], [-1, 2]],
    "23": [[1, 0], [1, -1], [0, 2], [1, 2]],
    "32": [[-1, 0], [-1, 1], [0, -2], [-1, -2]],
    "30": [[-1, 0], [-1, 1], [0, -2], [-1, -2]],
    "03": [[1, 0], [1, -1], [0, 2], [1, 2]],
    "02": [[0, -1], [1, -1], [-1, -1], [1, 0], [-1, 0]],
    "13": [[1, 0], [1, -2], [1, -1], [0, -2], [0, -1]],
    "20": [[0, 1], [-1, 1], [1, 1], [-1, 0], [1, 0]],
    "31": [[-1, 0], [-1, -2], [-1, -1], [0, -2], [0, -1]],
}
 
MINO_TYPES = ["Z", "L", "O", "S", "I", "J", "T"]
MINO_SHAPES = {
    "I": {
        "0": (
            (0, 0, 0, 0),
            (1, 1, 1, 1),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
        ),
        "1": (
            (0, 0, 1, 0),
            (0, 0, 1, 0),
            (0, 0, 1, 0),
            (0, 0, 1, 0),
        ),
        "2": (
            (0, 0, 0, 0),
            (0, 0, 0, 0),
            (1, 1, 1, 1),
            (0, 0, 0, 0),
        ),
        "3": (
            (0, 1, 0, 0),
            (0, 1, 0, 0),
            (0, 1, 0, 0),
            (0, 1, 0, 0),
        ),
    },
    "O": {
        "0": (
            (0, 1, 1, 0),
            (0, 1, 1, 0),
        ),
        "1": (
            (0, 1, 1, 0),
            (0, 1, 1, 0),
        ),
        "2": (
            (0, 1, 1, 0),
            (0, 1, 1, 0),
        ),
        "3": (
            (0, 1, 1, 0),
            (0, 1, 1, 0),
        ),
    },
    "T": {
        "0": (
            (0, 1, 0),
            (1, 1, 1),
            (0, 0, 0),
        ),
        "1": (
            (0, 1, 0),
            (0, 1, 1),
            (0, 1, 0),
        ),
        "2": (
            (0, 0, 0),
            (1, 1, 1),
            (0, 1, 0),
        ),
        "3": (
            (0, 1, 0),
            (1, 1, 0),
            (0, 1, 0),
        ),
    },
    "S": {
        "0": (
            (0, 1, 1),
            (1, 1, 0),
            (0, 0, 0),
        ),
        "1": (
            (0, 1, 0),
            (0, 1, 1),
            (0, 0, 1),
        ),
        "2": (
            (0, 0, 0),
            (0, 1, 1),
            (1, 1, 0),
        ),
        "3": (
            (1, 0, 0),
            (1, 1, 0),
            (0, 1, 0),
        ),
    },
    "Z": {
        "0": (
            (1, 1, 0),
            (0, 1, 1),
            (0, 0, 0),
        ),
        "1": (
            (0, 0, 1),
            (0, 1, 1),
            (0, 1, 0),
        ),
        "2": (
            (0, 0, 0),
            (1, 1, 0),
            (0, 1, 1),
        ),
        "3": (
            (0, 1, 0),
            (1, 1, 0),
            (1, 0, 0),
        ),
    },
    "J": {
        "0": (
            (1, 0, 0),
            (1, 1, 1),
            (0, 0, 0),
        ),
        "1": (
            (0, 1, 1),
            (0, 1, 0),
            (0, 1, 0),
        ),
        "2": (
            (0, 0, 0),
            (1, 1, 1),
            (0, 0, 1),
        ),
        "3": (
            (0, 1, 0),
            (0, 1, 0),
            (1, 1, 0),
        ),
    },
    "L": {
        "0": (
            (0, 0, 1),
            (1, 1, 1),
            (0, 0, 0),
        ),
        "1": (
            (0, 1, 0),
            (0, 1, 0),
            (0, 1, 1),
        ),
        "2": (
            (0, 0, 0),
            (1, 1, 1),
            (1, 0, 0),
        ),
        "3": (
            (1, 1, 0),
            (0, 1, 0),
            (0, 1, 0),
        ),
    },
}

BIT_SHAPES = {}
for type in MINO_SHAPES:
    BIT_SHAPES[type] = {}
    for r in MINO_SHAPES[type]:
        BIT_SHAPES[type][r] = grid_to_bitgrid(MINO_SHAPES[type][r], 0)

class Mino:
    def __init__(self, type, x, y, rotation=0):
        self.type = type
        self.x = x
        self.y = y
        self.rotation = rotation

    def check_collison(self, bitgrid):
        bit_shape = BIT_SHAPES[self.type][str(self.rotation)]
        for i, row in enumerate(bit_shape):
            if row == 0: 
                continue
        
            target_y = self.y+i
            if target_y < 0: 
                continue
            if target_y >= len(bitgrid):
                return True
            
            if self.x >= 0:
                shifted_row = row << self.x
            else:
                shifted_row = row >> abs(self.x)

            if self.x < 0:
                if (shifted_row << abs(self.x)) != row:
                    return True
            
            if shifted_row > FULL_ROW:
                return True
            
            if bitgrid[target_y] & shifted_row:
                return True
            
        return False

    def test_offsets(self, bitgrid, offsets):
        for x, y in offsets:
            if self.move(x, -y, bitgrid):
                return True
        return False

    def rotate(self, r, bitgrid):
        if self.type == "O":
            return
        old_rotation = self.rotation
        self.rotation += r
        if self.rotation >= 4:
            self.rotation -= 4
        if self.rotation < 0:
            self.rotation += 4
        if self.check_collison(bitgrid):
            key = f"{old_rotation}{self.rotation}"
            offsets = JLTSZ_OFFSETS[key]
            if self.type == "I":
                offsets = I_OFFSETS[key]
            if self.test_offsets(bitgrid, offsets) == False:
                self.rotation = old_rotation

    def move(self, x, y, board):
        self.x += x
        self.y += y
        if self.check_collison(board):
            self.x -= x
            self.y -= y
            return False
        return True