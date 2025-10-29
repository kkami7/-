import pygame
import random
import sys
import json
import os
import math

pygame.init()

# ==================== 전역 설정 ====================
FPS = 60
WIDTH, HEIGHT = 1000, 800
RIGHT_PANEL = 200
GAME_WIDTH = WIDTH - RIGHT_PANEL

# 색상
BG_COLOR = (205, 192, 180)
OUTLINE_COLOR = (187, 173, 160)
FONT_COLOR = (119, 110, 101)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# 게임 상태
MENU, GAME_2048, GAME_BREAKOUT = "menu", "2048", "breakout"
RESET_PASSWORD = "reset2048"

# ==================== 2048 설정 ====================
ROWS, COLS = 4, 4
RECT_WIDTH = GAME_WIDTH // COLS
RECT_HEIGHT = HEIGHT // ROWS

COLOR_MAP = {
    0: (205, 193, 180), 2: (237, 229, 218), 4: (238, 225, 201),
    8: (243, 178, 122), 16: (246, 150, 101), 32: (247, 124, 95),
    64: (247, 95, 59), 128: (237, 208, 115), 256: (237, 204, 99),
    512: (236, 202, 80), 1024: (190, 170, 50), 2048: (120, 100, 40)
}

# ==================== 블록깨기 설정 ====================
PADDLE_W, PADDLE_H, PADDLE_SPEED = 120, 20, 8
BALL_R, BALL_SPEED = 8, 6
BRICK_COLS = 10
BRICK_MARGIN_COLS = 1  # 양쪽 끝 제외
BRICK_W = GAME_WIDTH // BRICK_COLS
BRICK_H = 30

# 블록 종류별 개수 (고정)
BRICK_COLORS = {
    1: (46, 204, 113),   # 초록 - 내구도 1
    2: (241, 196, 15),   # 노랑 - 내구도 2
    3: (231, 76, 60),    # 빨강 - 내구도 3
    'speed': (100, 180, 255)  # 파랑 - 속도 부스트
}

DIFFICULTY = {
    'easy': {
        'speed': 6, 
        'paddle': 120, 
        'rows': 5, 
        'bricks': {'1': 24, '2': 10, '3': 3, 'speed': 3}  # 총 40개 (내구도1 중 10개가 공 생성)
    },
    'normal': {
        'speed': 6, 
        'paddle': 120, 
        'rows': 6, 
        'bricks': {'1': 27, '2': 12, '3': 6, 'speed': 3}  # 총 48개
    },
    'hard': {
        'speed': 6, 
        'paddle': 120, 
        'rows': 7, 
        'bricks': {'1': 27, '2': 15, '3': 11, 'speed': 3}  # 총 56개
    }
}

# ==================== 폰트 초기화 ====================
def init_fonts():
    fonts = ["malgun gothic", "맑은 고딕", "nanum gothic", "나눔고딕"]
    for name in fonts:
        try:
            return {
                'large': pygame.font.SysFont(name, 48, bold=True),
                'medium': pygame.font.SysFont(name, 26, bold=True),
                'small': pygame.font.SysFont(name, 20, bold=True),
                'tiny': pygame.font.SysFont(name, 14)
            }
        except:
            continue
    return {k: pygame.font.Font(None, s) for k, s in 
            [('large', 48), ('medium', 26), ('small', 20), ('tiny', 14)]}

FONTS = init_fonts()
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("게임 모음")

# ==================== 리더보드 관리 ====================
def get_leaderboard_file(game_type, difficulty=None):
    """리더보드 파일명 반환"""
    if game_type == GAME_BREAKOUT and difficulty:
        return f"leaderboard_{game_type}_{difficulty}.json"
    return f"leaderboard_{game_type}.json"

def load_leaderboard(game_type, difficulty=None):
    """리더보드 로드"""
    file = get_leaderboard_file(game_type, difficulty)
    try:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def save_leaderboard(game_type, scores, difficulty=None):
    """리더보드 저장"""
    file = get_leaderboard_file(game_type, difficulty)
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def update_leaderboard(game_type, score, difficulty=None):
    """리더보드 업데이트"""
    if score <= 0:
        return load_leaderboard(game_type, difficulty)
    
    lb = load_leaderboard(game_type, difficulty)
    lb.append(score)
    lb = list(set(lb))  # 중복 제거
    
    # 정렬: 블록깨기는 오름차순(시간), 2048은 내림차순(점수)
    lb = sorted(lb)[:10] if game_type == GAME_BREAKOUT else sorted(lb, reverse=True)[:10]
    save_leaderboard(game_type, lb, difficulty)
    return lb

