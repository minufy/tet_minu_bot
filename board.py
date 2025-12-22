class TestBoard:
    def __init__(self, grid):
        self.grid = [row.copy() for row in grid]
        self.w = len(self.grid[0])
        self.h = len(self.grid)

    def __repr__(self):
        s = "-"*self.w+"\n"
        for y in range(20, self.h):
            s += "".join(self.grid[y])+"\n"
        return s