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

# 색상 상수
COLORS = {
    'bg': (205, 192, 180), 'outline': (187, 173, 160), 'font': (119, 110, 101),
    'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0),
    'green': (0, 255, 0), 'blue': (135, 206, 250), 'yellow': (255, 255, 0),
    'pink': (255, 182, 193), 'brown': (139, 69, 19), 'dark_gray': (50, 50, 50),
    'purple': (148, 0, 211), 'gold': (255, 215, 0), 'cyan': (0, 255, 255),
    'orange': (255, 165, 0), 'lime': (50, 205, 50)
}

# 게임 상태
MENU, GAME_2048, GAME_BREAKOUT, GAME_TYPING, GAME_TETRIS, GAME_BLOCKBLAST, LEADERBOARD = "menu", "2048", "breakout", "typing", "tetris", "blockblast", "leaderboard"

# 관리자 모드 전역 변수
ADMIN_MODE = False

# ==================== 비밀번호 관리 ====================
class PasswordManager:
    PASSWORD_FILE = "reset_password.txt"
    DEFAULT_PASSWORD = "reset2048"
    
    @staticmethod
    def initialize():
        """초기 비밀번호 파일 확인 및 생성"""
        if not os.path.exists(PasswordManager.PASSWORD_FILE):
            try:
                with open(PasswordManager.PASSWORD_FILE, 'w', encoding='utf-8') as f:
                    f.write(PasswordManager.DEFAULT_PASSWORD)
                print(f"[INFO] 비밀번호 파일 생성됨: {PasswordManager.PASSWORD_FILE}")
                print(f"[INFO] 기본 비밀번호: {PasswordManager.DEFAULT_PASSWORD}")
                return True
            except Exception as e:
                print(f"[ERROR] 비밀번호 파일 생성 실패: {e}")
                return False
        else:
            print(f"[INFO] 비밀번호 파일 존재: {PasswordManager.PASSWORD_FILE}")
            return True
    
    @staticmethod
    def verify(password):
        """비밀번호 검증"""
        try:
            if not os.path.exists(PasswordManager.PASSWORD_FILE):
                PasswordManager.initialize()
                return password == PasswordManager.DEFAULT_PASSWORD
            
            with open(PasswordManager.PASSWORD_FILE, 'r', encoding='utf-8') as f:
                stored = f.read().strip()
            
            if not stored:
                return password == PasswordManager.DEFAULT_PASSWORD
                
            return password == stored
        except Exception as e:
            print(f"[ERROR] 비밀번호 검증 실패: {e}")
            return password == PasswordManager.DEFAULT_PASSWORD
    
    @staticmethod
    def change_password(new_password):
        """비밀번호 변경"""
        try:
            with open(PasswordManager.PASSWORD_FILE, 'w', encoding='utf-8') as f:
                f.write(new_password)
            print(f"[INFO] 비밀번호 변경됨")
            return True
        except Exception as e:
            print(f"[ERROR] 비밀번호 변경 실패: {e}")
            return False

# 초기화
PasswordManager.initialize()

# ==================== 2048 설정 ====================
GRID_SIZE = 4
TILE_SIZE = GAME_WIDTH // GRID_SIZE

TILE_COLORS = {
    0: (205, 193, 180), 2: (237, 229, 218), 4: (238, 225, 201),
    8: (243, 178, 122), 16: (246, 150, 101), 32: (247, 124, 95),
    64: (247, 95, 59), 128: (237, 208, 115), 256: (237, 204, 99),
    512: (236, 202, 80), 1024: (190, 170, 50), 2048: (120, 100, 40)
}

# ==================== 테트리스 설정 ====================
TETRIS_GRID_WIDTH = 10
TETRIS_GRID_HEIGHT = 20
TETRIS_BLOCK_SIZE = 35
TETRIS_OFFSET_X = (GAME_WIDTH - TETRIS_GRID_WIDTH * TETRIS_BLOCK_SIZE) // 2
TETRIS_OFFSET_Y = 20

# 테트리스 블록 모양
TETRIS_SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1], [1, 1]],
    'T': [[0, 1, 0], [1, 1, 1]],
    'S': [[0, 1, 1], [1, 1, 0]],
    'Z': [[1, 1, 0], [0, 1, 1]],
    'J': [[1, 0, 0], [1, 1, 1]],
    'L': [[0, 0, 1], [1, 1, 1]]
}

# 테트리스 블록 색상
TETRIS_COLORS = {
    'I': COLORS['cyan'],
    'O': COLORS['yellow'],
    'T': COLORS['purple'],
    'S': COLORS['green'],
    'Z': COLORS['red'],
    'J': COLORS['blue'],
    'L': COLORS['orange']
}

# ==================== 블록블라스트 설정 ====================
BLOCKBLAST_GRID_SIZE = 8
BLOCKBLAST_CELL_SIZE = 70
BLOCKBLAST_OFFSET_X = (GAME_WIDTH - BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE) // 2
BLOCKBLAST_OFFSET_Y = 50

# 블록블라스트 블록 모양들
BLOCKBLAST_SHAPES = [
    # 1x1
    [[1]],
    # 2x2
    [[1, 1], [1, 1]],
    # 3x3
    [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
    # L자형
    [[1, 0], [1, 0], [1, 1]],
    [[0, 1], [0, 1], [1, 1]],
    [[1, 1], [1, 0], [1, 0]],
    [[1, 1], [0, 1], [0, 1]],
    # 일자형
    [[1, 1, 1]],
    [[1], [1], [1]],
    [[1, 1, 1, 1]],
    [[1], [1], [1], [1]],
    [[1, 1, 1, 1, 1]],
    [[1], [1], [1], [1], [1]],
    # T자형
    [[1, 1, 1], [0, 1, 0]],
    [[0, 1], [1, 1], [0, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 0], [1, 1], [1, 0]],
    # Z자형
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1], [1, 1], [1, 0]],
]

BLOCKBLAST_COLORS = [
    (255, 107, 107), (255, 159, 64), (255, 206, 84),
    (75, 192, 192), (54, 162, 235), (153, 102, 255),
    (255, 99, 132), (255, 159, 243), (201, 203, 207)
]

