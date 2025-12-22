import pygame

BOARD_W = 10
FULL_ROW = (2<<(BOARD_W-1))-1

font = pygame.font.Font("fonts/Pretendard-Regular.ttf", 20)
font_bold = pygame.font.Font("fonts/Pretendard-Bold.ttf", 30)

def render_text(font, text, color="#ffffff"):
    surface = font.render(text, True, color)
    return surface

def grid_to_bitgrid(grid, empty=" "):
    bitgrid = []
    for row in grid:
        b = 0 
        for x, cell in enumerate(row):
            if cell != empty:
                b |= (1<<x)
        bitgrid.append(b)
    return bitgrid

def print_bitgrid(bitgrid, w):
    for row in bitgrid:
        print_row = bin(row)[2:].zfill(w-1)[::-1]
        print(print_row.replace("0", "  ").replace("1", "[]"))
    print("-"*w*2)

def draw_hud(screen, bot, game):
    x = 15
    y = 20
    gap = 20

    weights_text = render_text(font_bold, "WEIGHTS", "#F6D03C")
    screen.blit(weights_text, (x, y))
    y += font_bold.get_height() 

    bitgrid = grid_to_bitgrid(game.board.grid)

    weights = bot.get_weights(bitgrid)
    for i, weight in enumerate(weights):
        text = render_text(font, f"{weight}: {weights[weight]}")
        screen.blit(text, (x, y))
        y += font.get_height()

    y += gap

    # search_text = render_text(font_bold, "SEARCH", "#42AFE1")
    # screen.blit(search_text, (x, y))
    # y += font_bold.get_height()

    # depth_text = render_text(font, f"depth: {SEARCH_DEPTH}")
    # screen.blit(depth_text, (x, y))
    # y += font.get_height()
    
    # best_count_text = render_text(font, f"count: {SEARCH_COUNT}")
    # screen.blit(best_count_text, (x, y))
    # y += font.get_height()

    # y += gap

    state_text = render_text(font_bold, "STATE", "#EB4F65")
    screen.blit(state_text, (x, y))
    y += font_bold.get_height()

    attack_text = render_text(font, f"attack: {game.attack}")
    screen.blit(attack_text, (x, y))
    y += font.get_height()
    
    mode_text = render_text(font, f"mode: {bot.get_mode(bitgrid)}")
    screen.blit(mode_text, (x, y))
    y += font.get_height()

    max_height_text = render_text(font, f"max_height: {max(bot.get_heights(bitgrid))}")
    screen.blit(max_height_text, (x, y))
    y += font.get_height()