def reset_leaderboard(game_type, difficulty=None):
    """리더보드 리셋"""
    return save_leaderboard(game_type, [], difficulty)

# ==================== UI 함수 ====================
def draw_button(rect, text, font='medium'):
    """버튼 그리기"""
    pygame.draw.rect(WINDOW, (237, 229, 218), rect, border_radius=10)
    pygame.draw.rect(WINDOW, OUTLINE_COLOR, rect, 3, border_radius=10)
    txt = FONTS[font].render(text, True, FONT_COLOR)
    WINDOW.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

def draw_text_centered(text, y, font='medium', color=FONT_COLOR):
    """중앙 정렬 텍스트"""
    txt = FONTS[font].render(text, True, color)
    WINDOW.blit(txt, (WIDTH//2 - txt.get_width()//2, y))

def draw_panel_separator(y):
    """패널 구분선"""
    pygame.draw.line(WINDOW, OUTLINE_COLOR, (GAME_WIDTH + 10, y), (WIDTH - 10, y), 2)

def draw_panel_header(score_label, score_value, y=20):
    """패널 헤더 (점수/시간)"""
    WINDOW.blit(FONTS['small'].render(score_label, True, FONT_COLOR), (GAME_WIDTH + 10, y))
    WINDOW.blit(FONTS['small'].render(str(score_value), True, FONT_COLOR), (GAME_WIDTH + 10, y + 25))
    return y + 60

def draw_leaderboard(leaderboard, y, is_time=False):
    """리더보드 표시"""
    WINDOW.blit(FONTS['medium'].render("Best Times:" if is_time else "Leaderboard:", True, FONT_COLOR), 
                (GAME_WIDTH + 10, y))
    y += 25
    WINDOW.blit(FONTS['tiny'].render("R: reset, ESC: menu", True, FONT_COLOR), (GAME_WIDTH + 10, y))
    y += 25
    
    for i, s in enumerate(leaderboard[:8]):
        txt = f"{i+1}. {s}s" if is_time else (f"{i+1}. {s:,}" if len(f"{s:,}") < 12 else f"{i+1}. {s//1000}k")
        WINDOW.blit(FONTS['medium'].render(txt, True, FONT_COLOR), (GAME_WIDTH + 10, y + i * 25))

def draw_password_overlay(pw_input):
    """비밀번호 입력 오버레이"""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(128)
    overlay.fill(BLACK)
    WINDOW.blit(overlay, (0, 0))
    
    box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 300, 100)
    pygame.draw.rect(WINDOW, WHITE, box)
    pygame.draw.rect(WINDOW, OUTLINE_COLOR, box, 3)
    
    texts = ["Enter Reset Password:", "*" * len(pw_input), "ESC: cancel, ENTER: confirm"]
    fonts = ['medium', 'medium', 'tiny']
    for i, (text, font) in enumerate(zip(texts, fonts)):
        surf = FONTS[font].render(text, True, FONT_COLOR)
        WINDOW.blit(surf, (WIDTH//2 - surf.get_width()//2, HEIGHT//2 - 40 + i * 30))

def draw_game_over(won=False, time=None):
    """게임 종료 화면"""
    color = (0, 255, 0) if won else (255, 0, 0)
    text = "YOU WIN!" if won else "GAME OVER!"
    
    draw_text_centered(text, HEIGHT//2 - 60, 'large', color)
    
    if time is not None:
        draw_text_centered(f"Time: {time}s", HEIGHT//2 - 10, 'medium')
    
    draw_text_centered("SPACE: restart", HEIGHT//2 + 30, 'medium')
    
    if won or (time is None and not won):
        draw_text_centered("Record saved!", HEIGHT//2 + 60, 'medium', (0, 150, 0))

# ==================== 메뉴 ====================
def run_menu():
    WINDOW.fill(BG_COLOR)
    draw_text_centered("게임 선택", 100, 'large')
    
    buttons = []
    games = ["1. 2048 게임", "2. 블록깨기"]
    for i, name in enumerate(games):
        btn = pygame.Rect(WIDTH//2 - 150, 250 + i * 120, 300, 80)
        draw_button(btn, name)
        buttons.append(btn)
    
    draw_text_centered("클릭하거나 숫자키(1,2)를 눌러 선택하세요", 550, 'small')
    pygame.display.update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if buttons[0].collidepoint(pos):
                return GAME_2048
            elif buttons[1].collidepoint(pos):
                return GAME_BREAKOUT
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return GAME_2048
            elif event.key == pygame.K_2:
                return GAME_BREAKOUT
    return MENU

# ==================== 2048 게임 ====================
def compress_merge(line):
    """2048 라인 압축 및 병합"""
    new = [v for v in line if v]
    merged, gained, i = [], 0, 0
    while i < len(new):
        if i + 1 < len(new) and new[i] == new[i+1]:
            val = new[i] * 2
            merged.append(val)
            gained += val
            i += 2
        else:
            merged.append(new[i])
            i += 1
    return merged + [0] * (COLS - len(merged)), gained

def move_grid(grid, direction):
    """2048 그리드 이동"""
    moved, total_gained = False, 0
    new_grid = [row[:] for row in grid]
    
    if direction in ('left', 'right'):
        for r in range(ROWS):
            row = grid[r][::-1] if direction == 'right' else grid[r][:]
            compressed, gained = compress_merge(row)
            new_grid[r] = compressed[::-1] if direction == 'right' else compressed
            if new_grid[r] != grid[r]:
                moved = True
            total_gained += gained
    else:
        for c in range(COLS):
            col = [grid[r][c] for r in range(ROWS)]
            if direction == 'down':
                col = col[::-1]
            compressed, gained = compress_merge(col)
            if direction == 'down':
                compressed = compressed[::-1]
            for r in range(ROWS):
                new_grid[r][c] = compressed[r]
            if [new_grid[r][c] for r in range(ROWS)] != [grid[r][c] for r in range(ROWS)]:
                moved = True
            total_gained += gained
    
    return moved, total_gained, new_grid

def can_move(grid):
    """이동 가능 여부 확인"""
    for r in range(ROWS):
        for c in range(COLS):
            if not grid[r][c]:
                return True
            if c < COLS-1 and grid[r][c] == grid[r][c+1]:
                return True
            if r < ROWS-1 and grid[r][c] == grid[r+1][c]:
                return True
    return False

def add_new_tile(grid):
    """새 타일 추가"""
    empties = [(r, c) for r in range(ROWS) for c in range(COLS) if not grid[r][c]]
    if empties:
        r, c = random.choice(empties)
        grid[r][c] = 2

def draw_2048(grid, score, lb, game_over, entering_pw, pw_input):
    """2048 화면 그리기"""
    WINDOW.fill(BG_COLOR)
    
    # 타일 그리기
    for r in range(ROWS):
        for c in range(COLS):
            val = grid[r][c]
            color = COLOR_MAP.get(val, (100, 80, 40))
            rect = pygame.Rect(c * RECT_WIDTH + 10, r * RECT_HEIGHT + 10, 
                             RECT_WIDTH - 20, RECT_HEIGHT - 20)
            pygame.draw.rect(WINDOW, color, rect, border_radius=8)
            
            if val:
                txt = FONTS['large'].render(str(val), True, FONT_COLOR)
                WINDOW.blit(txt, (rect.centerx - txt.get_width()//2,
                                rect.centery - txt.get_height()//2))
    
    pygame.draw.rect(WINDOW, OUTLINE_COLOR, (0, 0, GAME_WIDTH, HEIGHT), 8, border_radius=8)
    
    # 패널
    pygame.draw.line(WINDOW, OUTLINE_COLOR, (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
    y = draw_panel_header("Score:", score)
    draw_panel_separator(y)
    draw_leaderboard(lb, y + 10)
    
    if entering_pw:
        draw_password_overlay(pw_input)
    elif game_over:
        draw_game_over()
    
    pygame.display.update()

def run_2048():
    grid = [[0]*COLS for _ in range(ROWS)]
    for _ in range(2):
        add_new_tile(grid)
    
    score = 0
    game_over = False
    entering_pw = False
    pw_input = ""
    lb = load_leaderboard(GAME_2048)
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            if event.type == pygame.KEYDOWN:
                if entering_pw:
                    if event.key == pygame.K_ESCAPE:
                        entering_pw = False
                        pw_input = ""
                    elif event.key == pygame.K_RETURN:
                        if pw_input == RESET_PASSWORD:
                            reset_leaderboard(GAME_2048)
                            lb = load_leaderboard(GAME_2048)
                        entering_pw = False
                        pw_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        pw_input = pw_input[:-1]
                    elif event.unicode.isprintable() and len(pw_input) < 20:
                        pw_input += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        return MENU
                    elif event.key == pygame.K_r and not game_over:
                        entering_pw = True
                    elif game_over and event.key == pygame.K_SPACE:
                        return GAME_2048
                    else:
                        dirs = {pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right',
                               pygame.K_UP: 'up', pygame.K_DOWN: 'down'}
                        if event.key in dirs and not game_over:
                            moved, gained, new_grid = move_grid(grid, dirs[event.key])
                            if moved:
                                grid = new_grid
                                score += gained
                                add_new_tile(grid)
                                
                                if not can_move(grid):
                                    game_over = True
                                    lb = update_leaderboard(GAME_2048, score)
        
        draw_2048(grid, score, lb, game_over, entering_pw, pw_input)

# ==================== 블록깨기 ====================
class Paddle:
    def __init__(self, width=PADDLE_W):
        self.width = width
        self.height = PADDLE_H
        self.rect = pygame.Rect(GAME_WIDTH//2 - width//2, HEIGHT - 60, width, PADDLE_H)
        self.base_speed = PADDLE_SPEED
        self.speed = PADDLE_SPEED
        self.boost = False
        self.boost_end = 0
    
    def update(self):
        if self.boost and pygame.time.get_ticks() >= self.boost_end:
            self.boost = False
            self.speed = self.base_speed
    
    def move(self, dx):
        self.rect.x = max(0, min(GAME_WIDTH - self.width, self.rect.x + dx * self.speed))
    
    def apply_boost(self, duration=5000):
        if not self.boost:
            self.boost = True
            self.boost_end = pygame.time.get_ticks() + duration
            self.speed = self.base_speed * 2
    
    def draw(self):
        color = (100, 200, 255) if self.boost else (52, 152, 219)
        pygame.draw.rect(WINDOW, color, self.rect, border_radius=5)

class Ball:
    def __init__(self, x=None, y=None, speed=BALL_SPEED):
        self.x = x or GAME_WIDTH // 2
        self.y = y or HEIGHT - 100
        self.base_speed = speed
        self.speed = speed
        self.boost = False
        self.boost_end = 0
        angle = random.uniform(-60, 60)
        self.dx = speed * math.sin(math.radians(angle))
        self.dy = -speed * math.cos(math.radians(angle))
        self.active = False
    
    def apply_boost(self, duration=5000):
        if not self.boost:
            self.boost = True
            self.boost_end = pygame.time.get_ticks() + duration
            self.dx *= 2
            self.dy *= 2
            self.speed = self.base_speed * 2
    
    def update(self):
        if not self.active:
            return
        
        if self.boost and pygame.time.get_ticks() >= self.boost_end:
            self.boost = False
            self.dx /= 2
            self.dy /= 2
            self.speed = self.base_speed
        
        self.x += self.dx
        self.y += self.dy
        
        # 벽 충돌
        if self.x - BALL_R <= 0 or self.x + BALL_R >= GAME_WIDTH:
            self.dx = -self.dx
            self.x = max(BALL_R, min(GAME_WIDTH - BALL_R, self.x))
        if self.y - BALL_R <= 0:
            self.dy = -self.dy
            self.y = BALL_R
    
    def draw(self):
        color = (255, 255, 0) if self.boost else WHITE
        pygame.draw.circle(WINDOW, color, (int(self.x), int(self.y)), BALL_R)

class Brick:
    def __init__(self, x, y, brick_type, ball_count=0):
        self.rect = pygame.Rect(x, y, BRICK_W - 5, BRICK_H - 5)
        self.type = brick_type  # '1', '2', '3', 'speed'
        self.ball_count = ball_count  # 이 블록을 깨면 생성될 공 개수 (0, 1, 2)
        
        if brick_type == 'speed':
            self.dur = 1
            self.max_dur = 1
            # 속도 부스트는 내구도 1과 같은 색상
            self.base_color = BRICK_COLORS[1]
        else:
            self.dur = int(brick_type)
            self.max_dur = int(brick_type)
            self.base_color = BRICK_COLORS[int(brick_type)]
        
        self.color = self.base_color
        self.alive = True
    
    def hit(self):
        self.dur -= 1
        if self.dur <= 0:
            self.alive = False
            return True
        self.color = tuple(int(c * self.dur / self.max_dur) for c in self.base_color)
        return False
    
    def draw(self):
        if self.alive:
            pygame.draw.rect(WINDOW, self.color, self.rect, border_radius=5)
            
            # 내구도 표시
            if self.type in ['1', '2', '3'] and self.dur > 1:
                txt = FONTS['tiny'].render(str(self.dur), True, WHITE)
                WINDOW.blit(txt, (self.rect.centerx - txt.get_width()//2,
                                self.rect.centery - txt.get_height()//2))

class Item:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
    
    def update(self):
        self.y += 3
        if self.y > HEIGHT:
            self.active = False
    
    def draw(self):
        if self.active:
            # 파란색 속도 부스트
            pygame.draw.circle(WINDOW, (50, 150, 255), (int(self.x), int(self.y)), 15)
            pygame.draw.circle(WINDOW, (100, 180, 255), (int(self.x), int(self.y)), 12)
            txt = FONTS['tiny'].render("SPD", True, WHITE)
            WINDOW.blit(txt, (self.x - txt.get_width()//2, self.y - 8))
            txt2 = FONTS['tiny'].render("x2", True, WHITE)
            WINDOW.blit(txt2, (self.x - txt2.get_width()//2, self.y + 1))

def select_difficulty():
    """난이도 선택"""
    difficulties = [
        ('Easy', '5 Rows, Mostly Green Bricks'),
        ('Normal', '6 Rows, Balanced Mix'),
        ('Hard', '7 Rows, Tough Bricks')
    ]
    
    while True:
        WINDOW.fill(BG_COLOR)
        draw_text_centered("Select Difficulty", 100, 'large')
        
        buttons = []
        for i, (diff, desc) in enumerate(difficulties):
            btn = pygame.Rect(WIDTH//2 - 200, 230 + i * 120, 400, 90)
            pygame.draw.rect(WINDOW, (237, 229, 218), btn, border_radius=10)
            pygame.draw.rect(WINDOW, OUTLINE_COLOR, btn, 3, border_radius=10)
            
            txt_diff = FONTS['medium'].render(f"{i+1}. {diff}", True, FONT_COLOR)
            txt_desc = FONTS['tiny'].render(desc, True, FONT_COLOR)
            WINDOW.blit(txt_diff, (WIDTH//2 - txt_diff.get_width()//2, 245 + i * 120))
            WINDOW.blit(txt_desc, (WIDTH//2 - txt_desc.get_width()//2, 275 + i * 120))
            buttons.append(btn)
        
        draw_text_centered("Click or press number key (1,2,3) to select", 650, 'small')
        draw_text_centered("ESC: Back to menu", 690, 'small')
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(buttons):
                    if btn.collidepoint(pygame.mouse.get_pos()):
                        return ['easy', 'normal', 'hard'][i]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return MENU
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    return ['easy', 'normal', 'hard'][event.key - pygame.K_1]

def create_bricks(settings):
    """블록 생성 - 난이도별 공 생성 블록"""
    bricks = []
    rows = settings['rows']
    brick_counts = settings['bricks']
    active_cols = BRICK_COLS - 2 * BRICK_MARGIN_COLS
    total_positions = rows * active_cols
    
    # 블록 타입 리스트 생성 (고정 개수)
    brick_types = []
    for brick_type, count in brick_counts.items():
        brick_types.extend([brick_type] * count)
    
    # 남은 공간은 내구도 1 블록으로 채우기
    while len(brick_types) < total_positions:
        brick_types.append('1')
    
    # 섞기
    random.shuffle(brick_types)
    
    # 난이도별 공 생성 블록 설정
    durability_1_indices = [i for i, t in enumerate(brick_types) if t == '1']
    ball_config = settings.get('ball_blocks', {'count': 10, 'distribution': [2]*5 + [1]*5})
    ball_count = ball_config['count']
    ball_distribution = ball_config['distribution']
    
    ball_indices = random.sample(durability_1_indices, min(ball_count, len(durability_1_indices)))
    ball_counts = ball_distribution[:len(ball_indices)]
    random.shuffle(ball_counts)
    
    # 블록 배치
    idx = 0
    ball_idx = 0
    for row in range(rows):
        for col in range(BRICK_MARGIN_COLS, BRICK_COLS - BRICK_MARGIN_COLS):
            if idx < len(brick_types):
                brick_type = brick_types[idx]
                ball_count = 0
                
                # 공 생성 블록 지정
                if idx in ball_indices:
                    ball_count = ball_counts[ball_idx]
                    ball_idx += 1
                
                bricks.append(Brick(col * BRICK_W + 2, row * BRICK_H + 50, brick_type, ball_count))
                idx += 1
    
    return bricks

def run_breakout():
    difficulty = select_difficulty()
    if difficulty is None:
        return None
    if difficulty == MENU:
        return MENU
    
    settings = DIFFICULTY[difficulty]
    paddle = Paddle(settings['paddle'])
    balls = [Ball(speed=settings['speed'])]
    bricks = create_bricks(settings)
    items = []
    
    game_over = False
    game_started = False
    entering_pw = False
    pw_input = ""
    start_time = None
    elapsed = 0
    
    lb = load_leaderboard(GAME_BREAKOUT, difficulty)
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        
        if game_started and not game_over and start_time:
            elapsed = (pygame.time.get_ticks() - start_time) / 1000
        
        # 입력 처리
        keys = pygame.key.get_pressed()
        if not game_over and not entering_pw:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                paddle.move(-1)
                for ball in balls:
                    if not ball.active:
                        ball.x = paddle.rect.centerx
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                paddle.move(1)
                for ball in balls:
                    if not ball.active:
                        ball.x = paddle.rect.centerx
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            if event.type == pygame.KEYDOWN:
                if entering_pw:
                    if event.key == pygame.K_ESCAPE:
                        entering_pw = False
                        pw_input = ""
                    elif event.key == pygame.K_RETURN:
                        if pw_input == RESET_PASSWORD:
                            reset_leaderboard(GAME_BREAKOUT, difficulty)
                            lb = load_leaderboard(GAME_BREAKOUT, difficulty)
                        entering_pw = False
                        pw_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        pw_input = pw_input[:-1]
                    elif event.unicode.isprintable() and len(pw_input) < 20:
                        pw_input += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        return MENU
                    elif event.key == pygame.K_r and not game_over:
                        entering_pw = True
                    elif event.key == pygame.K_SPACE:
                        if game_over or all(not b.alive for b in bricks):
                            return GAME_BREAKOUT
                        for ball in balls:
                            ball.active = True
                        if not game_started:
                            game_started = True
                            start_time = pygame.time.get_ticks()
        
        # 게임 로직
        if not game_over and not entering_pw:
            paddle.update()
            
            for ball in balls:
                ball.update()
                
                if ball.active:
                    # 패들 충돌
                    if (ball.y + BALL_R >= paddle.rect.y and 
                        ball.y - BALL_R <= paddle.rect.bottom and
                        paddle.rect.left <= ball.x <= paddle.rect.right):
                        hit_pos = (ball.x - paddle.rect.x) / paddle.width
                        angle = -60 + hit_pos * 120
                        speed = math.sqrt(ball.dx**2 + ball.dy**2)
                        ball.dx = speed * math.sin(math.radians(angle))
                        ball.dy = -speed * math.cos(math.radians(angle))
                        ball.y = paddle.rect.y - BALL_R
                    
                    # 블록 충돌
                    for brick in bricks:
                        if not brick.alive:
                            continue
                        
                        if (ball.x + BALL_R >= brick.rect.left and 
                            ball.x - BALL_R <= brick.rect.right and
                            ball.y + BALL_R >= brick.rect.top and 
                            ball.y - BALL_R <= brick.rect.bottom):
                            
                            # 블록 파괴시 처리
                            if brick.hit():
                                # 속도 부스트 아이템
                                if brick.type == 'speed':
                                    items.append(Item(brick.rect.centerx, brick.rect.centery))
                                
                                # 공 생성 (ball_count만큼)
                                for _ in range(brick.ball_count):
                                    new_ball = Ball(brick.rect.centerx, brick.rect.centery, settings['speed'])
                                    new_ball.active = True
                                    balls.append(new_ball)
                            
                            # 충돌 방향
                            dx = ball.x - brick.rect.centerx
                            dy = ball.y - brick.rect.centery
                            
                            if abs(dx / (brick.rect.width/2)) > abs(dy / (brick.rect.height/2)):
                                ball.dx = -ball.dx
                                ball.x = brick.rect.right + BALL_R if dx > 0 else brick.rect.left - BALL_R
                            else:
                                ball.dy = -ball.dy
                                ball.y = brick.rect.bottom + BALL_R if dy > 0 else brick.rect.top - BALL_R
                            break
            
            # 아이템 처리 (속도 부스트)
            for item in items[:]:
                if not item.active:
                    items.remove(item)
                    continue
                
                item.update()
                
                if (item.y + 15 >= paddle.rect.y and 
                    item.y - 15 <= paddle.rect.bottom and
                    item.x >= paddle.rect.left and 
                    item.x <= paddle.rect.right):
                    items.remove(item)
                    
                    # 속도 부스트
                    for b in [b for b in balls if b.active]:
                        b.apply_boost(5000)
                    paddle.apply_boost(5000)
            
            # 볼 제거 및 게임 오버
            balls = [b for b in balls if not (b.active and b.y > HEIGHT)]
            
            if game_started and not any(b.active for b in balls):
                game_over = True
                if all(not b.alive for b in bricks):
                    lb = update_leaderboard(GAME_BREAKOUT, int(elapsed), difficulty)
            
            if all(not b.alive for b in bricks) and not game_over:
                game_over = True
                lb = update_leaderboard(GAME_BREAKOUT, int(elapsed), difficulty)
        
        # 그리기
        WINDOW.fill(BG_COLOR)
        pygame.draw.rect(WINDOW, (50, 50, 50), (0, 0, GAME_WIDTH, HEIGHT))
        
        paddle.draw()
        for ball in balls:
            ball.draw()
        for brick in bricks:
            brick.draw()
        for item in items:
            item.draw()
        
        if not any(b.active for b in balls) and not game_over:
            draw_text_centered("Press SPACE to start", HEIGHT//2, 'medium', WHITE)
        
        pygame.draw.rect(WINDOW, OUTLINE_COLOR, (0, 0, GAME_WIDTH, HEIGHT), 3)
        
        # 패널
        pygame.draw.line(WINDOW, OUTLINE_COLOR, (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
        y = 20
        WINDOW.blit(FONTS['small'].render("Difficulty:", True, FONT_COLOR), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(difficulty.upper(), True, FONT_COLOR), (GAME_WIDTH + 10, y + 25))
        y = draw_panel_header("Time:", f"{int(elapsed)}s", y + 60)
        WINDOW.blit(FONTS['small'].render("Balls:", True, FONT_COLOR), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(str(len([b for b in balls if b.active])), True, FONT_COLOR), 
                   (GAME_WIDTH + 10, y + 25))
        y += 50
        draw_panel_separator(y)
        draw_leaderboard(lb, y + 10, True)
        
        if entering_pw:
            draw_password_overlay(pw_input)
        elif game_over:
            draw_game_over(won=all(not b.alive for b in bricks), time=int(elapsed))
        
        pygame.display.update()

# ==================== 메인 ====================
def main():
    current_game = MENU
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        
        if current_game == MENU:
            result = run_menu()
        elif current_game == GAME_2048:
            result = run_2048()
        elif current_game == GAME_BREAKOUT:
            result = run_breakout()
        else:
            break
        
        if result is None:
            break
        current_game = result
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()