# ==================== 블록깨기 설정 ====================
PADDLE_CONFIG = {'width': 120, 'height': 20, 'speed': 8}
BALL_CONFIG = {'radius': 8, 'speed': 6}
BRICK_CONFIG = {'cols': 10, 'margin': 1, 'height': 30, 'width': GAME_WIDTH // 10}

BRICK_COLORS = {1: (46, 204, 113), 2: (241, 196, 15), 3: (231, 76, 60)}

DIFFICULTY = {
    'easy': {
        'speed': 6, 'paddle': 120, 'rows': 5,
        'bricks': {'1': 24, '2': 10, '3': 3, 'speed': 3},
        'ball_blocks': 10
    },
    'normal': {
        'speed': 6, 'paddle': 120, 'rows': 6,
        'bricks': {'1': 27, '2': 12, '3': 6, 'speed': 3},
        'ball_blocks': 12
    },
    'hard': {
        'speed': 6, 'paddle': 120, 'rows': 7,
        'bricks': {'1': 27, '2': 15, '3': 11, 'speed': 3},
        'ball_blocks': 14
    }
}

# ==================== 타이핑 게임 설정 ====================
STAGE_CONCEPTS = {
    1: {'name': '과일 농장', 'bg_color': (135, 206, 250), 'ground_color': (144, 238, 144)},
    6: {'name': '동물 왕국', 'bg_color': (255, 218, 185), 'ground_color': (210, 180, 140)},
    11: {'name': '학교 생활', 'bg_color': (176, 196, 222), 'ground_color': (119, 136, 153)},
    16: {'name': '음식 천국', 'bg_color': (255, 239, 213), 'ground_color': (244, 164, 96)},
    21: {'name': '사계절', 'bg_color': (230, 230, 250), 'ground_color': (152, 251, 152)},
    26: {'name': '자연 탐험', 'bg_color': (173, 216, 230), 'ground_color': (60, 179, 113)},
    31: {'name': '우주 탐험', 'bg_color': (25, 25, 112), 'ground_color': (72, 61, 139)},
    36: {'name': '바다 속 세계', 'bg_color': (0, 105, 148), 'ground_color': (0, 139, 139)},
    41: {'name': '직업과 꿈', 'bg_color': (255, 248, 220), 'ground_color': (218, 165, 32)},
    46: {'name': '세계 여행', 'bg_color': (240, 248, 255), 'ground_color': (176, 196, 222)}
}

WORD_POOLS = {
    'fruits': ["사과", "포도", "수박", "딸기", "배", "감", "참외", "복숭아",
               "바나나", "귤", "레몬", "망고", "메론", "자두", "살구", "앵두",
               "양파", "무", "당근", "배추", "상추", "오이", "호박", "고구마",
               "토마토", "감자", "옥수수", "브로콜리", "파프리카", "가지"],
    
    'animals': ["강아지", "고양이", "토끼", "햄스터", "앵무새", "금붕어", "거북이",
                "사자", "호랑이", "코끼리", "기린", "얼룩말", "캥거루", "판다", "펭귄",
                "원숭이", "침팬지", "고릴라", "돌고래", "고래", "물개", "수달",
                "여우", "늑대", "곰", "사슴", "다람쥐", "청설모", "두더지", "너구리"],
    
    'school': ["교실", "칠판", "책상", "의자", "공책", "연필", "지우개", "가방",
               "선생님", "친구", "숙제", "시험", "공부", "수업", "방학", "소풍",
               "운동장", "급식", "도서관", "교과서", "필통", "색연필", "크레파스",
               "미술", "음악", "체육", "과학", "수학", "국어", "영어", "사회"],
    
    'food': ["피자", "치킨", "햄버거", "라면", "떡볶이", "순대", "김밥", "주먹밥",
             "삼겹살", "불고기", "갈비", "비빔밥", "냉면", "짜장면", "짬뽕",
             "김치찌개", "된장찌개", "순두부", "만두", "돈까스", "카레", "스파게티",
             "샌드위치", "핫도그", "타코", "도넛", "케이크", "쿠키", "아이스크림", "초밥"],
    
    'nature': ["봄", "여름", "가을", "겨울", "꽃", "나무", "풀", "산", "바다", "강",
               "하늘", "구름", "해", "달", "별", "비", "눈", "바람", "천둥", "번개",
               "무지개", "새", "나비", "벌", "개미", "매미", "반딧불이", "민들레",
               "장미", "튤립", "해바라기", "코스모스", "벚꽃", "단풍", "은행잎"],
    
    'nature2': ["소나무", "참나무", "버드나무", "대나무", "야자수", "선인장", "이끼",
                "고사리", "토끼풀", "클로버", "수련", "연꽃", "무궁화", "개나리",
                "잠자리", "나방", "메뚜기", "귀뚜라미", "무당벌레", "사마귀", "거미",
                "지렁이", "달팽이", "올챙이", "개구리", "두꺼비", "도롱뇽", "송사리"],
    
    'space': ["지구", "달", "화성", "금성", "목성", "토성", "해왕성", "천왕성",
              "태양", "혜성", "소행성", "은하수", "북두칠성", "별자리", "유성",
              "우주선", "로켓", "인공위성", "우주인", "망원경", "천문대", "블랙홀",
              "은하", "성운", "태양계", "외계인", "우주정거장", "달착륙선", "궤도"],
    
    'ocean': ["상어", "고래", "돌고래", "물개", "바다표범", "해파리", "문어", "오징어",
              "조개", "소라", "전복", "성게", "불가사리", "해마", "가오리", "거북이",
              "산호", "해초", "다시마", "미역", "김", "파래", "말미잘", "갯벌",
              "등대", "선박", "잠수함", "잠수부", "스쿠버", "수족관", "해안", "파도"],
    
    'jobs': ["선생님", "의사", "간호사", "경찰관", "소방관", "요리사", "제빵사", "화가",
             "가수", "배우", "댄서", "운동선수", "축구선수", "야구선수", "작가", "기자",
             "과학자", "연구원", "프로그래머", "디자이너", "건축가", "변호사", "판사",
             "파일럿", "승무원", "우주인", "탐험가", "사진작가", "음악가", "발명가"],
    
    'world': ["서울", "부산", "제주도", "독도", "한라산", "경복궁", "남산타워",
              "도쿄", "오사카", "교토", "후지산", "베이징", "상하이", "만리장성",
              "파리", "런던", "로마", "베를린", "뉴욕", "워싱턴", "샌프란시스코",
              "시드니", "멜버른", "이집트", "피라미드", "타지마할", "그랜드캐년",
              "나이아가라", "에펠탑", "자유의여신상", "콜로세움", "피사의사탑"]
}

STAGE_SCORE_REQUIREMENTS = {
    1: 120, 2: 220, 3: 350, 4: 500, 5: 680,
    6: 880, 7: 1100, 8: 1350, 9: 1630, 10: 1950,
    11: 2150, 12: 2380, 13: 2640, 14: 2930, 15: 3250,
    16: 3600, 17: 3980, 18: 4390, 19: 4830, 20: 5300,
    21: 5800, 22: 6330, 23: 6890, 24: 7480, 25: 8100,
    26: 8750, 27: 9430, 28: 10140, 29: 10880, 30: 11650,
    31: 12450, 32: 13280, 33: 14140, 34: 15030, 35: 15950,
    36: 16900, 37: 17880, 38: 18890, 39: 19930, 40: 21000,
    41: 22100, 42: 23230, 43: 24390, 44: 25580, 45: 26800,
    46: 28050, 47: 29330, 48: 30640, 49: 31980, 50: 33350
}

# ==================== 폰트 초기화 ====================
def init_fonts():
    for name in ["malgun gothic", "맑은 고딕", "nanum gothic", "나눔고딕"]:
        try:
            return {
                'large': pygame.font.SysFont(name, 48, bold=True),
                'medium': pygame.font.SysFont(name, 26, bold=True),
                'small': pygame.font.SysFont(name, 20, bold=True),
                'tiny': pygame.font.SysFont(name, 14, bold=True),
                'huge': pygame.font.SysFont(name, 44, bold=True),
                'title': pygame.font.SysFont(name, 28, bold=True)
            }
        except:
            continue
    return {k: pygame.font.Font(None, v) for k, v in 
            {'large': 48, 'medium': 26, 'small': 20, 'tiny': 14, 'huge': 44, 'title': 28}.items()}

FONTS = init_fonts()
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("게임 모음 - 테트리스 추가!")

# ==================== 리더보드 관리 ====================
class LeaderboardManager:
    _cache = {}
    
    @staticmethod
    def get_filepath(game_type, difficulty=None):
        suffix = f"_{difficulty}" if difficulty and game_type == GAME_BREAKOUT else ""
        return f"leaderboard_{game_type}{suffix}.json"
    
    @staticmethod
    def load(game_type, difficulty=None):
        cache_key = f"{game_type}_{difficulty}"
        if cache_key in LeaderboardManager._cache:
            return LeaderboardManager._cache[cache_key][:]
        
        filepath = LeaderboardManager.get_filepath(game_type, difficulty)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    scores = json.load(f)
                    LeaderboardManager._cache[cache_key] = scores
                    return scores[:]
        except:
            pass
        return []
    
    @staticmethod
    def save(game_type, scores, difficulty=None):
        cache_key = f"{game_type}_{difficulty}"
        LeaderboardManager._cache[cache_key] = scores[:]
        filepath = LeaderboardManager.get_filepath(game_type, difficulty)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(scores, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    @staticmethod
    def update(game_type, score, difficulty=None, stage=None):
        """리더보드 업데이트"""
        if score <= 0:
            return LeaderboardManager.load(game_type, difficulty)
        
        lb = LeaderboardManager.load(game_type, difficulty)
        
        if game_type == GAME_TYPING and stage is not None:
            entry = {'stage': stage, 'score': score}
            lb.append(entry)
            lb = sorted(lb, key=lambda x: (-x['stage'], -x['score']))[:10]
        else:
            lb.append(score)
            lb = sorted(list(set(lb)), reverse=(game_type != GAME_BREAKOUT))[:10]
        
        LeaderboardManager.save(game_type, lb, difficulty)
        return lb
    
    @staticmethod
    def reset(game_type, difficulty=None):
        return LeaderboardManager.save(game_type, [], difficulty)

# ==================== UI 유틸리티 ====================
class UIDrawer:
    @staticmethod
    def button(rect, text, font='medium'):
        pygame.draw.rect(WINDOW, (237, 229, 218), rect, border_radius=10)
        pygame.draw.rect(WINDOW, COLORS['outline'], rect, 3, border_radius=10)
        txt = FONTS[font].render(text, True, COLORS['font'])
        WINDOW.blit(txt, txt.get_rect(center=rect.center))
    
    @staticmethod
    def text_centered(text, y, font='medium', color=None):
        txt = FONTS[font].render(text, True, color or COLORS['font'])
        WINDOW.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
    
    @staticmethod
    def panel_separator(y):
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH + 10, y), (WIDTH - 10, y), 2)
    
    @staticmethod
    def panel_header(label, value, y=20):
        WINDOW.blit(FONTS['small'].render(label, True, COLORS['font']), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(str(value), True, COLORS['font']), (GAME_WIDTH + 10, y + 25))
        return y + 60
    
    @staticmethod
    def leaderboard(scores, y, is_time=False, is_typing=False):
        """리더보드 표시"""
        if is_typing:
            WINDOW.blit(FONTS['medium'].render("최고 기록:", True, COLORS['font']), (GAME_WIDTH + 10, y))
            y += 25
            WINDOW.blit(FONTS['tiny'].render("(단계/점수)", True, COLORS['font']), (GAME_WIDTH + 10, y))
            y += 20
        else:
            title = "최고 기록:" if is_time else "순위표:"
            WINDOW.blit(FONTS['medium'].render(title, True, COLORS['font']), (GAME_WIDTH + 10, y))
            y += 30
        
        WINDOW.blit(FONTS['tiny'].render("F12: 리셋", True, COLORS['font']), (GAME_WIDTH + 10, y))
        y += 18
        WINDOW.blit(FONTS['tiny'].render("ESC: 메뉴", True, COLORS['font']), (GAME_WIDTH + 10, y))
        y += 25
        
        for i, s in enumerate(scores[:6]):
            if is_typing and isinstance(s, dict):
                txt = f"{i+1}. {s['stage']}단계"
                txt2 = f"   {s['score']:,}점"
                WINDOW.blit(FONTS['small'].render(txt, True, COLORS['font']), (GAME_WIDTH + 10, y + i * 45))
                WINDOW.blit(FONTS['tiny'].render(txt2, True, (100, 100, 100)), (GAME_WIDTH + 10, y + i * 45 + 18))
            elif is_time:
                txt = f"{i+1}. {s}초"
                WINDOW.blit(FONTS['small'].render(txt, True, COLORS['font']), (GAME_WIDTH + 10, y + i * 28))
            else:
                txt = f"{i+1}. {s:,}점" if len(f"{s:,}") < 10 else f"{i+1}. {s//1000}k점"
                WINDOW.blit(FONTS['small'].render(txt, True, COLORS['font']), (GAME_WIDTH + 10, y + i * 28))
    
    @staticmethod
    def admin_mode_overlay():
        """관리자 모드 활성화 표시"""
        overlay = pygame.Surface((250, 40))
        overlay.set_alpha(200)
        overlay.fill((255, 100, 100))
        WINDOW.blit(overlay, (WIDTH - 260, 10))
        
        txt = FONTS['small'].render("관리자 모드 ON", True, COLORS['white'])
        WINDOW.blit(txt, (WIDTH - 250, 15))
    
    @staticmethod
    def admin_password_overlay(pw_input):
        """관리자 비밀번호 입력 창"""
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(COLORS['black'])
        WINDOW.blit(overlay, (0, 0))
        
        box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 300, 100)
        pygame.draw.rect(WINDOW, COLORS['white'], box)
        pygame.draw.rect(WINDOW, COLORS['outline'], box, 3)
        
        texts = [
            ("관리자 비밀번호 입력:", 'medium'),
            ("*" * len(pw_input), 'medium'),
            ("ESC: 취소, ENTER: 확인", 'tiny')
        ]
        for i, (text, font) in enumerate(texts):
            surf = FONTS[font].render(text, True, COLORS['font'])
            WINDOW.blit(surf, (WIDTH//2 - surf.get_width()//2, HEIGHT//2 - 40 + i * 30))
    
    @staticmethod
    def password_overlay(pw_input):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(COLORS['black'])
        WINDOW.blit(overlay, (0, 0))
        
        box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 300, 100)
        pygame.draw.rect(WINDOW, COLORS['white'], box)
        pygame.draw.rect(WINDOW, COLORS['outline'], box, 3)
        
        texts = [
            ("리셋 비밀번호 입력:", 'medium'),
            ("*" * len(pw_input), 'medium'),
            ("ESC: 취소, ENTER: 확인", 'tiny')
        ]
        for i, (text, font) in enumerate(texts):
            surf = FONTS[font].render(text, True, COLORS['font'])
            WINDOW.blit(surf, (WIDTH//2 - surf.get_width()//2, HEIGHT//2 - 40 + i * 30))
    
    @staticmethod
    def game_over_screen(won=False, time=None):
        color = COLORS['green'] if won else COLORS['red']
        text = "클리어!" if won else "게임 오버!"
        
        UIDrawer.text_centered(text, HEIGHT//2 - 60, 'large', color)
        if time is not None:
            UIDrawer.text_centered(f"시간: {time}초", HEIGHT//2 - 10, 'medium')
        UIDrawer.text_centered("ESC: 메뉴로", HEIGHT//2 + 30, 'medium')
        if won or (time is None and not won):
            UIDrawer.text_centered("기록이 저장되었습니다!", HEIGHT//2 + 60, 'medium', (0, 150, 0))

# ==================== 메뉴 ====================
def run_menu():
    global ADMIN_MODE
    entering_admin_pw = False
    admin_pw_input = ""
    
    while True:
        WINDOW.fill(COLORS['bg'])
        UIDrawer.text_centered("게임 선택", 40, 'large')
        
        games = [
            (GAME_2048, "1. 2048 게임", pygame.K_1),
            (GAME_BREAKOUT, "2. 블록깨기", pygame.K_2),
            (GAME_TYPING, "3. 케이크던지기", pygame.K_3),
            (GAME_TETRIS, "4. 테트리스", pygame.K_4),
            (GAME_BLOCKBLAST, "5. 블록블라스트", pygame.K_5),
            (LEADERBOARD, "6. 리더보드", pygame.K_6)
        ]
        
        buttons = [pygame.Rect(WIDTH//2 - 200, 110 + i * 70, 400, 60) for i in range(len(games))]
        for btn, (_, name, _) in zip(buttons, games):
            UIDrawer.button(btn, name)
        
        UIDrawer.text_centered("클릭하거나 숫자키를 눌러 선택하세요", 660, 'small')
        
        if ADMIN_MODE:
            UIDrawer.admin_mode_overlay()
        
        if entering_admin_pw:
            UIDrawer.admin_password_overlay(admin_pw_input)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            if event.type == pygame.KEYDOWN:
                if entering_admin_pw:
                    if event.key == pygame.K_ESCAPE:
                        entering_admin_pw = False
                        admin_pw_input = ""
                    elif event.key == pygame.K_RETURN:
                        if PasswordManager.verify(admin_pw_input):
                            ADMIN_MODE = not ADMIN_MODE
                        entering_admin_pw = False
                        admin_pw_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        admin_pw_input = admin_pw_input[:-1]
                    elif event.unicode.isprintable() and len(admin_pw_input) < 20:
                        admin_pw_input += event.unicode
                else:
                    if event.key == pygame.K_F11:
                        entering_admin_pw = True
                    else:
                        for game_type, _, key in games:
                            if event.key == key:
                                return game_type
            
            if event.type == pygame.MOUSEBUTTONDOWN and not entering_admin_pw:
                for i, btn in enumerate(buttons):
                    if btn.collidepoint(pygame.mouse.get_pos()):
                        return games[i][0]

# ==================== 리더보드 화면 ====================
def run_leaderboard():
    """전체 리더보드 화면"""
    while True:
        WINDOW.fill(COLORS['bg'])
        UIDrawer.text_centered("전체 리더보드", 30, 'large')
        
        # 박스 크기 및 위치 (5개로 변경)
        box_width = 190
        box_height = 420
        y_start = 90  # 60에서 90으로 증가
        margin = 8
        total_width = box_width * 5 + margin * 4
        start_x = (WIDTH - total_width) // 2
        
        # 2048 리더보드 (1번째)
        lb_2048 = LeaderboardManager.load(GAME_2048)
        x1 = start_x
        
        box_2048 = pygame.Rect(x1, y_start, box_width, box_height)
        pygame.draw.rect(WINDOW, (230, 220, 200), box_2048, border_radius=15)
        pygame.draw.rect(WINDOW, (237, 229, 218), box_2048.inflate(-16, -16), border_radius=12)
        pygame.draw.rect(WINDOW, COLORS['outline'], box_2048, 4, border_radius=15)
        
        title_2048 = FONTS['medium'].render("2048", True, (100, 80, 60))
        WINDOW.blit(title_2048, (x1 + box_width//2 - title_2048.get_width()//2, y_start + 12))
        pygame.draw.line(WINDOW, COLORS['outline'], (x1 + 15, y_start + 45), (x1 + box_width - 15, y_start + 45), 2)
        
        for i, score in enumerate(lb_2048[:10]):
            txt = f"{i+1}. {score:,}점"
            y_pos = y_start + 58 + i * 38
            WINDOW.blit(FONTS['small'].render(txt, True, COLORS['font']), (x1 + 15, y_pos))
        
        # 블록깨기 리더보드 (2번째)
        x2 = start_x + box_width + margin
        
        box_break = pygame.Rect(x2, y_start, box_width, box_height)
        pygame.draw.rect(WINDOW, (220, 230, 240), box_break, border_radius=15)
        pygame.draw.rect(WINDOW, (237, 242, 247), box_break.inflate(-16, -16), border_radius=12)
        pygame.draw.rect(WINDOW, COLORS['outline'], box_break, 4, border_radius=15)
        
        title_break = FONTS['medium'].render("블록깨기", True, (60, 80, 100))
        WINDOW.blit(title_break, (x2 + box_width//2 - title_break.get_width()//2, y_start + 12))
        pygame.draw.line(WINDOW, COLORS['outline'], (x2 + 15, y_start + 45), (x2 + box_width - 15, y_start + 45), 2)
        
        difficulties_text = ['쉬움', '보통', '어려움']
        difficulty_colors = [(46, 204, 113), (241, 196, 15), (231, 76, 60)]
        
        for j, (diff, diff_name, color) in enumerate(zip(['easy', 'normal', 'hard'], difficulties_text, difficulty_colors)):
            lb_break = LeaderboardManager.load(GAME_BREAKOUT, diff)
            y_diff = y_start + 58 + j * 130
            
            diff_title = FONTS['small'].render(f"[{diff_name}]", True, color)
            WINDOW.blit(diff_title, (x2 + 15, y_diff))
            
            for i, time in enumerate(lb_break[:5]):
                txt = f"{i+1}. {time}초"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x2 + 20, y_diff + 25 + i * 20))
        
        # 케이크던지기 리더보드 (3번째)
        lb_typing = LeaderboardManager.load(GAME_TYPING)
        x3 = start_x + (box_width + margin) * 2
        
        box_typing = pygame.Rect(x3, y_start, box_width, box_height)
        pygame.draw.rect(WINDOW, (240, 220, 230), box_typing, border_radius=15)
        pygame.draw.rect(WINDOW, (247, 237, 242), box_typing.inflate(-16, -16), border_radius=12)
        pygame.draw.rect(WINDOW, COLORS['outline'], box_typing, 4, border_radius=15)
        
        title_typing = FONTS['medium'].render("케이크", True, (100, 60, 80))
        WINDOW.blit(title_typing, (x3 + box_width//2 - title_typing.get_width()//2, y_start + 12))
        pygame.draw.line(WINDOW, COLORS['outline'], (x3 + 15, y_start + 45), (x3 + box_width - 15, y_start + 45), 2)
        
        for i, entry in enumerate(lb_typing[:10]):
            y_pos = y_start + 58 + i * 38
            if isinstance(entry, dict):
                stage_txt = f"{i+1}. {entry['stage']}단계"
                score_txt = f"    {entry['score']:,}"
                WINDOW.blit(FONTS['small'].render(stage_txt, True, COLORS['font']), (x3 + 15, y_pos))
                WINDOW.blit(FONTS['tiny'].render(score_txt, True, (100, 100, 100)), (x3 + 15, y_pos + 18))
            else:
                txt = f"{i+1}. {entry:,}"
                WINDOW.blit(FONTS['small'].render(txt, True, COLORS['font']), (x3 + 15, y_pos))
        
        # 테트리스 리더보드 (4번째)
        lb_tetris = LeaderboardManager.load(GAME_TETRIS)
        x4 = start_x + (box_width + margin) * 3
        
        box_tetris = pygame.Rect(x4, y_start, box_width, box_height)
        pygame.draw.rect(WINDOW, (210, 240, 230), box_tetris, border_radius=15)
        pygame.draw.rect(WINDOW, (230, 247, 237), box_tetris.inflate(-16, -16), border_radius=12)
        pygame.draw.rect(WINDOW, COLORS['outline'], box_tetris, 4, border_radius=15)
        
        title_tetris = FONTS['small'].render("테트리스", True, (40, 100, 80))
        WINDOW.blit(title_tetris, (x4 + box_width//2 - title_tetris.get_width()//2, y_start + 12))
        pygame.draw.line(WINDOW, COLORS['outline'], (x4 + 15, y_start + 40), (x4 + box_width - 15, y_start + 40), 2)
        
        for i, score in enumerate(lb_tetris[:10]):
            txt = f"{i+1}. {score:,}점"
            y_pos = y_start + 53 + i * 37
            WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x4 + 15, y_pos))
        
        # 블록블라스트 리더보드 (5번째)
        lb_blast = LeaderboardManager.load(GAME_BLOCKBLAST)
        x5 = start_x + (box_width + margin) * 4
        
        box_blast = pygame.Rect(x5, y_start, box_width, box_height)
        pygame.draw.rect(WINDOW, (240, 230, 220), box_blast, border_radius=15)
        pygame.draw.rect(WINDOW, (247, 240, 230), box_blast.inflate(-16, -16), border_radius=12)
        pygame.draw.rect(WINDOW, COLORS['outline'], box_blast, 4, border_radius=15)
        
        title_blast = FONTS['small'].render("블록블라스트", True, (100, 80, 60))
        WINDOW.blit(title_blast, (x5 + box_width//2 - title_blast.get_width()//2, y_start + 12))
        pygame.draw.line(WINDOW, COLORS['outline'], (x5 + 15, y_start + 40), (x5 + box_width - 15, y_start + 40), 2)
        
        for i, score in enumerate(lb_blast[:10]):
            txt = f"{i+1}. {score:,}점"
            y_pos = y_start + 53 + i * 37
            WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x5 + 15, y_pos))
        
        UIDrawer.text_centered("ESC: 메뉴로 돌아가기", 750, 'medium')
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return MENU

# ==================== 2048 게임 ====================
class Game2048:
    def __init__(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.entering_pw = False
        self.pw_input = ""
        self.leaderboard = LeaderboardManager.load(GAME_2048)
        
        for _ in range(2):
            self.add_tile()
    
    def add_tile(self):
        empties = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if not self.grid[r][c]]
        if empties:
            r, c = random.choice(empties)
            self.grid[r][c] = 2
    
    def compress_merge(self, line):
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
        return merged + [0] * (GRID_SIZE - len(merged)), gained
    
    def move(self, direction):
        moved, total_gained = False, 0
        new_grid = [row[:] for row in self.grid]
        
        if direction in ('left', 'right'):
            for r in range(GRID_SIZE):
                row = self.grid[r][::-1] if direction == 'right' else self.grid[r][:]
                compressed, gained = self.compress_merge(row)
                new_grid[r] = compressed[::-1] if direction == 'right' else compressed
                if new_grid[r] != self.grid[r]:
                    moved = True
                total_gained += gained
        else:
            for c in range(GRID_SIZE):
                col = [self.grid[r][c] for r in range(GRID_SIZE)]
                if direction == 'down':
                    col = col[::-1]
                compressed, gained = self.compress_merge(col)
                if direction == 'down':
                    compressed = compressed[::-1]
                for r in range(GRID_SIZE):
                    new_grid[r][c] = compressed[r]
                if [new_grid[r][c] for r in range(GRID_SIZE)] != [self.grid[r][c] for r in range(GRID_SIZE)]:
                    moved = True
                total_gained += gained
        
        if moved:
            self.grid = new_grid
            self.score += total_gained
            self.add_tile()
            
            if not self.can_move():
                self.game_over = True
                self.leaderboard = LeaderboardManager.update(GAME_2048, self.score)
        
        return moved
    
    def can_move(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if not self.grid[r][c]:
                    return True
                if c < GRID_SIZE-1 and self.grid[r][c] == self.grid[r][c+1]:
                    return True
                if r < GRID_SIZE-1 and self.grid[r][c] == self.grid[r+1][c]:
                    return True
        return False
    
    def draw(self):
        WINDOW.fill(COLORS['bg'])
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = self.grid[r][c]
                color = TILE_COLORS.get(val, (100, 80, 40))
                rect = pygame.Rect(c * TILE_SIZE + 10, r * TILE_SIZE + 10, 
                                 TILE_SIZE - 20, TILE_SIZE - 20)
                pygame.draw.rect(WINDOW, color, rect, border_radius=8)
                
                if val:
                    txt = FONTS['large'].render(str(val), True, COLORS['font'])
                    WINDOW.blit(txt, txt.get_rect(center=rect.center))
        
        pygame.draw.rect(WINDOW, COLORS['outline'], (0, 0, GAME_WIDTH, HEIGHT), 8, border_radius=8)
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
        
        if ADMIN_MODE:
            UIDrawer.admin_mode_overlay()
        
        y = UIDrawer.panel_header("점수:", self.score)
        UIDrawer.panel_separator(y)
        UIDrawer.leaderboard(self.leaderboard, y + 10)
        
        if self.entering_pw:
            UIDrawer.password_overlay(self.pw_input)
        elif self.game_over:
            UIDrawer.game_over_screen()
        
        pygame.display.update()
    
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return GAME_2048
        
        if self.entering_pw:
            if event.key == pygame.K_ESCAPE:
                self.entering_pw = False
                self.pw_input = ""
            elif event.key == pygame.K_RETURN:
                if PasswordManager.verify(self.pw_input):
                    LeaderboardManager.reset(GAME_2048)
                    self.leaderboard = LeaderboardManager.load(GAME_2048)
                self.entering_pw = False
                self.pw_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.pw_input = self.pw_input[:-1]
            elif event.unicode.isprintable() and len(self.pw_input) < 20:
                self.pw_input += event.unicode
        else:
            if event.key == pygame.K_ESCAPE:
                return MENU
            elif event.key == pygame.K_F12 and not self.game_over:
                self.entering_pw = True
            else:
                dirs = {pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right',
                       pygame.K_UP: 'up', pygame.K_DOWN: 'down'}
                if event.key in dirs and not self.game_over:
                    self.move(dirs[event.key])
        
        return GAME_2048

def run_2048():
    game = Game2048()
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            result = game.handle_event(event)
            if result != GAME_2048:
                return result
        game.draw()

# ==================== 테트리스 게임 ====================
class TetrisBlock:
    def __init__(self, shape_name):
        self.shape_name = shape_name
        self.shape = [row[:] for row in TETRIS_SHAPES[shape_name]]
        self.color = TETRIS_COLORS[shape_name]
        self.x = TETRIS_GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
        
    def rotate(self):
        """블록 회전"""
        self.shape = list(zip(*self.shape[::-1]))
        self.shape = [list(row) for row in self.shape]

class Tetris:
    def __init__(self):
        self.grid = [[0] * TETRIS_GRID_WIDTH for _ in range(TETRIS_GRID_HEIGHT)]
        self.bag = []  # 7bag 시스템
        self.current_block = self.new_block()
        self.next_block = self.new_block()
        self.hold_block = None  # 홀드 블록
        self.can_hold = True  # 이번 턴에 홀드 가능 여부
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.entering_pw = False
        self.pw_input = ""
        self.leaderboard = LeaderboardManager.load(GAME_TETRIS)
        
        self.fall_time = 0
        self.fall_speed = 1000  # 초기 낙하 속도 (1초) - 500에서 1000으로 증가
        self.game_start_time = pygame.time.get_ticks()  # 게임 시작 시간
        
        # 테트리오 점수 시스템
        self.combo = -1  # 콤보 카운터 (-1은 콤보 없음)
        self.back_to_back = False  # Back-to-Back 활성화
        self.last_clear_difficult = False  # 마지막 클리어가 어려운 클리어였는지 (4줄)
        
        # 키 반복 입력 관련
        self.key_timers = {
            'left': 0,
            'right': 0,
            'down': 0
        }
        self.key_pressed = {
            'left': False,
            'right': False,
            'down': False
        }
        self.initial_delay = 170  # 초기 지연 (밀리초)
        self.repeat_rate = 50  # 반복 속도 (밀리초)
        
    def new_block(self):
        """7bag 시스템으로 새로운 블록 생성"""
        if not self.bag:
            # 가방이 비면 7개의 블록을 섞어서 채움
            self.bag = list(TETRIS_SHAPES.keys())
            random.shuffle(self.bag)
        
        shape_name = self.bag.pop(0)
        return TetrisBlock(shape_name)
    
    def valid_position(self, block=None, offset_x=0, offset_y=0):
        """블록 위치가 유효한지 확인"""
        if block is None:
            block = self.current_block
            
        for y, row in enumerate(block.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = block.x + x + offset_x
                    new_y = block.y + y + offset_y
                    
                    if new_x < 0 or new_x >= TETRIS_GRID_WIDTH:
                        return False
                    if new_y >= TETRIS_GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True
    
    def lock_block(self):
        """현재 블록을 그리드에 고정"""
        for y, row in enumerate(self.current_block.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = self.current_block.y + y
                    grid_x = self.current_block.x + x
                    if 0 <= grid_y < TETRIS_GRID_HEIGHT:
                        self.grid[grid_y][grid_x] = self.current_block.color
        
        # 줄 제거 확인
        lines = self.clear_lines()
        
        if lines > 0:
            self.lines_cleared += lines
            
            # 테트리오 점수 계산
            base_scores = {1: 100, 2: 300, 3: 500, 4: 800}
            points = base_scores.get(lines, 0)
            
            # 4줄 클리어는 어려운 클리어
            is_difficult = (lines == 4)
            
            # Back-to-Back 보너스 (이전에도 어려운 클리어를 했고 지금도 어려운 클리어일 때)
            if is_difficult and self.back_to_back:
                points = int(points * 1.5)  # 1.5배 보너스
            
            # Combo 보너스
            if lines > 0:
                self.combo += 1
                if self.combo > 0:
                    combo_bonus = 50 * self.combo  # 콤보당 50점
                    points += combo_bonus
            
            self.score += points
            
            # Back-to-Back 상태 업데이트
            if is_difficult:
                self.back_to_back = True
            elif lines > 0:
                self.back_to_back = False
            
            # 레벨업 (10줄마다)
            self.level = self.lines_cleared // 10 + 1
        else:
            # 줄을 제거하지 못하면 콤보 리셋
            self.combo = -1
        
        # 다음 블록
        self.current_block = self.next_block
        self.next_block = self.new_block()
        self.can_hold = True  # 새 블록이 나오면 다시 홀드 가능
        
        # 게임 오버 확인
        if not self.valid_position():
            self.game_over = True
            self.leaderboard = LeaderboardManager.update(GAME_TETRIS, self.score)
    
    def clear_lines(self):
        """완성된 줄 제거"""
        lines_to_clear = []
        for y in range(TETRIS_GRID_HEIGHT):
            if all(self.grid[y]):
                lines_to_clear.append(y)
        
        for y in lines_to_clear:
            del self.grid[y]
            self.grid.insert(0, [0] * TETRIS_GRID_WIDTH)
        
        return len(lines_to_clear)
    
    def move(self, dx, dy):
        """블록 이동"""
        if self.valid_position(offset_x=dx, offset_y=dy):
            self.current_block.x += dx
            self.current_block.y += dy
            return True
        return False
    
    def rotate_block(self, clockwise=True):
        """블록 회전 (시계방향 또는 반시계방향)"""
        original_shape = [row[:] for row in self.current_block.shape]
        
        if clockwise:
            # 시계방향: 90도
            self.current_block.rotate()
        else:
            # 반시계방향: 270도 (시계방향 3번)
            for _ in range(3):
                self.current_block.rotate()
        
        # 회전 후 위치가 유효하지 않으면 원래대로
        if not self.valid_position():
            # 벽 킥 시도 (좌우로 1칸씩)
            for offset in [1, -1, 2, -2]:
                if self.valid_position(offset_x=offset):
                    self.current_block.x += offset
                    return
            # 벽 킥 실패시 원래 모양으로
            self.current_block.shape = original_shape
    
    def rotate_180(self):
        """180도 회전"""
        original_shape = [row[:] for row in self.current_block.shape]
        
        # 180도 회전 (90도 2번)
        for _ in range(2):
            self.current_block.rotate()
        
        # 회전 후 위치가 유효하지 않으면 원래대로
        if not self.valid_position():
            # 벽 킥 시도
            for offset in [1, -1, 2, -2]:
                if self.valid_position(offset_x=offset):
                    self.current_block.x += offset
                    return
            self.current_block.shape = original_shape
    
    def hold_piece(self):
        """현재 블록을 홀드"""
        if not self.can_hold:
            return
        
        self.can_hold = False
        
        if self.hold_block is None:
            # 처음 홀드하는 경우
            self.hold_block = self.current_block.shape_name
            self.current_block = self.next_block
            self.next_block = self.new_block()
        else:
            # 이미 홀드된 블록이 있는 경우 교환
            temp = self.hold_block
            self.hold_block = self.current_block.shape_name
            self.current_block = TetrisBlock(temp)
            
        # 위치 초기화
        if not self.valid_position():
            self.game_over = True
            self.leaderboard = LeaderboardManager.update(GAME_TETRIS, self.score)
    
    def hard_drop(self):
        """하드 드롭 (한번에 떨어뜨리기)"""
        while self.move(0, 1):
            self.score += 2  # 하드 드롭 보너스
        self.lock_block()
    
    def soft_drop(self):
        """소프트 드롭 (빠르게 떨어뜨리기)"""
        if self.move(0, 1):
            self.score += 1
            return True
        return False
    
    def update(self, dt):
        """게임 업데이트"""
        if self.game_over:
            return
        
        # 시간에 따른 낙하 속도 증가 (2분마다 10% 빠르게, 최소 200ms)
        elapsed_seconds = (pygame.time.get_ticks() - self.game_start_time) / 1000
        speed_multiplier = max(0.2, 1.0 - (elapsed_seconds / 120) * 0.1)  # 2분(120초)마다 10% 감소
        current_fall_speed = max(200, int(1000 * speed_multiplier))
        
        # 자동 낙하
        self.fall_time += dt
        if self.fall_time >= current_fall_speed:
            self.fall_time = 0
            if not self.move(0, 1):
                self.lock_block()
        
        # 키 반복 입력 처리
        keys = pygame.key.get_pressed()
        
        # 좌우 이동
        if keys[pygame.K_LEFT] or keys[pygame.K_KP4]:
            if not self.key_pressed['left']:
                self.move(-1, 0)
                self.key_pressed['left'] = True
                self.key_timers['left'] = 0
            else:
                self.key_timers['left'] += dt
                if self.key_timers['left'] >= self.initial_delay:
                    # 초기 지연 후 반복
                    if (self.key_timers['left'] - self.initial_delay) % self.repeat_rate < dt:
                        self.move(-1, 0)
        else:
            self.key_pressed['left'] = False
            self.key_timers['left'] = 0
        
        if keys[pygame.K_RIGHT] or keys[pygame.K_KP6]:
            if not self.key_pressed['right']:
                self.move(1, 0)
                self.key_pressed['right'] = True
                self.key_timers['right'] = 0
            else:
                self.key_timers['right'] += dt
                if self.key_timers['right'] >= self.initial_delay:
                    # 초기 지연 후 반복
                    if (self.key_timers['right'] - self.initial_delay) % self.repeat_rate < dt:
                        self.move(1, 0)
        else:
            self.key_pressed['right'] = False
            self.key_timers['right'] = 0
        
        # 소프트 드롭
        if keys[pygame.K_DOWN] or keys[pygame.K_KP2]:
            if not self.key_pressed['down']:
                self.soft_drop()
                self.key_pressed['down'] = True
                self.key_timers['down'] = 0
            else:
                self.key_timers['down'] += dt
                if self.key_timers['down'] >= 50:  # 소프트 드롭은 더 빠르게
                    if (self.key_timers['down'] - 50) % 30 < dt:
                        self.soft_drop()
        else:
            self.key_pressed['down'] = False
            self.key_timers['down'] = 0
    
    def draw(self):
        """게임 화면 그리기"""
        WINDOW.fill(COLORS['bg'])
        
        # 그리드 배경
        grid_rect = pygame.Rect(TETRIS_OFFSET_X, TETRIS_OFFSET_Y,
                               TETRIS_GRID_WIDTH * TETRIS_BLOCK_SIZE,
                               TETRIS_GRID_HEIGHT * TETRIS_BLOCK_SIZE)
        pygame.draw.rect(WINDOW, (40, 40, 40), grid_rect)
        
        # 그리드 선
        for x in range(TETRIS_GRID_WIDTH + 1):
            pygame.draw.line(WINDOW, (60, 60, 60),
                           (TETRIS_OFFSET_X + x * TETRIS_BLOCK_SIZE, TETRIS_OFFSET_Y),
                           (TETRIS_OFFSET_X + x * TETRIS_BLOCK_SIZE, 
                            TETRIS_OFFSET_Y + TETRIS_GRID_HEIGHT * TETRIS_BLOCK_SIZE))
        for y in range(TETRIS_GRID_HEIGHT + 1):
            pygame.draw.line(WINDOW, (60, 60, 60),
                           (TETRIS_OFFSET_X, TETRIS_OFFSET_Y + y * TETRIS_BLOCK_SIZE),
                           (TETRIS_OFFSET_X + TETRIS_GRID_WIDTH * TETRIS_BLOCK_SIZE,
                            TETRIS_OFFSET_Y + y * TETRIS_BLOCK_SIZE))
        
        # 고정된 블록들
        for y in range(TETRIS_GRID_HEIGHT):
            for x in range(TETRIS_GRID_WIDTH):
                if self.grid[y][x]:
                    rect = pygame.Rect(
                        TETRIS_OFFSET_X + x * TETRIS_BLOCK_SIZE + 1,
                        TETRIS_OFFSET_Y + y * TETRIS_BLOCK_SIZE + 1,
                        TETRIS_BLOCK_SIZE - 2,
                        TETRIS_BLOCK_SIZE - 2
                    )
                    pygame.draw.rect(WINDOW, self.grid[y][x], rect)
                    pygame.draw.rect(WINDOW, COLORS['white'], rect, 2)
        
        # 현재 블록
        if not self.game_over:
            for y, row in enumerate(self.current_block.shape):
                for x, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            TETRIS_OFFSET_X + (self.current_block.x + x) * TETRIS_BLOCK_SIZE + 1,
                            TETRIS_OFFSET_Y + (self.current_block.y + y) * TETRIS_BLOCK_SIZE + 1,
                            TETRIS_BLOCK_SIZE - 2,
                            TETRIS_BLOCK_SIZE - 2
                        )
                        pygame.draw.rect(WINDOW, self.current_block.color, rect)
                        pygame.draw.rect(WINDOW, COLORS['white'], rect, 2)
        
        # 테두리
        pygame.draw.rect(WINDOW, COLORS['outline'], grid_rect, 4)
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
        
        # 관리자 모드 표시
        if ADMIN_MODE:
            UIDrawer.admin_mode_overlay()
        
        # 우측 패널
        y = UIDrawer.panel_header("점수:", self.score)
        WINDOW.blit(FONTS['small'].render("레벨:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(str(self.level), True, COLORS['font']), (GAME_WIDTH + 10, y + 25))
        y += 50
        WINDOW.blit(FONTS['small'].render("라인:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(str(self.lines_cleared), True, COLORS['font']), (GAME_WIDTH + 10, y + 25))
        y += 50
        
        # 콤보와 B2B 표시
        if self.combo >= 0:
            WINDOW.blit(FONTS['small'].render("콤보:", True, COLORS['yellow']), (GAME_WIDTH + 10, y))
            WINDOW.blit(FONTS['small'].render(f"{self.combo + 1}", True, COLORS['yellow']), (GAME_WIDTH + 10, y + 25))
            y += 50
        
        if self.back_to_back:
            WINDOW.blit(FONTS['small'].render("B2B!", True, COLORS['gold']), (GAME_WIDTH + 10, y))
            y += 35
        
        # 홀드 블록 표시
        WINDOW.blit(FONTS['small'].render("홀드:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        y += 30
        
        if self.hold_block:
            hold_shape = TETRIS_SHAPES[self.hold_block]
            hold_color = TETRIS_COLORS[self.hold_block]
            preview_size = 20
            
            for py, row in enumerate(hold_shape):
                for px, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            GAME_WIDTH + 30 + px * preview_size,
                            y + py * preview_size,
                            preview_size - 2,
                            preview_size - 2
                        )
                        # 홀드 불가능할 때는 회색으로 표시
                        color = hold_color if self.can_hold else (100, 100, 100)
                        pygame.draw.rect(WINDOW, color, rect)
                        pygame.draw.rect(WINDOW, COLORS['white'], rect, 1)
            
            y += len(hold_shape) * preview_size + 20
        else:
            y += 60
        
        UIDrawer.panel_separator(y)
        y += 10
        
        # 다음 블록 미리보기
        WINDOW.blit(FONTS['small'].render("다음:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        y += 30
        
        preview_size = 20
        for py, row in enumerate(self.next_block.shape):
            for px, cell in enumerate(row):
                if cell:
                    rect = pygame.Rect(
                        GAME_WIDTH + 30 + px * preview_size,
                        y + py * preview_size,
                        preview_size - 2,
                        preview_size - 2
                    )
                    pygame.draw.rect(WINDOW, self.next_block.color, rect)
                    pygame.draw.rect(WINDOW, COLORS['white'], rect, 1)
        
        y += len(self.next_block.shape) * preview_size + 20
        UIDrawer.panel_separator(y)
        
        # 조작법
        y += 10
        controls = [
            "← →: 이동",
            "↑ X: 회전(시계)",
            "Ctrl Z: 회전(반시계)",
            "A: 180도 회전",
            "↓: 소프트 드롭",
            "Space: 하드 드롭",
            "Shift C: 홀드"
        ]
        for i, text in enumerate(controls):
            WINDOW.blit(FONTS['tiny'].render(text, True, COLORS['font']), 
                       (GAME_WIDTH + 10, y + i * 16))
        
        y += len(controls) * 16 + 10
        UIDrawer.panel_separator(y)
        UIDrawer.leaderboard(self.leaderboard, y + 10)
        
        # 오버레이
        if self.entering_pw:
            UIDrawer.password_overlay(self.pw_input)
        elif self.game_over:
            UIDrawer.game_over_screen()
        
        pygame.display.update()
    
    def handle_event(self, event):
        """이벤트 처리"""
        if event.type != pygame.KEYDOWN:
            return GAME_TETRIS
        
        if self.entering_pw:
            if event.key == pygame.K_ESCAPE:
                self.entering_pw = False
                self.pw_input = ""
            elif event.key == pygame.K_RETURN:
                if PasswordManager.verify(self.pw_input):
                    LeaderboardManager.reset(GAME_TETRIS)
                    self.leaderboard = LeaderboardManager.load(GAME_TETRIS)
                self.entering_pw = False
                self.pw_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.pw_input = self.pw_input[:-1]
            elif event.unicode.isprintable() and len(self.pw_input) < 20:
                self.pw_input += event.unicode
        else:
            if event.key == pygame.K_ESCAPE:
                return MENU
            elif event.key == pygame.K_F12 and not self.game_over:
                self.entering_pw = True
            elif not self.game_over:
                # 좌우하 방향키는 update()에서 처리하므로 제외
                
                # 하드 드롭 (SPACE, NUMPAD8)
                if event.key in [pygame.K_SPACE, pygame.K_KP8]:
                    self.hard_drop()
                
                # 시계방향 회전 (UP, X, NUMPAD1, NUMPAD5, NUMPAD9)
                elif event.key in [pygame.K_UP, pygame.K_x, pygame.K_KP1, pygame.K_KP5, pygame.K_KP9]:
                    self.rotate_block(clockwise=True)
                
                # 반시계방향 회전 (CTRL, Z, NUMPAD3, NUMPAD7)
                elif event.key in [pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_z, pygame.K_KP3, pygame.K_KP7]:
                    self.rotate_block(clockwise=False)
                
                # 180도 회전 (A)
                elif event.key == pygame.K_a:
                    self.rotate_180()
                
                # 홀드 (SHIFT, C, NUMPAD0)
                elif event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_c, pygame.K_KP0]:
                    self.hold_piece()
        
        return GAME_TETRIS

def run_tetris():
    """테트리스 게임 실행"""
    game = Tetris()
    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            result = game.handle_event(event)
            if result != GAME_TETRIS:
                return result
        
        game.update(dt)
        game.draw()

# ==================== 블록깨기 ====================
class GameObject:
    def __init__(self, x, y):
        self.x, self.y, self.active = x, y, True

class Paddle(GameObject):
    def __init__(self, width=PADDLE_CONFIG['width']):
        super().__init__(GAME_WIDTH//2, HEIGHT - 60)
        self.width, self.height = width, PADDLE_CONFIG['height']
        self.base_width = width  # 기본 너비 저장
        self.rect = pygame.Rect(self.x - width//2, self.y, width, self.height)
        self.speed = PADDLE_CONFIG['speed']
        self.boost = False
        self.boost_end = 0
        self.expanded = False  # 확장 상태
        self.expand_end = 0  # 확장 종료 시간
    
    def update(self):
        if self.boost and pygame.time.get_ticks() >= self.boost_end:
            self.boost = False
            self.speed = PADDLE_CONFIG['speed']
        
        if self.expanded and pygame.time.get_ticks() >= self.expand_end:
            self.expanded = False
            # 원래 너비로 복귀
            old_center = self.rect.centerx
            self.width = self.base_width
            self.rect = pygame.Rect(old_center - self.width//2, self.y, self.width, self.height)
    
    def move(self, dx):
        self.rect.x = max(0, min(GAME_WIDTH - self.width, self.rect.x + dx * self.speed))
    
    def apply_boost(self, duration=5000):
        if not self.boost:
            self.boost, self.boost_end = True, pygame.time.get_ticks() + duration
            self.speed = PADDLE_CONFIG['speed'] * 2
    
    def expand(self, duration=10000):
        """패들 확장 (10초)"""
        if not self.expanded:
            self.expanded = True
            self.expand_end = pygame.time.get_ticks() + duration
            old_center = self.rect.centerx
            self.width = int(self.base_width * 1.5)  # 1.5배 확장
            self.rect = pygame.Rect(old_center - self.width//2, self.y, self.width, self.height)
    
    def draw(self):
        if self.expanded:
            color = (255, 150, 50)  # 주황색
        elif self.boost:
            color = (100, 200, 255)  # 하늘색
        else:
            color = (52, 152, 219)  # 파란색
        pygame.draw.rect(WINDOW, color, self.rect, border_radius=5)

class Ball(GameObject):
    def __init__(self, x=None, y=None, speed=BALL_CONFIG['speed'], spawn_down=False):
        super().__init__(x or GAME_WIDTH // 2, y or HEIGHT - 100)
        self.radius, self.base_speed = BALL_CONFIG['radius'], speed
        self.speed, self.boost, self.boost_end = speed, False, 0
        
        angle = random.uniform(-30, 30) if spawn_down else random.uniform(-60, 60)
        self.dx = speed * math.sin(math.radians(angle))
        self.dy = speed * (math.cos(math.radians(angle)) if spawn_down else -math.cos(math.radians(angle)))
        self.active = False
    
    def apply_boost(self, duration=5000):
        if not self.boost:
            self.boost, self.boost_end = True, pygame.time.get_ticks() + duration
            self.dx, self.dy, self.speed = self.dx * 2, self.dy * 2, self.base_speed * 2
    
    def update(self):
        if not self.active:
            return
        
        if self.boost and pygame.time.get_ticks() >= self.boost_end:
            self.boost = False
            self.dx, self.dy, self.speed = self.dx / 2, self.dy / 2, self.base_speed
        
        self.x, self.y = self.x + self.dx, self.y + self.dy
        
        if self.x - self.radius <= 0 or self.x + self.radius >= GAME_WIDTH:
            self.dx = -self.dx
            self.x = max(self.radius, min(GAME_WIDTH - self.radius, self.x))
        if self.y - self.radius <= 0:
            self.dy, self.y = -self.dy, self.radius
    
    def draw(self):
        color = COLORS['yellow'] if self.boost else COLORS['white']
        pygame.draw.circle(WINDOW, color, (int(self.x), int(self.y)), self.radius)

class Brick(GameObject):
    def __init__(self, x, y, brick_type, new_balls_count=0, has_paddle_item=False):
        super().__init__(x, y)
        self.rect = pygame.Rect(x, y, BRICK_CONFIG['width'] - 5, BRICK_CONFIG['height'] - 5)
        self.type, self.new_balls_count = brick_type, new_balls_count
        self.has_paddle_item = has_paddle_item  # 패들 아이템 여부
        
        if brick_type == 'speed':
            self.dur, self.max_dur, self.base_color = 1, 1, BRICK_COLORS[1]
        else:
            self.dur = self.max_dur = int(brick_type)
            self.base_color = BRICK_COLORS[int(brick_type)]
        self.color = self.base_color
    
    def hit(self):
        self.dur -= 1
        if self.dur <= 0:
            self.active = False
            return True
        self.color = tuple(int(c * self.dur / self.max_dur) for c in self.base_color)
        return False
    
    def draw(self):
        if self.active:
            pygame.draw.rect(WINDOW, self.color, self.rect, border_radius=5)
            if self.type in ['1', '2', '3'] and self.dur > 1:
                txt = FONTS['tiny'].render(str(self.dur), True, COLORS['white'])
                WINDOW.blit(txt, txt.get_rect(center=self.rect.center))

class Item(GameObject):
    def update(self):
        self.y += 3
        if self.y > HEIGHT:
            self.active = False
    
    def draw(self):
        if self.active:
            pygame.draw.circle(WINDOW, (50, 150, 255), (int(self.x), int(self.y)), 15)
            pygame.draw.circle(WINDOW, (100, 180, 255), (int(self.x), int(self.y)), 12)
            txt = FONTS['tiny'].render("SPD", True, COLORS['white'])
            WINDOW.blit(txt, (self.x - txt.get_width()//2, self.y - 8))
            txt2 = FONTS['tiny'].render("x2", True, COLORS['white'])
            WINDOW.blit(txt2, (self.x - txt2.get_width()//2, self.y + 1))

class PaddleItem(GameObject):
    def update(self):
        self.y += 3
        if self.y > HEIGHT:
            self.active = False
    
    def draw(self):
        if self.active:
            pygame.draw.circle(WINDOW, (255, 150, 50), (int(self.x), int(self.y)), 15)
            pygame.draw.circle(WINDOW, (255, 180, 100), (int(self.x), int(self.y)), 12)
            txt = FONTS['tiny'].render("PAD", True, COLORS['white'])
            WINDOW.blit(txt, (self.x - txt.get_width()//2, self.y - 8))
            txt2 = FONTS['tiny'].render("+", True, COLORS['white'])
            WINDOW.blit(txt2, (self.x - txt2.get_width()//2, self.y + 1))

def select_difficulty():
    difficulties = [
        ('easy', '쉬움', pygame.K_1),
        ('normal', '보통', pygame.K_2),
        ('hard', '어려움', pygame.K_3)
    ]
    
    while True:
        WINDOW.fill(COLORS['bg'])
        UIDrawer.text_centered("난이도 선택", 100, 'large')
        
        buttons = []
        for i, (_, name, _) in enumerate(difficulties):
            btn = pygame.Rect(WIDTH//2 - 200, 230 + i * 100, 400, 70)
            pygame.draw.rect(WINDOW, (237, 229, 218), btn, border_radius=10)
            pygame.draw.rect(WINDOW, COLORS['outline'], btn, 3, border_radius=10)
            
            txt_diff = FONTS['medium'].render(f"{i+1}. {name}", True, COLORS['font'])
            WINDOW.blit(txt_diff, (WIDTH//2 - txt_diff.get_width()//2, 255 + i * 100))
            buttons.append(btn)
        
        UIDrawer.text_centered("클릭하거나 숫자키(1,2,3)를 눌러 선택", 610, 'small')
        UIDrawer.text_centered("ESC: 메뉴로 돌아가기", 650, 'small')
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(buttons):
                    if btn.collidepoint(pygame.mouse.get_pos()):
                        return difficulties[i][0]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return MENU
                for diff_id, _, key in difficulties:
                    if event.key == key:
                        return diff_id

def create_bricks(settings):
    bricks, rows = [], settings['rows']
    brick_counts = settings['bricks']
    active_cols = BRICK_CONFIG['cols'] - 2 * BRICK_CONFIG['margin']
    total_positions = rows * active_cols
    
    brick_types = []
    for brick_type, count in brick_counts.items():
        brick_types.extend([brick_type] * count)
    
    brick_types.extend(['1'] * (total_positions - len(brick_types)))
    random.shuffle(brick_types)
    
    durability_1_indices = [i for i, t in enumerate(brick_types) if t == '1']
    num_ball_blocks = settings.get('ball_blocks', 10)
    ball_indices = random.sample(durability_1_indices, min(num_ball_blocks, len(durability_1_indices)))
    
    # 패들 아이템을 위한 인덱스 선택 (ball_indices와 겹치지 않도록)
    remaining_1_indices = [i for i in durability_1_indices if i not in ball_indices]
    num_paddle_blocks = min(5, len(remaining_1_indices))  # 5개의 패들 아이템
    paddle_indices = random.sample(remaining_1_indices, num_paddle_blocks) if remaining_1_indices else []
    
    idx = 0
    for row in range(rows):
        for col in range(BRICK_CONFIG['margin'], BRICK_CONFIG['cols'] - BRICK_CONFIG['margin']):
            if idx < len(brick_types):
                new_balls = 1 if idx in ball_indices else 0
                has_paddle_item = idx in paddle_indices
                bricks.append(Brick(col * BRICK_CONFIG['width'] + 2, 
                                  row * BRICK_CONFIG['height'] + 50, 
                                  brick_types[idx], new_balls, has_paddle_item))
                idx += 1
    return bricks

def run_breakout():
    difficulty = select_difficulty()
    if difficulty in [None, MENU]:
        return difficulty
    
    settings = DIFFICULTY[difficulty]
    paddle = Paddle(settings['paddle'])
    balls = [Ball(speed=settings['speed'])]
    bricks = create_bricks(settings)
    items = []
    paddle_items = []  # 패들 아이템 리스트
    
    game_over, game_won, game_started = False, False, False
    entering_pw, pw_input = False, ""
    start_time, elapsed = None, 0
    
    lb = LeaderboardManager.load(GAME_BREAKOUT, difficulty)
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        
        if game_started and not game_over and start_time:
            elapsed = (pygame.time.get_ticks() - start_time) / 1000
        
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
                        entering_pw, pw_input = False, ""
                    elif event.key == pygame.K_RETURN:
                        if PasswordManager.verify(pw_input):
                            LeaderboardManager.reset(GAME_BREAKOUT, difficulty)
                            lb = LeaderboardManager.load(GAME_BREAKOUT, difficulty)
                        entering_pw, pw_input = False, ""
                    elif event.key == pygame.K_BACKSPACE:
                        pw_input = pw_input[:-1]
                    elif event.unicode.isprintable() and len(pw_input) < 20:
                        pw_input += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        return MENU
                    elif event.key == pygame.K_F12 and not game_over:
                        entering_pw = True
                    elif event.key == pygame.K_SPACE and not game_started:
                        for ball in balls:
                            ball.active = True
                        game_started, start_time = True, pygame.time.get_ticks()
        
        if not game_over and not entering_pw and game_started:
            paddle.update()
            
            for ball in balls:
                ball.update()
                
                if ball.active:
                    if (ball.y + ball.radius >= paddle.rect.y and 
                        ball.y - ball.radius <= paddle.rect.bottom and
                        paddle.rect.left <= ball.x <= paddle.rect.right):
                        hit_pos = (ball.x - paddle.rect.x) / paddle.width
                        angle = -60 + hit_pos * 120
                        speed = math.sqrt(ball.dx**2 + ball.dy**2)
                        ball.dx = speed * math.sin(math.radians(angle))
                        ball.dy = -speed * math.cos(math.radians(angle))
                        ball.y = paddle.rect.y - ball.radius
                    
                    for brick in bricks:
                        if not brick.active:
                            continue
                        
                        if (ball.x + ball.radius >= brick.rect.left and 
                            ball.x - ball.radius <= brick.rect.right and
                            ball.y + ball.radius >= brick.rect.top and 
                            ball.y - ball.radius <= brick.rect.bottom):
                            
                            if brick.hit():
                                if brick.type == 'speed':
                                    items.append(Item(brick.rect.centerx, brick.rect.centery))
                                
                                # 패들 아이템 드롭
                                if brick.has_paddle_item:
                                    paddle_items.append(PaddleItem(brick.rect.centerx, brick.rect.centery))
                                
                                for _ in range(brick.new_balls_count):
                                    new_ball = Ball(brick.rect.centerx, brick.rect.centery, settings['speed'], spawn_down=True)
                                    new_ball.active = True
                                    balls.append(new_ball)
                            
                            dx = ball.x - brick.rect.centerx
                            dy = ball.y - brick.rect.centery
                            
                            if abs(dx / (brick.rect.width/2)) > abs(dy / (brick.rect.height/2)):
                                ball.dx = -ball.dx
                                ball.x = brick.rect.right + ball.radius if dx > 0 else brick.rect.left - ball.radius
                            else:
                                ball.dy = -ball.dy
                                ball.y = brick.rect.bottom + ball.radius if dy > 0 else brick.rect.top - ball.radius
                            break
            
            # 속도 아이템 처리
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
                    for b in [b for b in balls if b.active]:
                        b.apply_boost(5000)
                    paddle.apply_boost(5000)
            
            # 패들 아이템 처리
            for paddle_item in paddle_items[:]:
                if not paddle_item.active:
                    paddle_items.remove(paddle_item)
                    continue
                paddle_item.update()
                if (paddle_item.y + 15 >= paddle.rect.y and 
                    paddle_item.y - 15 <= paddle.rect.bottom and
                    paddle_item.x >= paddle.rect.left and 
                    paddle_item.x <= paddle.rect.right):
                    paddle_items.remove(paddle_item)
                    paddle.expand(10000)  # 10초간 확장
            
            balls = [b for b in balls if not (b.active and b.y > HEIGHT)]
            
            if not any(b.active for b in balls):
                game_over, game_won = True, False
            
            if all(not b.active for b in bricks) and not game_over:
                game_over, game_won = True, True
                lb = LeaderboardManager.update(GAME_BREAKOUT, int(elapsed), difficulty)
        
        WINDOW.fill(COLORS['bg'])
        pygame.draw.rect(WINDOW, (50, 50, 50), (0, 0, GAME_WIDTH, HEIGHT))
        
        paddle.draw()
        for obj in balls + bricks + items + paddle_items:
            obj.draw()
        
        if not game_started and not game_over:
            UIDrawer.text_centered("스페이스바를 눌러 시작", HEIGHT//2, 'medium', COLORS['white'])
        
        pygame.draw.rect(WINDOW, COLORS['outline'], (0, 0, GAME_WIDTH, HEIGHT), 3)
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
        
        if ADMIN_MODE:
            UIDrawer.admin_mode_overlay()
        
        y = 20
        WINDOW.blit(FONTS['small'].render("난이도:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(difficulty.upper(), True, COLORS['font']), (GAME_WIDTH + 10, y + 25))
        y = UIDrawer.panel_header("시간:", f"{int(elapsed)}초", y + 60)
        WINDOW.blit(FONTS['small'].render("공:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(str(len([b for b in balls if b.active])), True, COLORS['font']), 
                   (GAME_WIDTH + 10, y + 25))
        y += 50
        UIDrawer.panel_separator(y)
        UIDrawer.leaderboard(lb, y + 10, True)
        
        if entering_pw:
            UIDrawer.password_overlay(pw_input)
        elif game_over:
            UIDrawer.game_over_screen(won=game_won, time=int(elapsed))
        
        pygame.display.update()

# ==================== 타이핑 게임 ====================
class Cake(GameObject):
    def __init__(self, x, y, target_x, target_y, target_robot=None):
        super().__init__(x, y)
        self.target_robot, self.size = target_robot, 12
        dx, dy = target_x - x, target_y - y
        distance = max(1, math.sqrt(dx**2 + dy**2))
        self.speed = 30
        self.vx, self.vy = (dx / distance) * self.speed, (dy / distance) * self.speed
        
    def update(self):
        self.x, self.y = self.x + self.vx, self.y + self.vy
        if self.x < 0 or self.x > GAME_WIDTH or self.y < 0 or self.y > HEIGHT:
            self.active = False
            
    def draw(self):
        if self.active:
            pygame.draw.circle(WINDOW, COLORS['pink'], (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(WINDOW, COLORS['brown'], (int(self.x), int(self.y)), self.size - 3)
            pygame.draw.circle(WINDOW, COLORS['white'], (int(self.x), int(self.y)), 3)

class Robot(GameObject):
    def __init__(self, stage):
        self.stage = stage
        self.is_special = stage >= 6 and random.random() < 0.3
        self.is_fast = stage >= 8 and not self.is_special and random.random() < 0.25
        
        self.speed = 1.0
        self.size = 30
        
        if stage <= 5:
            word_pool = WORD_POOLS['fruits']
        elif stage <= 10:
            word_pool = WORD_POOLS['fruits'] + WORD_POOLS['animals']
        elif stage <= 15:
            word_pool = WORD_POOLS['animals'] + WORD_POOLS['school']
        elif stage <= 20:
            word_pool = WORD_POOLS['school'] + WORD_POOLS['food']
        elif stage <= 25:
            word_pool = WORD_POOLS['food'] + WORD_POOLS['nature']
        elif stage <= 30:
            word_pool = WORD_POOLS['nature'] + WORD_POOLS['nature2']
        elif stage <= 35:
            word_pool = WORD_POOLS['nature2'] + WORD_POOLS['space']
        elif stage <= 40:
            word_pool = WORD_POOLS['space'] + WORD_POOLS['ocean']
        elif stage <= 45:
            word_pool = WORD_POOLS['ocean'] + WORD_POOLS['jobs']
        else:
            word_pool = WORD_POOLS['jobs'] + WORD_POOLS['world']

        self.word = random.choice(word_pool)
        
        if self.is_special:
            self.color, self.hits_required, self.hits_taken = COLORS['red'], 2, 0
            self.original_speed = self.speed
            self.is_transparent = False
        elif self.is_fast:
            self.speed, self.color = self.speed * 1.5, (135, 206, 250)
            self.is_transparent = True
        else:
            self.color = COLORS['black']
            self.is_transparent = False
        
        super().__init__(GAME_WIDTH - 50, random.randint(100, HEIGHT - 150))
        self.hit_cooldown = 0
        
    def update(self):
        if self.active:
            self.x -= self.speed
            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1
                
    def draw(self):
        if not self.active:
            return
        
        rect = pygame.Rect(int(self.x - self.size//2), int(self.y - self.size//2), self.size, self.size)
        
        if self.is_transparent:
            transparent_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            current_color = self.color if self.hit_cooldown == 0 else COLORS['yellow']
            color_with_alpha = current_color + (128,) if len(current_color) == 3 else current_color
            pygame.draw.rect(transparent_surface, color_with_alpha, (0, 0, self.size, self.size))
            
            border_color = COLORS['white']
            pygame.draw.rect(transparent_surface, border_color + (128,), (0, 0, self.size, self.size), 2)
            
            WINDOW.blit(transparent_surface, (int(self.x - self.size//2), int(self.y - self.size//2)))
        else:
            current_color = self.color if self.hit_cooldown == 0 else COLORS['yellow']
            pygame.draw.rect(WINDOW, current_color, rect)
            
            border_width = 4 if self.is_special else 2
            border_color = COLORS['gold'] if self.is_special else COLORS['white']
            pygame.draw.rect(WINDOW, border_color, rect, border_width)
        
        eye_offset = self.size // 4
        for dx in [-eye_offset, eye_offset]:
            pygame.draw.circle(WINDOW, COLORS['white'], 
                             (int(self.x + dx), int(self.y - eye_offset//2)), 5)
            pygame.draw.circle(WINDOW, COLORS['black'], 
                             (int(self.x + dx), int(self.y - eye_offset//2)), 3)
        
        word_surface = FONTS['medium'].render(self.word, True, COLORS['black'])
        word_rect = word_surface.get_rect(center=(self.x, self.y + self.size))
        
        bg_color = (255, 220, 220) if self.is_special else COLORS['white']
        bg_rect = word_rect.inflate(10, 10)
        pygame.draw.rect(WINDOW, bg_color, bg_rect)
        pygame.draw.rect(WINDOW, COLORS['black'], bg_rect, 2)
        WINDOW.blit(word_surface, word_rect)
        
        if self.is_special:
            remaining = self.hits_required - self.hits_taken
            hits_text = FONTS['small'].render(f"x{remaining}", True, COLORS['red'])
            WINDOW.blit(hits_text, hits_text.get_rect(center=(self.x, self.y + self.size + 25)))
    
    def hit(self):
        if self.is_special:
            self.hits_taken += 1
            self.hit_cooldown = 10
            if self.hits_taken == 1:
                self.speed = self.original_speed * 0.75
            if self.hits_taken >= self.hits_required:
                self.active = False
                return True
            return False
        else:
            self.active = False
            return True
    
    def is_off_screen(self):
        return self.x < -50

class Heart(GameObject):
    def __init__(self):
        super().__init__(GAME_WIDTH - 50, random.randint(100, HEIGHT - 150))
        self.word, self.speed = "하트", 2
        
    def update(self):
        if self.active:
            self.x -= self.speed
            
    def draw(self):
        if not self.active:
            return
            
        pygame.draw.circle(WINDOW, COLORS['red'], (int(self.x - 8), int(self.y - 5)), 10)
        pygame.draw.circle(WINDOW, COLORS['red'], (int(self.x + 8), int(self.y - 5)), 10)
        points = [(self.x, self.y + 5), (self.x - 15, self.y - 8), 
                 (self.x, self.y + 15), (self.x + 15, self.y - 8)]
        pygame.draw.polygon(WINDOW, COLORS['red'], points)
        
        word_surface = FONTS['small'].render(self.word, True, COLORS['red'])
        word_rect = word_surface.get_rect(center=(self.x, self.y + 30))
        bg_rect = word_rect.inflate(6, 4)
        pygame.draw.rect(WINDOW, COLORS['white'], bg_rect)
        WINDOW.blit(word_surface, word_rect)
    
    def is_off_screen(self):
        return self.x < -50

class Particle(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx, self.vy = random.uniform(-8, 8), random.uniform(-8, 8)
        self.life = 30
        self.color = random.choice([COLORS['red'], COLORS['yellow'], (255, 128, 0), COLORS['pink']])
        
    def update(self):
        self.x, self.y, self.vy = self.x + self.vx, self.y + self.vy, self.vy + 0.3
        self.life -= 1
        
    def draw(self):
        if self.life > 0:
            size = max(2, self.life // 5)
            pygame.draw.circle(WINDOW, self.color, (int(self.x), int(self.y)), size)

def draw_house():
    house_x, house_y, house_width, house_height = 80, HEIGHT - 200, 120, 100
    
    pygame.draw.rect(WINDOW, (200, 150, 100), (house_x, house_y, house_width, house_height))
    pygame.draw.rect(WINDOW, COLORS['dark_gray'], (house_x, house_y, house_width, house_height), 3)
    
    roof_points = [
        (house_x - 10, house_y),
        (house_x + house_width // 2, house_y - 50),
        (house_x + house_width + 10, house_y)
    ]
    pygame.draw.polygon(WINDOW, COLORS['red'], roof_points)
    pygame.draw.polygon(WINDOW, COLORS['dark_gray'], roof_points, 3)
    
    pygame.draw.rect(WINDOW, (100, 200, 255), (house_x + 20, house_y + 20, 30, 30))
    pygame.draw.rect(WINDOW, COLORS['dark_gray'], (house_x + 20, house_y + 20, 30, 30), 2)
    pygame.draw.rect(WINDOW, COLORS['brown'], (house_x + 70, house_y + 40, 35, 60))
    pygame.draw.rect(WINDOW, COLORS['dark_gray'], (house_x + 70, house_y + 40, 35, 60), 2)
    pygame.draw.circle(WINDOW, COLORS['yellow'], (house_x + 95, house_y + 70), 4)

def run_typing():
    pygame.key.start_text_input()
    
    stage, score, hp, max_hp = 1, 0, 3, 3
    robots, hearts, cakes, particles = [], [], [], []
    spawn_timer, spawn_delay, heart_spawn_timer = 0, 90, 0
    
    target_score = STAGE_SCORE_REQUIREMENTS.get(stage, 33350 + (stage - 50) * 770)
    
    current_input, composing_text = "", ""
    game_over, stage_clear = False, False
    entering_pw, pw_input = False, ""
    start_time, elapsed = pygame.time.get_ticks(), 0
    
    lb = LeaderboardManager.load(GAME_TYPING)
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        
        if not game_over and not stage_clear:
            elapsed = (pygame.time.get_ticks() - start_time) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.key.stop_text_input()
                return None
            
            if event.type == pygame.TEXTINPUT:
                if not game_over and not stage_clear and not entering_pw:
                    if event.text and event.text.strip():
                        current_input += event.text
                    composing_text = ""

            if event.type == pygame.TEXTEDITING:
                if not game_over and not stage_clear and not entering_pw:
                    composing_text = event.text if event.text else ""
            
            if event.type == pygame.KEYDOWN:
                if entering_pw:
                    if event.key == pygame.K_ESCAPE:
                        entering_pw, pw_input = False, ""
                    elif event.key == pygame.K_RETURN:
                        if PasswordManager.verify(pw_input):
                            LeaderboardManager.reset(GAME_TYPING)
                            lb = LeaderboardManager.load(GAME_TYPING)
                        entering_pw, pw_input = False, ""
                    elif event.key == pygame.K_BACKSPACE:
                        pw_input = pw_input[:-1]
                    elif event.unicode.isprintable() and len(pw_input) < 20:
                        pw_input += event.unicode
                elif event.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input()
                    return MENU
                elif event.key == pygame.K_F12 and not game_over and not stage_clear:
                    entering_pw = True
                elif stage_clear and event.key == pygame.K_SPACE:
                    stage += 1
                    robots, hearts, cakes, particles = [], [], [], []
                    target_score = STAGE_SCORE_REQUIREMENTS.get(stage, 33350 + (stage - 50) * 770)
                    spawn_delay = max(60, 90 - stage * 3)
                    stage_clear, hp = False, max_hp
                    current_input, composing_text = "", ""
                    spawn_timer, heart_spawn_timer = 0, 0
                elif not game_over and not stage_clear:
                    if event.key == pygame.K_BACKSPACE:
                        if current_input:
                            current_input = current_input[:-1]
                        composing_text = ""
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if current_input:
                            hit = False
                            
                            for heart in hearts[:]:
                                if current_input == heart.word:
                                    hp = min(hp + 1, max_hp)
                                    hearts.remove(heart)
                                    score += len(heart.word) * 10
                                    hit = True
                                    break
                            
                            if not hit:
                                matching_robots = [r for r in robots if current_input == r.word]
                                if matching_robots:
                                    target_robot = min(matching_robots, key=lambda r: r.x)
                                    cakes.append(Cake(100, HEIGHT - 150, target_robot.x, target_robot.y, target_robot))
                                    score += len(target_robot.word) * 10
                                    hit = True
                            
                            current_input, composing_text = "", ""
                    elif ADMIN_MODE and event.key == pygame.K_2:
                        score = target_score
                        stage_clear = True
        
        if not game_over and not stage_clear and not entering_pw:
            spawn_timer += 1
            if spawn_timer >= spawn_delay and len(robots) < 8:
                robots.append(Robot(stage))
                spawn_timer = 0
            
            heart_spawn_timer += 1
            if heart_spawn_timer >= 1800 and hp < max_hp:
                hearts.append(Heart())
                heart_spawn_timer = 0
            
            for cake in cakes[:]:
                cake.update()
                if not cake.active:
                    cakes.remove(cake)
                    continue
                
                if cake.target_robot and cake.target_robot.active:
                    robot = cake.target_robot
                    distance = math.sqrt((cake.x - robot.x)**2 + (cake.y - robot.y)**2)
                    if distance < robot.size:
                        if robot.hit():
                            for _ in range(20):
                                particles.append(Particle(robot.x, robot.y))
                        cake.active = False
            
            for robot in robots[:]:
                robot.update()
                if robot.is_off_screen() and robot.active:
                    robots.remove(robot)
                    if not ADMIN_MODE:
                        hp -= 1
                elif not robot.active:
                    robots.remove(robot)
            
            for heart in hearts[:]:
                heart.update()
                if heart.is_off_screen():
                    hearts.remove(heart)
            
            particles = [p for p in particles if (p.update() or True) and p.life > 0]
            
            if score >= target_score:
                stage_clear = True
            
            if hp <= 0:
                game_over = True
                lb = LeaderboardManager.update(GAME_TYPING, score, stage=stage)
        
        current_concept = None
        for concept_stage in sorted(STAGE_CONCEPTS.keys(), reverse=True):
            if stage >= concept_stage:
                current_concept = STAGE_CONCEPTS[concept_stage]
                break
        
        if current_concept is None:
            current_concept = STAGE_CONCEPTS[1]
        
        WINDOW.fill(current_concept['bg_color'])
        pygame.draw.rect(WINDOW, current_concept['ground_color'], (0, HEIGHT - 120, GAME_WIDTH, 120))
        draw_house()
        
        for obj in hearts + robots + cakes + particles:
            obj.draw()
        
        stage_text = FONTS['title'].render(f"단계: {stage}", True, COLORS['black'])
        score_text = FONTS['title'].render(f"점수: {score}", True, COLORS['black'])
        if target_score >= 1000:
            progress_text = FONTS['tiny'].render(f"{score}/{target_score}", True, COLORS['black'])
        else:
            progress_text = FONTS['small'].render(f"{score}/{target_score}", True, COLORS['black'])
        
        WINDOW.blit(stage_text, (10, 15))
        WINDOW.blit(score_text, (GAME_WIDTH // 2 - score_text.get_width() // 2, 15))
        WINDOW.blit(FONTS['tiny'].render("목표:", True, COLORS['black']), (GAME_WIDTH - 160, 15))
        WINDOW.blit(progress_text, (GAME_WIDTH - 160, 30))
        
        concept_text = FONTS['tiny'].render(f"테마: {current_concept['name']}", True, COLORS['black'])
        WINDOW.blit(concept_text, (10, 45))
        
        for i in range(max_hp):
            color = COLORS['red'] if i < hp else (100, 100, 100)
            x, y = 10 + i * 40, 75
            pygame.draw.circle(WINDOW, color, (x - 8, y - 5), 10)
            pygame.draw.circle(WINDOW, color, (x + 8, y - 5), 10)
            points = [(x, y + 5), (x - 15, y - 8), (x, y + 15), (x + 15, y - 8)]
            pygame.draw.polygon(WINDOW, color, points)
        
        input_box = pygame.Rect(GAME_WIDTH // 2 - 200, HEIGHT - 80, 400, 50)
        pygame.draw.rect(WINDOW, COLORS['red'], input_box.inflate(10, 10), 5)
        pygame.draw.rect(WINDOW, (200, 255, 200), input_box)
        
        display_text = current_input + composing_text
        if display_text:
            input_text = FONTS['huge'].render(display_text, True, COLORS['black'])
        else:
            input_text = FONTS['small'].render("단어를 입력하세요...", True, (150, 150, 150))
        
        input_rect = input_text.get_rect(midleft=(input_box.x + 15, input_box.centery))
        WINDOW.blit(input_text, input_rect)
        
        if not game_over and not stage_clear:
            if (pygame.time.get_ticks() // 500) % 2:
                pygame.draw.line(WINDOW, COLORS['black'], 
                               (input_rect.right + 5, input_box.y + 10),
                               (input_rect.right + 5, input_box.bottom - 10), 3)
        
        pygame.draw.rect(WINDOW, COLORS['outline'], (0, 0, GAME_WIDTH, HEIGHT), 3)
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
        
        if ADMIN_MODE:
            UIDrawer.admin_mode_overlay()
            cheat_info = ["2키: 스킵", "무적 모드"]
            for i, info in enumerate(cheat_info):
                txt = FONTS['tiny'].render(info, True, COLORS['white'])
                WINDOW.blit(txt, (WIDTH - 250, 50 + i * 15))
        
        y = UIDrawer.panel_header("점수:", score)
        WINDOW.blit(FONTS['small'].render("시간:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(f"{int(elapsed)}초", True, COLORS['font']), (GAME_WIDTH + 10, y + 25))
        y += 50
        UIDrawer.panel_separator(y)
        UIDrawer.leaderboard(lb, y + 10, is_typing=True)
        
        if entering_pw:
            UIDrawer.password_overlay(pw_input)
        elif stage_clear:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(COLORS['black'])
            WINDOW.blit(overlay, (0, 0))
            
            UIDrawer.text_centered("단계 클리어!", HEIGHT // 2 - 60, 'huge', COLORS['yellow'])
            UIDrawer.text_centered(f"다음 단계: {stage + 1}", HEIGHT // 2, 'title', COLORS['white'])
            UIDrawer.text_centered("스페이스바를 눌러 계속", HEIGHT // 2 + 60, 'small', COLORS['white'])
        elif game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(COLORS['black'])
            WINDOW.blit(overlay, (0, 0))
            
            UIDrawer.text_centered("게임 오버!", HEIGHT // 2 - 100, 'huge', COLORS['red'])
            UIDrawer.text_centered(f"점수: {score}", HEIGHT // 2 - 30, 'huge', COLORS['yellow'])
            UIDrawer.text_centered(f"도달 단계: {stage}", HEIGHT // 2 + 20, 'title', COLORS['white'])
            UIDrawer.text_centered(f"생존 시간: {int(elapsed)}초", HEIGHT // 2 + 50, 'small', COLORS['white'])
            UIDrawer.text_centered("ESC: 메뉴로", HEIGHT // 2 + 90, 'small', COLORS['white'])
        
        pygame.display.flip()
    
    pygame.key.stop_text_input()

# ==================== 블록블라스트 ====================
class BlockBlastPiece:
    def __init__(self, shape):
        self.shape = [row[:] for row in shape]
        self.color = random.choice(BLOCKBLAST_COLORS)
        self.width = len(self.shape[0]) if self.shape else 0
        self.height = len(self.shape)
    
    def draw(self, x, y, cell_size, alpha=255):
        """블록 그리기"""
        for row_idx, row in enumerate(self.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    rect = pygame.Rect(
                        x + col_idx * cell_size,
                        y + row_idx * cell_size,
                        cell_size - 2,
                        cell_size - 2
                    )
                    if alpha < 255:
                        surf = pygame.Surface((cell_size - 2, cell_size - 2), pygame.SRCALPHA)
                        color_with_alpha = self.color + (alpha,)
                        pygame.draw.rect(surf, color_with_alpha, (0, 0, cell_size - 2, cell_size - 2), border_radius=5)
                        WINDOW.blit(surf, rect)
                    else:
                        pygame.draw.rect(WINDOW, self.color, rect, border_radius=5)
                    pygame.draw.rect(WINDOW, COLORS['white'], rect, 2, border_radius=5)

class BlockBlast:
    def __init__(self):
        self.grid = [[0] * BLOCKBLAST_GRID_SIZE for _ in range(BLOCKBLAST_GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.entering_pw = False
        self.pw_input = ""
        self.leaderboard = LeaderboardManager.load(GAME_BLOCKBLAST)
        
        # 현재 사용 가능한 3개의 블록
        self.available_pieces = [self.new_piece() for _ in range(3)]
        self.selected_piece_idx = None
        self.dragging = False
        self.mouse_x = 0
        self.mouse_y = 0
        self.drag_offset_x = 0  # 드래그 시작 시 마우스와 블록 중심의 오프셋
        self.drag_offset_y = 0
    
    def new_piece(self):
        """새로운 블록 생성"""
        shape = random.choice(BLOCKBLAST_SHAPES)
        return BlockBlastPiece(shape)
    
    def can_place(self, piece, grid_row, grid_col):
        """블록을 놓을 수 있는지 확인"""
        for row_idx, row in enumerate(piece.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    r = grid_row + row_idx
                    c = grid_col + col_idx
                    if r < 0 or r >= BLOCKBLAST_GRID_SIZE or c < 0 or c >= BLOCKBLAST_GRID_SIZE:
                        return False
                    if self.grid[r][c] != 0:
                        return False
        return True
    
    def place_piece(self, piece, grid_row, grid_col):
        """블록 배치"""
        for row_idx, row in enumerate(piece.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    r = grid_row + row_idx
                    c = grid_col + col_idx
                    self.grid[r][c] = piece.color
        
        # 줄 제거 확인
        self.clear_lines()
    
    def clear_lines(self):
        """완성된 행과 열 제거"""
        cleared_count = 0
        
        # 행 체크
        rows_to_clear = []
        for r in range(BLOCKBLAST_GRID_SIZE):
            if all(self.grid[r][c] != 0 for c in range(BLOCKBLAST_GRID_SIZE)):
                rows_to_clear.append(r)
        
        # 열 체크
        cols_to_clear = []
        for c in range(BLOCKBLAST_GRID_SIZE):
            if all(self.grid[r][c] != 0 for r in range(BLOCKBLAST_GRID_SIZE)):
                cols_to_clear.append(c)
        
        # 행 제거
        for r in rows_to_clear:
            for c in range(BLOCKBLAST_GRID_SIZE):
                self.grid[r][c] = 0
            cleared_count += 1
        
        # 열 제거
        for c in cols_to_clear:
            for r in range(BLOCKBLAST_GRID_SIZE):
                self.grid[r][c] = 0
            cleared_count += 1
        
        # 점수 추가
        if cleared_count > 0:
            self.score += cleared_count * 100
            # 콤보 보너스
            if cleared_count >= 2:
                self.score += (cleared_count - 1) * 50
    
    def check_game_over(self):
        """게임 오버 확인"""
        # 남아있는 블록 중 하나라도 놓을 수 있으면 게임 계속
        for piece in self.available_pieces:
            if piece is None:
                continue
            for r in range(BLOCKBLAST_GRID_SIZE):
                for c in range(BLOCKBLAST_GRID_SIZE):
                    if self.can_place(piece, r, c):
                        return False
        return True
    
    def screen_to_grid(self, x, y, piece=None):
        """화면 좌표를 그리드 좌표로 변환 (블록 중심 기준)"""
        if piece:
            # 블록의 중심을 기준으로 계산
            center_offset_x = (piece.width * BLOCKBLAST_CELL_SIZE) // 2
            center_offset_y = (piece.height * BLOCKBLAST_CELL_SIZE) // 2
            
            grid_col = (x - BLOCKBLAST_OFFSET_X - center_offset_x + BLOCKBLAST_CELL_SIZE // 2) // BLOCKBLAST_CELL_SIZE
            grid_row = (y - BLOCKBLAST_OFFSET_Y - center_offset_y + BLOCKBLAST_CELL_SIZE // 2) // BLOCKBLAST_CELL_SIZE
        else:
            grid_col = (x - BLOCKBLAST_OFFSET_X) // BLOCKBLAST_CELL_SIZE
            grid_row = (y - BLOCKBLAST_OFFSET_Y) // BLOCKBLAST_CELL_SIZE
        
        # 그리드 범위 내에 있는지 확인하지 않고 그냥 반환 (나중에 can_place에서 체크)
        return grid_row, grid_col
    
    def draw(self):
        """게임 화면 그리기"""
        WINDOW.fill(COLORS['bg'])
        
        # 그리드 배경
        grid_rect = pygame.Rect(
            BLOCKBLAST_OFFSET_X,
            BLOCKBLAST_OFFSET_Y,
            BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE,
            BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE
        )
        pygame.draw.rect(WINDOW, (250, 248, 239), grid_rect)
        
        # 그리드 선
        for i in range(BLOCKBLAST_GRID_SIZE + 1):
            # 수평선
            pygame.draw.line(
                WINDOW, (200, 200, 200),
                (BLOCKBLAST_OFFSET_X, BLOCKBLAST_OFFSET_Y + i * BLOCKBLAST_CELL_SIZE),
                (BLOCKBLAST_OFFSET_X + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE,
                 BLOCKBLAST_OFFSET_Y + i * BLOCKBLAST_CELL_SIZE),
                2
            )
            # 수직선
            pygame.draw.line(
                WINDOW, (200, 200, 200),
                (BLOCKBLAST_OFFSET_X + i * BLOCKBLAST_CELL_SIZE, BLOCKBLAST_OFFSET_Y),
                (BLOCKBLAST_OFFSET_X + i * BLOCKBLAST_CELL_SIZE,
                 BLOCKBLAST_OFFSET_Y + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE),
                2
            )
        
        # 배치된 블록들
        for r in range(BLOCKBLAST_GRID_SIZE):
            for c in range(BLOCKBLAST_GRID_SIZE):
                if self.grid[r][c] != 0:
                    rect = pygame.Rect(
                        BLOCKBLAST_OFFSET_X + c * BLOCKBLAST_CELL_SIZE + 1,
                        BLOCKBLAST_OFFSET_Y + r * BLOCKBLAST_CELL_SIZE + 1,
                        BLOCKBLAST_CELL_SIZE - 2,
                        BLOCKBLAST_CELL_SIZE - 2
                    )
                    pygame.draw.rect(WINDOW, self.grid[r][c], rect, border_radius=5)
                    pygame.draw.rect(WINDOW, COLORS['white'], rect, 2, border_radius=5)
        
        # 배치 가능한 위치 하이라이트
        if self.dragging and self.selected_piece_idx is not None:
            piece = self.available_pieces[self.selected_piece_idx]
            if piece:
                grid_row, grid_col = self.screen_to_grid(self.mouse_x, self.mouse_y, piece)
                
                if self.can_place(piece, grid_row, grid_col):
                    # 배치 가능한 위치를 반투명 녹색으로 표시
                    for row_idx, row in enumerate(piece.shape):
                        for col_idx, cell in enumerate(row):
                            if cell:
                                r = grid_row + row_idx
                                c = grid_col + col_idx
                                if 0 <= r < BLOCKBLAST_GRID_SIZE and 0 <= c < BLOCKBLAST_GRID_SIZE:
                                    rect = pygame.Rect(
                                        BLOCKBLAST_OFFSET_X + c * BLOCKBLAST_CELL_SIZE + 1,
                                        BLOCKBLAST_OFFSET_Y + r * BLOCKBLAST_CELL_SIZE + 1,
                                        BLOCKBLAST_CELL_SIZE - 2,
                                        BLOCKBLAST_CELL_SIZE - 2
                                    )
                                    surf = pygame.Surface((BLOCKBLAST_CELL_SIZE - 2, BLOCKBLAST_CELL_SIZE - 2), pygame.SRCALPHA)
                                    pygame.draw.rect(surf, (0, 255, 0, 100), (0, 0, BLOCKBLAST_CELL_SIZE - 2, BLOCKBLAST_CELL_SIZE - 2), border_radius=5)
                                    WINDOW.blit(surf, rect)
        
        # 테두리
        pygame.draw.rect(WINDOW, COLORS['outline'], grid_rect, 4)
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
        
        # 사용 가능한 블록들 표시
        piece_area_y = BLOCKBLAST_OFFSET_Y + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE + 30
        piece_spacing = GAME_WIDTH // 3
        
        for idx, piece in enumerate(self.available_pieces):
            if piece is None:
                continue
            
            # 블록을 드래그 중이 아닐 때만 표시
            if self.dragging and idx == self.selected_piece_idx:
                continue
            
            # 블록을 중앙에 배치
            piece_center_x = piece_spacing * idx + piece_spacing // 2
            piece_x = piece_center_x - (piece.width * 50) // 2
            piece_y = piece_area_y
            
            # 배치 가능 여부 확인
            can_be_placed = False
            for r in range(BLOCKBLAST_GRID_SIZE):
                for c in range(BLOCKBLAST_GRID_SIZE):
                    if self.can_place(piece, r, c):
                        can_be_placed = True
                        break
                if can_be_placed:
                    break
            
            # 배치 불가능하면 회색으로 표시
            alpha = 255 if can_be_placed else 100
            piece.draw(piece_x, piece_y, 50, alpha)
        
        # 드래그 중인 블록 (마우스 중심에 표시)
        if self.dragging and self.selected_piece_idx is not None:
            piece = self.available_pieces[self.selected_piece_idx]
            if piece:
                # 블록의 중심이 마우스 위치에 오도록
                draw_x = self.mouse_x - (piece.width * 50) // 2
                draw_y = self.mouse_y - (piece.height * 50) // 2
                piece.draw(draw_x, draw_y, 50)
        
        # 관리자 모드 표시
        if ADMIN_MODE:
            UIDrawer.admin_mode_overlay()
        
        # 우측 패널
        y = UIDrawer.panel_header("점수:", self.score)
        UIDrawer.panel_separator(y)
        
        # 조작법
        y += 10
        controls = [
            "마우스로 블록 선택",
            "드래그하여 배치",
            "",
            "줄을 완성하면",
            "자동으로 제거됩니다"
        ]
        for i, text in enumerate(controls):
            WINDOW.blit(FONTS['tiny'].render(text, True, COLORS['font']), 
                       (GAME_WIDTH + 10, y + i * 18))
        
        y += len(controls) * 18 + 10
        UIDrawer.panel_separator(y)
        UIDrawer.leaderboard(self.leaderboard, y + 10)
        
        # 오버레이
        if self.entering_pw:
            UIDrawer.password_overlay(self.pw_input)
        elif self.game_over:
            UIDrawer.game_over_screen()
        
        pygame.display.update()
    
    def handle_event(self, event):
        """이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if self.entering_pw:
                if event.key == pygame.K_ESCAPE:
                    self.entering_pw = False
                    self.pw_input = ""
                elif event.key == pygame.K_RETURN:
                    if PasswordManager.verify(self.pw_input):
                        LeaderboardManager.reset(GAME_BLOCKBLAST)
                        self.leaderboard = LeaderboardManager.load(GAME_BLOCKBLAST)
                    self.entering_pw = False
                    self.pw_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.pw_input = self.pw_input[:-1]
                elif event.unicode.isprintable() and len(self.pw_input) < 20:
                    self.pw_input += event.unicode
            else:
                if event.key == pygame.K_ESCAPE:
                    return MENU
                elif event.key == pygame.K_F12 and not self.game_over:
                    self.entering_pw = True
        
        elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over and not self.entering_pw:
            if event.button == 1:  # 좌클릭
                # 사용 가능한 블록 클릭 확인
                piece_area_y = BLOCKBLAST_OFFSET_Y + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE + 30
                piece_spacing = GAME_WIDTH // 3
                
                for idx, piece in enumerate(self.available_pieces):
                    if piece is None:
                        continue
                    
                    # 블록을 중앙에 배치
                    piece_center_x = piece_spacing * idx + piece_spacing // 2
                    piece_x = piece_center_x - (piece.width * 50) // 2
                    piece_y = piece_area_y
                    
                    # 블록 영역 클릭 확인
                    if (piece_x <= event.pos[0] <= piece_x + piece.width * 50 and
                        piece_y <= event.pos[1] <= piece_y + piece.height * 50):
                        self.selected_piece_idx = idx
                        self.dragging = True
                        self.mouse_x, self.mouse_y = event.pos
                        break
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.mouse_x, self.mouse_y = event.pos
        
        elif event.type == pygame.MOUSEBUTTONUP and self.dragging:
            if event.button == 1:  # 좌클릭 release
                if self.selected_piece_idx is not None:
                    piece = self.available_pieces[self.selected_piece_idx]
                    if piece:
                        grid_row, grid_col = self.screen_to_grid(self.mouse_x, self.mouse_y, piece)
                        
                        if self.can_place(piece, grid_row, grid_col):
                            # 블록 배치
                            self.place_piece(piece, grid_row, grid_col)
                            self.score += 10  # 배치 점수
                            self.available_pieces[self.selected_piece_idx] = None
                            
                            # 모든 블록을 사용했으면 새로 생성
                            if all(p is None for p in self.available_pieces):
                                self.available_pieces = [self.new_piece() for _ in range(3)]
                                self.score += 50  # 보너스 점수
                            
                            # 게임 오버 확인
                            if self.check_game_over():
                                self.game_over = True
                                self.leaderboard = LeaderboardManager.update(GAME_BLOCKBLAST, self.score)
                
                self.dragging = False
                self.selected_piece_idx = None
        
        return GAME_BLOCKBLAST

def run_blockblast():
    """블록블라스트 게임 실행"""
    game = BlockBlast()
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            result = game.handle_event(event)
            if result != GAME_BLOCKBLAST:
                return result
        
        game.draw()

# ==================== 메인 ====================
def main():
    current_game = MENU
    clock = pygame.time.Clock()
    
    game_runners = {
        MENU: run_menu,
        GAME_2048: run_2048,
        GAME_BREAKOUT: run_breakout,
        GAME_TYPING: run_typing,
        GAME_TETRIS: run_tetris,
        GAME_BLOCKBLAST: run_blockblast,
        LEADERBOARD: run_leaderboard
    }
    
    while True:
        clock.tick(FPS)
        runner = game_runners.get(current_game)
        if not runner:
            break
        result = runner()
        if result is None:
            break
        current_game = result
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()