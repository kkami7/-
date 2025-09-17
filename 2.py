import pygame
import random
import sys

pygame.init()

FPS = 60
WIDTH, HEIGHT = 1000, 800
RIGHT_PANEL = 200
GAME_WIDTH = WIDTH - RIGHT_PANEL
ROWS, COLS = 4, 4
RECT_WIDTH = GAME_WIDTH // COLS
RECT_HEIGHT = HEIGHT // ROWS

OUTLINE_COLOR = (187, 173, 160)
OUTLINE_THICKNESS = 8
BACKGROUND_COLOR = (205, 192, 180)
FONT_COLOR = (119, 110, 101)

FONT = pygame.font.SysFont("comicsans", 48, bold=True)
SMALL_FONT = pygame.font.SysFont("comicsans", 26, bold=True)
SCORE_FONT = pygame.font.SysFont("comicsans", 20, bold=True)  # 스코어 전용 폰트 추가

WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048 (space to restart)")

score = 0
leaderboard = []
game_over = False

COLOR_MAP = {
    0: (205, 193, 180),
    2: (237, 229, 218),
    4: (238, 225, 201),
    8: (243, 178, 122),
    16: (246, 150, 101),
    32: (247, 124, 95),
    64: (247, 95, 59),
    128: (237, 208, 115),
    256: (237, 204, 99),
    512: (236, 202, 80),
    1024: (190, 170, 50),
    2048: (120, 100, 40),
}

def get_color(value):
    return COLOR_MAP.get(value, (100, 80, 40))

def draw(grid):
    WINDOW.fill(BACKGROUND_COLOR)
    
    # 타일
    for r in range(ROWS):
        for c in range(COLS):
            val = grid[r][c]
            x = c * RECT_WIDTH
            y = r * RECT_HEIGHT
            rect = pygame.Rect(x + 10, y + 10, RECT_WIDTH - 20, RECT_HEIGHT - 20)
            pygame.draw.rect(WINDOW, get_color(val), rect, border_radius=8)
            
            if val != 0:
                text = FONT.render(str(val), True, FONT_COLOR)
                WINDOW.blit(text, (x + RECT_WIDTH//2 - text.get_width()//2, 
                                 y + RECT_HEIGHT//2 - text.get_height()//2))
    
    # 외곽선
    pygame.draw.rect(WINDOW, OUTLINE_COLOR, (0, 0, GAME_WIDTH, HEIGHT), 
                     OUTLINE_THICKNESS, border_radius=8)
    
    # 스코어 표시 (줄바꿈으로 처리)
    score_label = SCORE_FONT.render("Score:", True, FONT_COLOR)
    score_value = SCORE_FONT.render(str(score), True, FONT_COLOR)
    
    WINDOW.blit(score_label, (GAME_WIDTH + 10, 20))
    WINDOW.blit(score_value, (GAME_WIDTH + 10, 45))
    
    # 리더보드
    lb_title = SMALL_FONT.render("Leaderboard:", True, FONT_COLOR)
    WINDOW.blit(lb_title, (GAME_WIDTH + 10, 90))
    
    for i, s in enumerate(leaderboard[:10]):
        # 리더보드 항목도 길면 줄바꿈
        entry_text = f"{i+1}. {s}"
        if len(entry_text) > 15:  # 너무 길면 줄임
            entry_text = f"{i+1}. {s//1000}k"
        entry = SMALL_FONT.render(entry_text, True, FONT_COLOR)
        WINDOW.blit(entry, (GAME_WIDTH + 10, 120 + i * 25))
    
    # 게임 오버 시 표시
    if game_over:
        go_text = FONT.render("GAME OVER!", True, (255, 0, 0))
        restart_text = SMALL_FONT.render("Press SPACE to restart", True, FONT_COLOR)
        WINDOW.blit(go_text, (GAME_WIDTH//2 - go_text.get_width()//2, 
                             HEIGHT//2 - go_text.get_height()//2))
        WINDOW.blit(restart_text, (GAME_WIDTH//2 - restart_text.get_width()//2, 
                                  HEIGHT//2 + 40))
    
    pygame.display.update()

def add_random_tile(grid):
    empties = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == 0]
    if not empties:
        return False
    r, c = random.choice(empties)
    grid[r][c] = random.choices([2, 4], weights=[0.9, 0.1])[0]
    return True

def compress_and_merge(line):
    new = [v for v in line if v != 0]
    merged = []
    gained = 0
    i = 0
    while i < len(new):
        if i + 1 < len(new) and new[i] == new[i+1]:
            val = new[i] * 2
            merged.append(val)
            gained += val
            i += 2
        else:
            merged.append(new[i])
            i += 1
    merged += [0] * (COLS - len(merged))
    return merged, gained

def move_grid(grid, direction):
    moved = False
    total_gained = 0
    new_grid = [row[:] for row in grid]
    
    if direction in ('left', 'right'):
        for r in range(ROWS):
            row = grid[r][:]
            if direction == 'right':
                row = row[::-1]
            compressed, gained = compress_and_merge(row)
            if direction == 'right':
                compressed = compressed[::-1]
            new_grid[r] = compressed
            if compressed != grid[r]:
                moved = True
            total_gained += gained
    else:
        for c in range(COLS):
            col = [grid[r][c] for r in range(ROWS)]
            if direction == 'down':
                col = col[::-1]
            compressed, gained = compress_and_merge(col)
            if direction == 'down':
                compressed = compressed[::-1]
            for r in range(ROWS):
                new_grid[r][c] = compressed[r]
            if [new_grid[r][c] for r in range(ROWS)] != [grid[r][c] for r in range(ROWS)]:
                moved = True
            total_gained += gained
    
    return moved, total_gained, new_grid

def can_move(grid):
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] == 0:
                return True
    
    for r in range(ROWS):
        for c in range(COLS - 1):
            if grid[r][c] == grid[r][c+1]:
                return True
    
    for c in range(COLS):
        for r in range(ROWS - 1):
            if grid[r][c] == grid[r+1][c]:
                return True
    
    return False

def update_leaderboard():
    global leaderboard, score
    leaderboard.append(score)
    leaderboard = sorted(leaderboard, reverse=True)[:10]

def reset_game():
    global score, game_over
    grid = [[0]*COLS for _ in range(ROWS)]
    score = 0
    game_over = False
    add_random_tile(grid)
    add_random_tile(grid)
    return grid

def main():
    global score, game_over
    clock = pygame.time.Clock()
    grid = reset_game()
    running = True
    
    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
                
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_SPACE:
                        grid = reset_game()
                else:
                    dir_map = {
                        pygame.K_LEFT: 'left',
                        pygame.K_RIGHT: 'right',
                        pygame.K_UP: 'up',
                        pygame.K_DOWN: 'down'
                    }
                    
                    if event.key in dir_map:
                        direction = dir_map[event.key]
                        moved, gained, new_grid = move_grid(grid, direction)
                        
                        if moved:
                            grid = new_grid
                            score += gained
                            add_random_tile(grid)
                            
                            if not can_move(grid):
                                game_over = True
                                update_leaderboard()
        
        draw(grid)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()