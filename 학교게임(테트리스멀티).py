import pygame
import random
import sys
import json
import os
import math
import socket
import threading
import pickle

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
    'green': (0, 255, 0), 'blue': (0, 0, 255), 'yellow': (255, 255, 0),
    'pink': (255, 182, 193), 'brown': (139, 69, 19), 'dark_gray': (50, 50, 50),
    'purple': (148, 0, 211), 'gold': (255, 215, 0), 'cyan': (0, 255, 255),
    'orange': (255, 165, 0), 'lime': (50, 205, 50)
}

# 게임 상태
MENU, GAME_2048, GAME_BREAKOUT, GAME_TYPING, GAME_TETRIS, GAME_BLOCKBLAST, LEADERBOARD, TETRIS_MULTI = "menu", "2048", "breakout", "typing", "tetris", "blockblast", "leaderboard", "tetris_multi"

# 관리자 모드 전역 변수
ADMIN_MODE = False

# 현재 학번 저장
CURRENT_STUDENT_ID = None

# ==================== 파티클 효과 시스템 ====================
class EffectParticle:
    """개별 파티클 클래스 (효과용)"""
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0

    def update(self):
        """파티클 업데이트"""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3  # 중력 효과
        self.age += 1
        return self.age < self.lifetime

    def draw(self, surface):
        """파티클 그리기"""
        alpha = int(255 * (1 - self.age / self.lifetime))
        color = (*self.color[:3], alpha)
        size = int(self.size * (1 - self.age / self.lifetime))
        if size > 0:
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size, size), size)
            surface.blit(surf, (int(self.x - size), int(self.y - size)))

class ParticleSystem:
    """파티클 시스템 관리"""
    def __init__(self):
        self.particles = []

    def add_explosion(self, x, y, color, count=20):
        """폭발 효과"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(3, 8)
            lifetime = random.randint(20, 40)
            self.particles.append(EffectParticle(x, y, vx, vy, color, size, lifetime))

    def add_sparkle(self, x, y, count=10):
        """반짝임 효과"""
        colors = [(255, 255, 0), (255, 215, 0), (255, 255, 255)]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 5)
            lifetime = random.randint(15, 30)
            color = random.choice(colors)
            self.particles.append(EffectParticle(x, y, vx, vy, color, size, lifetime))

    def add_confetti(self, x, y, count=30):
        """색종이 효과"""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                  (255, 0, 255), (0, 255, 255), (255, 165, 0)]
        for _ in range(count):
            vx = random.uniform(-5, 5)
            vy = random.uniform(-10, -3)
            size = random.uniform(4, 10)
            lifetime = random.randint(40, 80)
            color = random.choice(colors)
            self.particles.append(EffectParticle(x, y, vx, vy, color, size, lifetime))

    def update(self):
        """모든 파티클 업데이트"""
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surface):
        """모든 파티클 그리기"""
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        """모든 파티클 제거"""
        self.particles.clear()

# 전역 파티클 시스템
PARTICLE_SYSTEM = ParticleSystem()

# ==================== 떠오르는 텍스트 시스템 ====================
class FloatingText:
    """떠오르는 점수 텍스트"""
    def __init__(self, x, y, text, color, size='medium'):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 60  # 1초
        self.age = 0
        self.size = size
        self.vy = -2  # 위로 떠오르는 속도

    def update(self):
        self.y += self.vy
        self.age += 1
        return self.age < self.lifetime

    def draw(self, surface):
        alpha = int(255 * (1 - self.age / self.lifetime))
        if alpha > 0:
            font = FONTS[self.size]
            text_surf = font.render(self.text, True, self.color)
            # 알파 적용
            text_surf.set_alpha(alpha)
            # 크기 애니메이션 (처음에 크게 나타났다가 작아짐)
            scale = 1.0 + (1 - self.age / self.lifetime) * 0.3
            if scale != 1.0:
                new_width = int(text_surf.get_width() * scale)
                new_height = int(text_surf.get_height() * scale)
                text_surf = pygame.transform.scale(text_surf, (new_width, new_height))
            surface.blit(text_surf, (int(self.x - text_surf.get_width() // 2), int(self.y)))

class FloatingTextSystem:
    """떠오르는 텍스트 시스템"""
    def __init__(self):
        self.texts = []

    def add_text(self, x, y, text, color=(255, 215, 0), size='medium'):
        self.texts.append(FloatingText(x, y, text, color, size))

    def update(self):
        self.texts = [t for t in self.texts if t.update()]

    def draw(self, surface):
        for t in self.texts:
            t.draw(surface)

    def clear(self):
        self.texts.clear()

# 전역 떠오르는 텍스트 시스템
FLOATING_TEXT_SYSTEM = FloatingTextSystem()

# ==================== 학번 입력 시스템 ====================
class StudentIDInput:
    """학번 입력 화면"""
    def __init__(self):
        self.student_id = ""
        self.error_msg = ""
        self.animation_time = 0

    def validate_id(self, student_id):
        """학번 유효성 검증"""
        if not student_id:
            return False, "학번을 입력해주세요"
        if not student_id.isdigit():
            return False, "숫자만 입력 가능합니다"
        if len(student_id) != 5:
            return False, "5자리 숫자를 입력해주세요"
        return True, ""

    def draw(self):
        """학번 입력 화면 그리기"""
        WINDOW.fill(COLORS['bg'])

        # 제목
        title = FONTS['huge'].render("학번 입력", True, COLORS['font'])
        WINDOW.blit(title, (WIDTH//2 - title.get_width()//2, 150))

        # 설명
        desc = FONTS['small'].render("게임 시작 전 학번을 입력해주세요", True, COLORS['font'])
        WINDOW.blit(desc, (WIDTH//2 - desc.get_width()//2, 220))

        # 입력 박스
        box_rect = pygame.Rect(WIDTH//2 - 200, 300, 400, 80)
        box_color = (255, 255, 255) if not self.error_msg else (255, 200, 200)
        pygame.draw.rect(WINDOW, box_color, box_rect, border_radius=15)
        pygame.draw.rect(WINDOW, COLORS['outline'], box_rect, 4, border_radius=15)

        # 입력된 학번 표시
        if self.student_id:
            id_text = FONTS['large'].render(self.student_id, True, COLORS['font'])
        else:
            id_text = FONTS['medium'].render("학번 입력...", True, (150, 150, 150))
        WINDOW.blit(id_text, (WIDTH//2 - id_text.get_width()//2, 320))

        # 에러 메시지
        if self.error_msg:
            error_surf = FONTS['small'].render(self.error_msg, True, COLORS['red'])
            WINDOW.blit(error_surf, (WIDTH//2 - error_surf.get_width()//2, 400))

        # 안내 문구
        help_texts = [
            "숫자 5자리를 입력하세요",
            "ENTER: 확인 | ESC: 취소"
        ]
        for i, text in enumerate(help_texts):
            surf = FONTS['small'].render(text, True, (100, 100, 100))
            WINDOW.blit(surf, (WIDTH//2 - surf.get_width()//2, 450 + i * 30))

        # 경고문
        warning_text = "부적절한 학번 입력 시 기록이 삭제될 수 있습니다"
        warning_surf = FONTS['small'].render(warning_text, True, (200, 50, 50))
        WINDOW.blit(warning_surf, (WIDTH//2 - warning_surf.get_width()//2, 520))

        pygame.display.update()

    def handle_event(self, event):
        """이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return None  # 취소
            elif event.key == pygame.K_RETURN:
                valid, msg = self.validate_id(self.student_id)
                if valid:
                    return self.student_id
                else:
                    self.error_msg = msg
            elif event.key == pygame.K_BACKSPACE:
                self.student_id = self.student_id[:-1]
                self.error_msg = ""
            elif event.unicode.isdigit() and len(self.student_id) < 5:
                self.student_id += event.unicode
                self.error_msg = ""
        return "input"  # 계속 입력 중

    def run(self):
        """학번 입력 루프"""
        clock = pygame.time.Clock()
        while True:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                result = self.handle_event(event)
                if result != "input":
                    return result

            self.draw()

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
                return True
            except Exception as e:
                return False
        else:
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
            return password == PasswordManager.DEFAULT_PASSWORD

    @staticmethod
    def change_password(new_password):
        """비밀번호 변경"""
        try:
            with open(PasswordManager.PASSWORD_FILE, 'w', encoding='utf-8') as f:
                f.write(new_password)
            return True
        except Exception as e:
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
    'L': COLORS['orange']  # 주황색
}

# ==================== 블록블라스트 설정 ====================
BLOCKBLAST_GRID_SIZE = 8
BLOCKBLAST_CELL_SIZE = 60
BLOCKBLAST_OFFSET_X = (GAME_WIDTH - BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE) // 2
BLOCKBLAST_OFFSET_Y = 30

# 블록블라스트 블록 모양들 (난이도별 분류)

# 쉬운 블록 (초반용 - 작고 단순) - 높은 출현 빈도
BLOCKBLAST_SHAPES_EASY = [
    # 2칸 블록
    [[1, 1]],
    [[1], [1]],

    # 2x2 정사각형
    [[1, 1], [1, 1]],

    # 3칸 블록
    [[1, 1, 1]],
    [[1], [1], [1]],
]

# 보통 블록 - 중간 출현 빈도
BLOCKBLAST_SHAPES_NORMAL = [
    # 4칸 블록
    [[1, 1, 1, 1]],
    [[1], [1], [1], [1]],

    # T자형 (4가지 방향)
    [[1, 1, 1], [0, 1, 0]],
    [[0, 1], [1, 1], [0, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 0], [1, 1], [1, 0]],

    # Z자형
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1], [1, 1], [1, 0]],

    # S자형
    [[0, 1, 1], [1, 1, 0]],
    [[1, 0], [1, 1], [0, 1]],

    # ㅗ자형
    [[1, 0], [1, 1]],
    [[0, 1], [1, 1]],
]

# 니은자/L자형 블록 (어려운 블록) - 낮은 출현 빈도
BLOCKBLAST_SHAPES_LSHAPE = [
    # 작은 ㄱ자형 (3칸)
    [[1, 1], [1, 0]],
    [[1, 1], [0, 1]],
    [[1, 0], [1, 1]],
    [[0, 1], [1, 1]],

    # 중간 L자형 (4가지 방향)
    [[1, 0], [1, 0], [1, 1]],
    [[0, 1], [0, 1], [1, 1]],
    [[1, 1], [1, 0], [1, 0]],
    [[1, 1], [0, 1], [0, 1]],

    # 큰 L자형
    [[1, 0, 0], [1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [0, 0, 1], [1, 1, 1]],
    [[1, 1, 1], [1, 0, 0], [1, 0, 0]],
    [[1, 1, 1], [0, 0, 1], [0, 0, 1]],
]

# 매우 어려운 블록 - 낮은 출현 빈도
BLOCKBLAST_SHAPES_HARD = [
    # 5칸 블록
    [[1, 1, 1, 1, 1]],
    [[1], [1], [1], [1], [1]],

    # 3x3 정사각형
    [[1, 1, 1], [1, 1, 1], [1, 1, 1]],

    # 2x3 블록
    [[1, 1, 1], [1, 1, 1]],

    # 3x2 블록
    [[1, 1], [1, 1], [1, 1]],
]

# 호환성을 위한 전체 블록 리스트
BLOCKBLAST_SHAPES = BLOCKBLAST_SHAPES_EASY + BLOCKBLAST_SHAPES_NORMAL + BLOCKBLAST_SHAPES_LSHAPE + BLOCKBLAST_SHAPES_HARD

# 블록 출현 가중치 (높을수록 자주 출현)
BLOCKBLAST_WEIGHTS = {
    'easy': 5,      # 쉬운 블록 (5배 확률)
    'normal': 3,    # 보통 블록 (3배 확률)
    'lshape': 1,    # 니은자/L자형 (1배 확률 - 낮음)
    'hard': 1       # 매우 어려운 블록 (1배 확률 - 낮음)
}

# 블록블라스트 색상 (더 밝고 화려하게 개선)
BLOCKBLAST_COLORS = [
    (255, 69, 58),    # 생생한 빨강
    (255, 159, 10),   # 밝은 오렌지
    (255, 214, 10),   # 선명한 노랑
    (48, 209, 88),    # 생생한 초록
    (90, 200, 250),   # 하늘색
    (191, 90, 242),   # 보라색
    (255, 55, 95),    # 분홍
    (100, 210, 255),  # 청록색
    (175, 82, 222),   # 자주색
]

# 블록블라스트 배경색 (숫자가 잘 보이도록)
BLOCKBLAST_BG = (240, 245, 250)        # 밝은 회색-파랑
BLOCKBLAST_GRID_COLOR = (200, 210, 220) # 부드러운 회색

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
pygame.display.set_caption("게임모음집")

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
    def update(game_type, score, difficulty=None, stage=None, student_id=None):
        """리더보드 업데이트 (학번 포함)"""
        if score <= 0:
            return LeaderboardManager.load(game_type, difficulty)

        lb = LeaderboardManager.load(game_type, difficulty)

        # 학번이 있으면 딕셔너리 형태로 저장
        if student_id:
            if game_type == GAME_TYPING and stage is not None:
                # 같은 학번의 최고 점수만 유지
                existing_entries = [e for e in lb if isinstance(e, dict) and e.get('student_id') == student_id]
                if existing_entries:
                    # 기존 기록과 비교
                    best_existing = max(existing_entries, key=lambda x: (x.get('stage', 0), x.get('score', 0)))
                    if (stage > best_existing.get('stage', 0) or
                        (stage == best_existing.get('stage', 0) and score > best_existing.get('score', 0))):
                        # 새 기록이 더 좋으면 기존 것들 모두 제거
                        lb = [e for e in lb if not (isinstance(e, dict) and e.get('student_id') == student_id)]
                        entry = {'student_id': student_id, 'stage': stage, 'score': score}
                        lb.append(entry)
                    # 새 기록이 더 나쁘면 추가하지 않음
                else:
                    # 처음 기록하는 경우
                    entry = {'student_id': student_id, 'stage': stage, 'score': score}
                    lb.append(entry)
                lb = sorted(lb, key=lambda x: (-x.get('stage', 0) if isinstance(x, dict) else 0,
                                               -x.get('score', 0) if isinstance(x, dict) else 0))[:10]
            else:
                # 같은 학번의 최고 점수만 유지
                existing_entries = [e for e in lb if isinstance(e, dict) and e.get('student_id') == student_id]
                if existing_entries:
                    best_existing = max(existing_entries, key=lambda x: x.get('score', 0))
                    # 블록깨기는 시간이므로 낮은 게 좋음
                    if game_type == GAME_BREAKOUT:
                        if score < best_existing.get('score', 999999):
                            lb = [e for e in lb if not (isinstance(e, dict) and e.get('student_id') == student_id)]
                            entry = {'student_id': student_id, 'score': score}
                            lb.append(entry)
                    else:
                        if score > best_existing.get('score', 0):
                            lb = [e for e in lb if not (isinstance(e, dict) and e.get('student_id') == student_id)]
                            entry = {'student_id': student_id, 'score': score}
                            lb.append(entry)
                else:
                    entry = {'student_id': student_id, 'score': score}
                    lb.append(entry)

                # 블록깨기는 시간이므로 오름차순, 나머지는 내림차순
                if game_type == GAME_BREAKOUT:
                    lb = sorted(lb, key=lambda x: x.get('score', 999999) if isinstance(x, dict) else x)[:10]
                else:
                    lb = sorted(lb, key=lambda x: -x.get('score', 0) if isinstance(x, dict) else -x)[:10]
        else:
            # 하위 호환성: 학번 없이 저장 (기존 방식)
            if game_type == GAME_TYPING and stage is not None:
                entry = {'stage': stage, 'score': score}
                lb.append(entry)
                lb = sorted(lb, key=lambda x: (-x['stage'], -x['score']) if isinstance(x, dict) else (0, 0))[:10]
            else:
                lb.append(score)
                lb = sorted(list(set(lb)), reverse=(game_type != GAME_BREAKOUT))[:10]

        LeaderboardManager.save(game_type, lb, difficulty)
        return lb
    
    @staticmethod
    def reset(game_type, difficulty=None):
        return LeaderboardManager.save(game_type, [], difficulty)

    @staticmethod
    def delete_entry(game_type, index, difficulty=None):
        """리더보드 항목 삭제"""
        lb = LeaderboardManager.load(game_type, difficulty)
        if 0 <= index < len(lb):
            lb.pop(index)
            LeaderboardManager.save(game_type, lb, difficulty)
            return True
        return False

    @staticmethod
    def edit_entry(game_type, index, new_student_id, difficulty=None):
        """리더보드 항목의 학번 수정"""
        lb = LeaderboardManager.load(game_type, difficulty)
        if 0 <= index < len(lb):
            if isinstance(lb[index], dict):
                lb[index]['student_id'] = new_student_id
                LeaderboardManager.save(game_type, lb, difficulty)
                return True
        return False

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
        """리더보드 표시 (학번 포함)"""
        # 제목
        title = "최고 기록" if is_time or is_typing else "순위표"
        title_surf = FONTS['medium'].render(title, True, COLORS['font'])
        WINDOW.blit(title_surf, (GAME_WIDTH + 10, y))
        y += 35

        # 구분선
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH + 10, y), (WIDTH - 10, y), 2)
        y += 15

        # ESC 안내
        esc_surf = FONTS['tiny'].render("ESC: 메뉴", True, (120, 120, 120))
        WINDOW.blit(esc_surf, (GAME_WIDTH + 10, y))
        y += 25

        # 순위 표시
        medal_colors = [(255, 215, 0), (230, 230, 230), (205, 127, 50)]  # 금, 은(밝게 개선), 동

        for i, s in enumerate(scores[:3]):
            # 2등 배경 강조 (가시성 개선)
            if i == 1:
                bg_rect = pygame.Rect(GAME_WIDTH + 10, y - 3, RIGHT_PANEL - 20, 46)
                pygame.draw.rect(WINDOW, (80, 80, 100), bg_rect, border_radius=8)  # 어두운 배경

            # 순위 배지
            medal_color = medal_colors[i] if i < 3 else COLORS['font']
            rank_surf = FONTS['medium'].render(f"{i+1}", True, medal_color)
            WINDOW.blit(rank_surf, (GAME_WIDTH + 15, y))

            if isinstance(s, dict):
                student_id = s.get('student_id', '익명')

                if is_typing:
                    stage = s.get('stage', 0)
                    score = s.get('score', 0)
                    # 학번
                    id_surf = FONTS['small'].render(student_id, True, COLORS['font'])
                    WINDOW.blit(id_surf, (GAME_WIDTH + 50, y + 3))
                    # 상세 정보
                    detail_surf = FONTS['tiny'].render(f"{stage}단계  {score:,}점", True, (100, 100, 100))
                    WINDOW.blit(detail_surf, (GAME_WIDTH + 50, y + 22))
                else:
                    score = s.get('score', 0)
                    # 학번
                    id_surf = FONTS['small'].render(student_id, True, COLORS['font'])
                    WINDOW.blit(id_surf, (GAME_WIDTH + 50, y + 3))
                    # 점수/시간
                    if is_time:
                        detail_text = f"{score}초"
                    else:
                        detail_text = f"{score:,}점" if score < 10000 else f"{score//1000}k점"
                    detail_surf = FONTS['tiny'].render(detail_text, True, (100, 100, 100))
                    WINDOW.blit(detail_surf, (GAME_WIDTH + 50, y + 22))
            else:
                # 하위 호환성
                if is_time:
                    txt = f"{s}초"
                else:
                    txt = f"{s:,}점" if s < 10000 else f"{s//1000}k점"
                score_surf = FONTS['small'].render(txt, True, COLORS['font'])
                WINDOW.blit(score_surf, (GAME_WIDTH + 50, y + 8))

            y += 50
    
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
    global ADMIN_MODE, CURRENT_STUDENT_ID
    entering_admin_pw = False
    admin_pw_input = ""
    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)

        # 배경
        WINDOW.fill(COLORS['bg'])

        # 제목
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

        # 버튼 그리기
        for btn, (_, name, _) in zip(buttons, games):
            UIDrawer.button(btn, name)

        # 안내 문구
        UIDrawer.text_centered("클릭하거나 숫자키를 눌러 선택하세요", 660, 'small')

        # 관리자 모드
        if ADMIN_MODE:
            UIDrawer.admin_mode_overlay()

        # 비밀번호 입력
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
                            PARTICLE_SYSTEM.add_confetti(WIDTH//2, HEIGHT//2, 50)
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
                                # 리더보드는 학번 불필요
                                if game_type == LEADERBOARD:
                                    return game_type

                                # 테트리스는 싱글/멀티 선택
                                if game_type == GAME_TETRIS:
                                    return "tetris_mode_select"

                                # 게임 시작 전 학번 입력
                                student_input = StudentIDInput()
                                result = student_input.run()
                                if result:
                                    CURRENT_STUDENT_ID = result
                                    return game_type

            if event.type == pygame.MOUSEBUTTONDOWN and not entering_admin_pw:
                for i, btn in enumerate(buttons):
                    if btn.collidepoint(pygame.mouse.get_pos()):
                        game_type = games[i][0]

                        # 리더보드는 학번 불필요
                        if game_type == LEADERBOARD:
                            return game_type

                        # 테트리스는 싱글/멀티 선택
                        if game_type == GAME_TETRIS:
                            return "tetris_mode_select"

                        # 게임 시작 전 학번 입력
                        student_input = StudentIDInput()
                        result = student_input.run()
                        if result:
                            CURRENT_STUDENT_ID = result
                            return game_type

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
        
        for i, entry in enumerate(lb_2048[:10]):
            y_pos = y_start + 58 + i * 36
            if isinstance(entry, dict):
                student_id = entry.get('student_id', '익명')
                score = entry.get('score', 0)
                txt = f"{i+1}. {student_id[:6]}"
                txt2 = f"   {score:,}점"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x1 + 10, y_pos))
                WINDOW.blit(FONTS['tiny'].render(txt2, True, (100, 100, 100)), (x1 + 10, y_pos + 14))
            else:
                txt = f"{i+1}. {entry:,}점"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x1 + 10, y_pos))
        
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
            
            for i, entry in enumerate(lb_break[:5]):
                if isinstance(entry, dict):
                    student_id = entry.get('student_id', '익명')
                    time = entry.get('score', 0)
                    txt = f"{i+1}. {student_id[:6]}: {time}초"
                else:
                    txt = f"{i+1}. {entry}초"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x2 + 12, y_diff + 25 + i * 20))
        
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
                student_id = entry.get('student_id', '익명')
                stage = entry.get('stage', 0)
                score = entry.get('score', 0)
                txt1 = f"{i+1}. {student_id[:6]}"
                txt2 = f"   {stage}단계 {score:,}점"
                WINDOW.blit(FONTS['tiny'].render(txt1, True, COLORS['font']), (x3 + 10, y_pos))
                WINDOW.blit(FONTS['tiny'].render(txt2, True, (100, 100, 100)), (x3 + 10, y_pos + 14))
            else:
                txt = f"{i+1}. {entry:,}"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x3 + 10, y_pos))
        
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
        
        for i, entry in enumerate(lb_tetris[:10]):
            y_pos = y_start + 53 + i * 36
            if isinstance(entry, dict):
                student_id = entry.get('student_id', '익명')
                score = entry.get('score', 0)
                txt = f"{i+1}. {student_id[:6]}"
                txt2 = f"   {score:,}점"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x4 + 10, y_pos))
                WINDOW.blit(FONTS['tiny'].render(txt2, True, (100, 100, 100)), (x4 + 10, y_pos + 14))
            else:
                txt = f"{i+1}. {entry:,}점"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x4 + 10, y_pos))
        
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
        
        for i, entry in enumerate(lb_blast[:10]):
            y_pos = y_start + 53 + i * 36
            if isinstance(entry, dict):
                student_id = entry.get('student_id', '익명')
                score = entry.get('score', 0)
                txt = f"{i+1}. {student_id[:6]}"
                txt2 = f"   {score:,}점"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x5 + 10, y_pos))
                WINDOW.blit(FONTS['tiny'].render(txt2, True, (100, 100, 100)), (x5 + 10, y_pos + 14))
            else:
                txt = f"{i+1}. {entry:,}점"
                WINDOW.blit(FONTS['tiny'].render(txt, True, COLORS['font']), (x5 + 10, y_pos))
        
        # 안내 문구
        help_y = 720
        if ADMIN_MODE:
            UIDrawer.text_centered("F10: 편집 모드 | ESC: 메뉴", help_y, 'small', (255, 100, 100))
            UIDrawer.text_centered("(관리자 모드 활성화 중)", help_y + 25, 'tiny', (200, 0, 0))
        else:
            UIDrawer.text_centered("ESC: 메뉴로 돌아가기", help_y, 'medium')

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return MENU
                elif event.key == pygame.K_F10 and ADMIN_MODE:
                    # 편집 모드 진입
                    PARTICLE_SYSTEM.add_confetti(WIDTH//2, HEIGHT//2, 50)
                    result = run_admin_leaderboard_editor()
                    if result == MENU:
                        return MENU

# ==================== 관리자 리더보드 편집 ====================
def run_admin_leaderboard_editor():
    """관리자 리더보드 편집 모드"""
    selected_game = None
    selected_difficulty = None
    selected_index = None
    editing_id = False
    new_id_input = ""
    message = ""
    message_time = 0

    games = [
        (GAME_2048, "2048", None),
        (GAME_BREAKOUT, "블록깨기 (쉬움)", "easy"),
        (GAME_BREAKOUT, "블록깨기 (보통)", "normal"),
        (GAME_BREAKOUT, "블록깨기 (어려움)", "hard"),
        (GAME_TYPING, "케이크던지기", None),
        (GAME_TETRIS, "테트리스", None),
        (GAME_BLOCKBLAST, "블록블라스트", None)
    ]

    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)
        WINDOW.fill(COLORS['bg'])

        # 제목
        UIDrawer.text_centered("관리자 리더보드 편집", 30, 'large', (255, 0, 0))

        if selected_game is None:
            # 게임 선택 화면
            UIDrawer.text_centered("편집할 게임을 선택하세요", 90, 'medium')

            y_offset = 140
            for i, (game, name, diff) in enumerate(games):
                btn = pygame.Rect(WIDTH//2 - 200, y_offset + i * 50, 400, 45)
                pygame.draw.rect(WINDOW, (255, 220, 220), btn, border_radius=10)
                pygame.draw.rect(WINDOW, (200, 0, 0), btn, 3, border_radius=10)
                txt = FONTS['small'].render(f"{i+1}. {name}", True, COLORS['font'])
                WINDOW.blit(txt, txt.get_rect(center=btn.center))

            UIDrawer.text_centered("ESC: 돌아가기", 700, 'small')

        else:
            # 항목 편집 화면
            lb = LeaderboardManager.load(selected_game, selected_difficulty)
            game_name = [name for g, name, d in games if g == selected_game and d == selected_difficulty][0]

            UIDrawer.text_centered(f"[{game_name}] 편집 중", 80, 'medium')

            y_offset = 120
            for i, entry in enumerate(lb[:15]):
                y = y_offset + i * 32

                # 항목 표시
                if isinstance(entry, dict):
                    student_id = entry.get('student_id', '익명')
                    score = entry.get('score', 0)
                    stage = entry.get('stage', '')
                    if stage:
                        txt = f"{i+1}. {student_id} - {stage}단계 {score:,}점"
                    else:
                        txt = f"{i+1}. {student_id} - {score:,}점"
                else:
                    txt = f"{i+1}. {entry:,}"

                color = (255, 200, 200) if selected_index == i else COLORS['font']
                surf = FONTS['tiny'].render(txt, True, color)
                WINDOW.blit(surf, (WIDTH//2 - 250, y))

            # 안내
            help_texts = [
                "숫자 입력: 항목 선택",
                "DELETE: 선택 항목 삭제",
                "E: 학번 수정",
                "ESC: 게임 선택으로"
            ]
            y_help = 600
            for i, text in enumerate(help_texts):
                surf = FONTS['tiny'].render(text, True, (100, 100, 100))
                WINDOW.blit(surf, (WIDTH//2 - 150, y_help + i * 20))

            # 선택된 항목 표시
            if selected_index is not None:
                txt = f"선택: {selected_index + 1}번 항목"
                surf = FONTS['small'].render(txt, True, (255, 0, 0))
                WINDOW.blit(surf, (WIDTH//2 - surf.get_width()//2, 550))

            # 학번 수정 모드
            if editing_id:
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(128)
                overlay.fill(COLORS['black'])
                WINDOW.blit(overlay, (0, 0))

                box = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 80, 400, 160)
                pygame.draw.rect(WINDOW, COLORS['white'], box, border_radius=15)
                pygame.draw.rect(WINDOW, (200, 0, 0), box, 4, border_radius=15)

                texts = [
                    ("새 학번 입력:", 'small'),
                    (new_id_input if new_id_input else "(입력...)", 'medium'),
                    ("ENTER: 확인 | ESC: 취소", 'tiny')
                ]
                for i, (text, font) in enumerate(texts):
                    color = COLORS['font'] if i != 1 else (0, 0, 255)
                    surf = FONTS[font].render(text, True, color)
                    WINDOW.blit(surf, (WIDTH//2 - surf.get_width()//2, HEIGHT//2 - 60 + i * 40))

        # 메시지 표시
        if message and message_time > 0:
            msg_surf = FONTS['medium'].render(message, True, (0, 200, 0))
            WINDOW.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT - 50))
            message_time -= 1

        # 파티클
        PARTICLE_SYSTEM.update()
        PARTICLE_SYSTEM.draw(WINDOW)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return MENU

            if event.type == pygame.KEYDOWN:
                if editing_id:
                    # 학번 수정 모드
                    if event.key == pygame.K_ESCAPE:
                        editing_id = False
                        new_id_input = ""
                    elif event.key == pygame.K_RETURN and new_id_input:
                        if LeaderboardManager.edit_entry(selected_game, selected_index, new_id_input, selected_difficulty):
                            message = "학번이 수정되었습니다!"
                            message_time = 120
                            PARTICLE_SYSTEM.add_confetti(WIDTH//2, HEIGHT//2, 30)
                        editing_id = False
                        new_id_input = ""
                        selected_index = None
                    elif event.key == pygame.K_BACKSPACE:
                        new_id_input = new_id_input[:-1]
                    elif event.unicode.isdigit() and len(new_id_input) < 10:
                        new_id_input += event.unicode

                elif selected_game is None:
                    # 게임 선택 모드
                    if event.key == pygame.K_ESCAPE:
                        return LEADERBOARD
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(games):
                            selected_game, _, selected_difficulty = games[idx]
                            selected_index = None

                else:
                    # 항목 편집 모드
                    if event.key == pygame.K_ESCAPE:
                        selected_game = None
                        selected_index = None
                    elif event.key == pygame.K_DELETE and selected_index is not None:
                        # 삭제 확인
                        if LeaderboardManager.delete_entry(selected_game, selected_index, selected_difficulty):
                            message = "항목이 삭제되었습니다!"
                            message_time = 120
                            PARTICLE_SYSTEM.add_explosion(WIDTH//2, HEIGHT//2, (255, 0, 0), 30)
                            selected_index = None
                    elif event.key == pygame.K_e and selected_index is not None:
                        # 학번 수정 시작
                        editing_id = True
                        new_id_input = ""
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        # 항목 선택
                        idx = event.key - pygame.K_1
                        lb = LeaderboardManager.load(selected_game, selected_difficulty)
                        if idx < len(lb):
                            selected_index = idx
                    elif event.key == pygame.K_0:
                        idx = 9
                        lb = LeaderboardManager.load(selected_game, selected_difficulty)
                        if idx < len(lb):
                            selected_index = idx

# ==================== 2048 게임 ====================
class Game2048:
    def __init__(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.game_over_timer = 0
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
                self.leaderboard = LeaderboardManager.update(GAME_2048, self.score, student_id=CURRENT_STUDENT_ID)
        
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

        # 게임 오버 후 5초 자동 메뉴 복귀
        if game.game_over:
            game.game_over_timer += 1
            if game.game_over_timer >= 300:  # 5초 (60 FPS * 5)
                return MENU

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
    def __init__(self, is_multiplayer=False):
        self.is_multiplayer = is_multiplayer
        self.grid = [[0] * TETRIS_GRID_WIDTH for _ in range(TETRIS_GRID_HEIGHT)]
        self.bag = []  # 7bag 시스템
        self.next_pieces = []  # 다음 4개 블록 미리보기

        # 초기 블록 생성 (현재 블록 + 다음 4개)
        self._refill_next_pieces()
        self.current_block = self._get_next_piece()

        self.hold_block = None  # 홀드 블록
        self.can_hold = True  # 이번 턴에 홀드 가능 여부
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.game_over_timer = 0
        self.entering_pw = False
        self.pw_input = ""
        self.leaderboard = LeaderboardManager.load(GAME_TETRIS) if not is_multiplayer else None

        self.fall_time = 0
        self.fall_speed = 1000  # 초기 낙하 속도 (1초) - 500에서 1000으로 증가
        self.game_start_time = pygame.time.get_ticks()  # 게임 시작 시간
        self.time_limit = 60 if not is_multiplayer else None  # 멀티플레이는 시간 제한 없음

        # 테트리오 점수 시스템
        self.combo = -1  # 콤보 카운터 (-1은 콤보 없음)
        self.back_to_back = False  # Back-to-Back 활성화

        # 하드드롭 타이머 (0.5초 지속 누름 필요)
        self.down_hold_time = 0
        self.hard_drop_threshold = 500  # 0.5초 = 500ms
        self.hard_drop_triggered = False  # 이미 하드드롭 발동됨
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

        # 착지 지연 (Lock Delay)
        self.lock_delay_time = 0  # 현재 착지 지연 시간
        self.lock_delay_max = 500  # 최대 착지 지연 시간 (0.5초)
        self.is_on_ground = False  # 블록이 바닥에 닿았는지 여부
        self.lock_delay_moves = 0  # 착지 지연 중 이동 횟수
        self.lock_delay_max_moves = 15  # 최대 이동 가능 횟수

    def _refill_bag(self):
        """7개 블록을 섞어서 bag에 추가"""
        pieces = list(TETRIS_SHAPES.keys())  # ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
        random.shuffle(pieces)
        self.bag.extend(pieces)

    def _get_next_piece(self):
        """next_pieces에서 다음 블록을 가져오고 새 블록을 추가"""
        # next_pieces가 비어있으면 리필
        if len(self.next_pieces) == 0:
            self._refill_next_pieces()

        # next_pieces에서 첫 번째 블록을 꺼내서 사용
        shape_name = self.next_pieces.pop(0)
        block = TetrisBlock(shape_name)

        # bag에서 새 블록을 next_pieces 끝에 추가
        if len(self.bag) == 0:
            self._refill_bag()
        self.next_pieces.append(self.bag.pop(0))

        return block

    def _refill_next_pieces(self):
        """처음 시작할 때 next_pieces를 5개로 채움 (미리보기용)"""
        while len(self.next_pieces) < 5:
            if len(self.bag) == 0:
                self._refill_bag()
            self.next_pieces.append(self.bag.pop(0))

    def new_block(self):
        """7bag 시스템으로 새로운 블록 생성 (하위 호환성을 위해 유지)"""
        return self._get_next_piece()
    
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
        self.current_block = self._get_next_piece()
        self.can_hold = True  # 새 블록이 나오면 다시 홀드 가능

        # 키 상태 초기화 (가속 버그 수정)
        self.key_pressed = {
            'left': False,
            'right': False,
            'down': False
        }
        self.key_timers = {
            'left': 0,
            'right': 0,
            'down': 0
        }

        # 게임 오버 확인
        if not self.valid_position():
            self.game_over = True
            if not self.is_multiplayer:
                self.leaderboard = LeaderboardManager.update(GAME_TETRIS, self.score, student_id=CURRENT_STUDENT_ID)
    
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
            # 좌우 이동 시 착지 지연 리셋 (이동 횟수 제한 적용)
            if dx != 0 and self.is_on_ground and self.lock_delay_moves < self.lock_delay_max_moves:
                self.lock_delay_time = 0
                self.lock_delay_moves += 1
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
                    # 회전 성공 시 착지 지연 리셋
                    if self.is_on_ground and self.lock_delay_moves < self.lock_delay_max_moves:
                        self.lock_delay_time = 0
                        self.lock_delay_moves += 1
                    return
            # 벽 킥 실패시 원래 모양으로
            self.current_block.shape = original_shape
        else:
            # 회전 성공 시 착지 지연 리셋
            if self.is_on_ground and self.lock_delay_moves < self.lock_delay_max_moves:
                self.lock_delay_time = 0
                self.lock_delay_moves += 1
    
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
            self.current_block = self._get_next_piece()
        else:
            # 이미 홀드된 블록이 있는 경우 교환
            temp = self.hold_block
            self.hold_block = self.current_block.shape_name
            self.current_block = TetrisBlock(temp)

        # 키 상태 초기화 (가속 버그 수정)
        self.key_pressed = {
            'left': False,
            'right': False,
            'down': False
        }
        self.key_timers = {
            'left': 0,
            'right': 0,
            'down': 0
        }

        # 위치 초기화
        if not self.valid_position():
            self.game_over = True
            if not self.is_multiplayer:
                self.leaderboard = LeaderboardManager.update(GAME_TETRIS, self.score, student_id=CURRENT_STUDENT_ID)
    
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

        # 시간 제한 확인 (싱글플레이만)
        if not self.is_multiplayer:
            elapsed_seconds = (pygame.time.get_ticks() - self.game_start_time) / 1000
            if elapsed_seconds >= self.time_limit:
                self.game_over = True
                self.leaderboard = LeaderboardManager.update(GAME_TETRIS, self.score, student_id=CURRENT_STUDENT_ID)
                return

            # 시간에 따른 낙하 속도 증가 (1분 안에 점점 빨라짐, 최소 300ms)
            speed_multiplier = max(0.3, 1.0 - (elapsed_seconds / 60) * 0.5)  # 1분(60초)동안 점점 빨라짐
            current_fall_speed = max(300, int(1000 * speed_multiplier))
        else:
            # 멀티플레이는 고정 속도
            current_fall_speed = 500
        
        # 블록이 바닥에 닿았는지 확인
        if not self.valid_position(offset_y=1):
            # 바닥에 닿음
            if not self.is_on_ground:
                # 처음 바닥에 닿았을 때 초기화
                self.is_on_ground = True
                self.lock_delay_time = 0
                self.lock_delay_moves = 0

            # 착지 지연 타이머 증가
            self.lock_delay_time += dt

            # 착지 지연 시간이 최대치에 도달하거나 이동 횟수 초과시 블록 고정
            if self.lock_delay_time >= self.lock_delay_max or self.lock_delay_moves >= self.lock_delay_max_moves:
                self.lock_block()
                self.is_on_ground = False
                self.lock_delay_time = 0
                self.lock_delay_moves = 0
        else:
            # 바닥에서 떨어짐 (이동 후)
            self.is_on_ground = False
            self.lock_delay_time = 0
            self.lock_delay_moves = 0

            # 자동 낙하
            self.fall_time += dt
            if self.fall_time >= current_fall_speed:
                self.fall_time = 0
                self.move(0, 1)
        
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

        # 타이머 표시
        elapsed_seconds = (pygame.time.get_ticks() - self.game_start_time) / 1000
        remaining_time = max(0, self.time_limit - elapsed_seconds)
        timer_color = COLORS['red'] if remaining_time <= 10 else COLORS['font']
        WINDOW.blit(FONTS['small'].render("시간:", True, timer_color), (GAME_WIDTH + 10, y))
        WINDOW.blit(FONTS['small'].render(f"{int(remaining_time)}초", True, timer_color), (GAME_WIDTH + 10, y + 25))
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

        # 다음 블록 4개 미리보기
        WINDOW.blit(FONTS['small'].render("다음:", True, COLORS['font']), (GAME_WIDTH + 10, y))
        y += 30

        preview_size = 15  # 4개를 보여주기 위해 크기 축소
        for i, shape_name in enumerate(self.next_pieces[:4]):  # 최대 4개
            next_shape = TETRIS_SHAPES[shape_name]
            next_color = TETRIS_COLORS[shape_name]

            # 각 블록 그리기
            for py, row in enumerate(next_shape):
                for px, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            GAME_WIDTH + 30 + px * preview_size,
                            y + py * preview_size,
                            preview_size - 2,
                            preview_size - 2
                        )
                        pygame.draw.rect(WINDOW, next_color, rect)
                        pygame.draw.rect(WINDOW, COLORS['white'], rect, 1)

            # 다음 블록으로 이동 (블록 높이 + 간격)
            y += len(next_shape) * preview_size + 15

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

def run_tetris_mode_select():
    """테트리스 모드 선택 화면"""
    clock = pygame.time.Clock()

    # 버튼
    single_btn = pygame.Rect(WIDTH//2 - 200, 250, 400, 60)
    multi_btn = pygame.Rect(WIDTH//2 - 200, 330, 400, 60)
    back_btn = pygame.Rect(WIDTH//2 - 200, 410, 400, 60)

    while True:
        clock.tick(FPS)
        WINDOW.fill(COLORS['bg'])

        # 제목
        title = FONTS['large'].render("테트리스", True, COLORS['font'])
        title_rect = title.get_rect(center=(WIDTH//2, 150))
        WINDOW.blit(title, title_rect)

        # 버튼 그리기
        mouse_pos = pygame.mouse.get_pos()

        # 싱글플레이 버튼
        color = COLORS['outline'] if single_btn.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(WINDOW, color, single_btn, border_radius=10)
        pygame.draw.rect(WINDOW, COLORS['font'], single_btn, 3, border_radius=10)
        single_text = FONTS['medium'].render("싱글플레이", True, COLORS['font'])
        single_rect = single_text.get_rect(center=single_btn.center)
        WINDOW.blit(single_text, single_rect)

        # 멀티플레이 버튼
        color = COLORS['outline'] if multi_btn.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(WINDOW, color, multi_btn, border_radius=10)
        pygame.draw.rect(WINDOW, COLORS['font'], multi_btn, 3, border_radius=10)
        multi_text = FONTS['medium'].render("멀티플레이 (로컬 네트워크)", True, COLORS['font'])
        multi_rect = multi_text.get_rect(center=multi_btn.center)
        WINDOW.blit(multi_text, multi_rect)

        # 뒤로가기 버튼
        color = COLORS['outline'] if back_btn.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(WINDOW, color, back_btn, border_radius=10)
        pygame.draw.rect(WINDOW, COLORS['font'], back_btn, 3, border_radius=10)
        back_text = FONTS['medium'].render("뒤로가기", True, COLORS['font'])
        back_rect = back_text.get_rect(center=back_btn.center)
        WINDOW.blit(back_text, back_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return MENU
                elif event.key == pygame.K_1:
                    # 학번 입력
                    student_input = StudentIDInput()
                    result = student_input.run()
                    if result:
                        global CURRENT_STUDENT_ID
                        CURRENT_STUDENT_ID = result
                        return GAME_TETRIS
                elif event.key == pygame.K_2:
                    return TETRIS_MULTI

            if event.type == pygame.MOUSEBUTTONDOWN:
                if single_btn.collidepoint(event.pos):
                    # 학번 입력
                    student_input = StudentIDInput()
                    result = student_input.run()
                    if result:
                        CURRENT_STUDENT_ID = result
                        return GAME_TETRIS
                elif multi_btn.collidepoint(event.pos):
                    return TETRIS_MULTI
                elif back_btn.collidepoint(event.pos):
                    return MENU

def run_tetris():
    """테트리스 게임 실행"""
    game = Tetris()
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(FPS)

        # 게임 오버 후 5초 자동 메뉴 복귀
        if game.game_over:
            game.game_over_timer += 1
            if game.game_over_timer >= 300:  # 5초 (60 FPS * 5)
                return MENU

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            result = game.handle_event(event)
            if result != GAME_TETRIS:
                return result

        game.update(dt)
        game.draw()

# ==================== 테트리스 멀티플레이 (Tetrio 스타일) ====================

# Tetrio 공격 데미지 테이블
TETRIO_ATTACK_TABLE = {
    'single': 0,      # 1줄 클리어
    'double': 1,      # 2줄 클리어
    'triple': 2,      # 3줄 클리어
    'tetris': 4,      # 4줄 클리어 (Tetris)
    't_spin_mini': 0,
    't_spin_single': 2,
    't_spin_double': 4,
    't_spin_triple': 6,
    'b2b_bonus': 1,   # Back-to-Back 보너스
    'combo_table': [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5],  # 콤보 보너스
    'all_clear': 10   # Perfect Clear
}

class NetworkManager:
    """네트워크 통신 관리 클래스 (4인용 서버-클라이언트)"""
    def __init__(self, is_server=True, host='0.0.0.0', port=5555):
        self.is_server = is_server
        self.host = host if not is_server else '0.0.0.0'  # 서버는 모든 인터페이스에서 수신
        self.port = port
        self.socket = None
        self.clients = []  # 서버: 연결된 클라이언트들
        self.connection = None  # 클라이언트: 서버 연결
        self.connected = False
        self.received_data = []  # 여러 클라이언트의 데이터
        self.lock = threading.Lock()
        self.player_id = 0  # 내 플레이어 ID (0-3)
        self.last_heartbeat = pygame.time.get_ticks()  # 마지막 하트비트 시간
        self.heartbeat_interval = 1000  # 하트비트 간격 (1초로 단축)
        self.client_heartbeats = {}  # 클라이언트별 마지막 하트비트 시간

    def _send_data_with_length(self, conn, data):
        """데이터 크기를 먼저 전송한 후 데이터 전송"""
        try:
            pickled = pickle.dumps(data)
            length = len(pickled)
            # 4바이트로 길이 전송
            conn.sendall(length.to_bytes(4, byteorder='big'))
            # 실제 데이터 전송
            conn.sendall(pickled)
            return True
        except Exception as e:
            print(f"데이터 전송 실패: {e}")
            return False

    def _recv_data_with_length(self, conn):
        """데이터 크기를 먼저 받은 후 완전한 데이터 수신"""
        try:
            # 4바이트 길이 정보 수신
            length_bytes = b''
            while len(length_bytes) < 4:
                chunk = conn.recv(4 - len(length_bytes))
                if not chunk:
                    return None
                length_bytes += chunk

            length = int.from_bytes(length_bytes, byteorder='big')

            # 전체 데이터 수신
            data = b''
            while len(data) < length:
                chunk = conn.recv(min(65536, length - len(data)))
                if not chunk:
                    return None
                data += chunk

            return pickle.loads(data)
        except Exception as e:
            raise e

    def start_server(self):
        """서버 시작 (최대 3명의 클라이언트)"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # TCP Keep-Alive
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Nagle 알고리즘 비활성화 (지연 감소)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)  # 송신 버퍼 128KB
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)  # 수신 버퍼 128KB
            self.socket.bind((self.host, self.port))
            self.socket.listen(3)  # 최대 3명
            self.socket.settimeout(0.5)  # 타임아웃 증가 (0.1초 -> 0.5초)
            self.connected = True
            self.player_id = 0  # 서버는 플레이어 0
            return True
        except Exception as e:
            print(f"서버 시작 실패: {e}")
            return False

    def accept_connection(self):
        """클라이언트 연결 수락 (최대 3명)"""
        if len(self.clients) >= 3:
            return False

        try:
            conn, addr = self.socket.accept()
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # TCP Keep-Alive
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Nagle 알고리즘 비활성화
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)  # 송신 버퍼 128KB
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)  # 수신 버퍼 128KB
            conn.settimeout(0.5)  # 타임아웃 증가
            player_id = len(self.clients) + 1
            self.clients.append({'conn': conn, 'id': player_id, 'addr': addr})
            self.client_heartbeats[player_id] = pygame.time.get_ticks()

            # 플레이어 ID 전송
            self._send_data_with_length(conn, {'type': 'player_id', 'id': player_id})

            # 수신 스레드 시작
            threading.Thread(target=self._receive_loop_client, args=(conn, player_id), daemon=True).start()
            return True
        except socket.timeout:
            return False
        except:
            return False

    def connect_to_server(self):
        """서버에 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # TCP Keep-Alive
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Nagle 알고리즘 비활성화
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)  # 송신 버퍼 128KB
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)  # 수신 버퍼 128KB
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(0.5)  # 타임아웃 증가
            self.connection = self.socket
            self.connected = True

            # 플레이어 ID 수신
            msg = self._recv_data_with_length(self.connection)
            if msg and msg['type'] == 'player_id':
                self.player_id = msg['id']

            threading.Thread(target=self._receive_loop_server, daemon=True).start()
            return True
        except socket.timeout:
            print(f"서버 연결 시간 초과: {self.host}:{self.port}")
            return False
        except ConnectionRefusedError:
            print(f"서버 연결 거부됨: {self.host}:{self.port} (서버가 실행 중인지 확인하세요)")
            return False
        except Exception as e:
            print(f"서버 연결 실패: {e}")
            return False

    def _receive_loop_server(self):
        """서버로부터 데이터 수신 (클라이언트용)"""
        while self.connected:
            try:
                msg = self._recv_data_with_length(self.connection)
                if msg:
                    # 하트비트 응답 처리
                    if isinstance(msg, dict) and msg.get('type') == 'heartbeat':
                        continue
                    with self.lock:
                        self.received_data = msg
                else:
                    # 연결 끊김
                    print("서버 연결 끊김 감지")
                    self.connected = False
                    break
            except socket.timeout:
                continue
            except Exception as e:
                print(f"클라이언트 수신 에러: {e}")
                self.connected = False
                break

    def _receive_loop_client(self, conn, player_id):
        """클라이언트로부터 데이터 수신 (서버용)"""
        while self.connected:
            try:
                msg = self._recv_data_with_length(conn)
                if msg:
                    # 하트비트 응답 처리
                    if isinstance(msg, dict) and msg.get('type') == 'heartbeat':
                        self.client_heartbeats[player_id] = pygame.time.get_ticks()
                        continue
                    msg['player_id'] = player_id
                    with self.lock:
                        self.received_data.append(msg)
                    self.client_heartbeats[player_id] = pygame.time.get_ticks()
                else:
                    # 연결 끊김
                    print(f"플레이어 {player_id} 연결 끊김 감지")
                    with self.lock:
                        self.clients = [c for c in self.clients if c['id'] != player_id]
                        if player_id in self.client_heartbeats:
                            del self.client_heartbeats[player_id]
                    break
            except socket.timeout:
                continue
            except Exception as e:
                print(f"플레이어 {player_id} 수신 에러: {e}")
                # 클라이언트 연결 끊김
                with self.lock:
                    self.clients = [c for c in self.clients if c['id'] != player_id]
                    if player_id in self.client_heartbeats:
                        del self.client_heartbeats[player_id]
                break

    def send_heartbeat(self):
        """하트비트 전송 (연결 확인용)"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_heartbeat >= self.heartbeat_interval:
            self.last_heartbeat = current_time
            try:
                heartbeat_msg = {'type': 'heartbeat'}
                if self.is_server:
                    # 서버: 모든 클라이언트에게 하트비트 전송
                    for client in self.clients[:]:
                        if not self._send_data_with_length(client['conn'], heartbeat_msg):
                            # 전송 실패 시 클라이언트 제거
                            print(f"플레이어 {client['id']} 하트비트 전송 실패")
                            with self.lock:
                                self.clients = [c for c in self.clients if c['id'] != client['id']]
                                if client['id'] in self.client_heartbeats:
                                    del self.client_heartbeats[client['id']]
                else:
                    # 클라이언트: 서버로 하트비트 전송
                    if not self._send_data_with_length(self.connection, heartbeat_msg):
                        self.connected = False
            except Exception as e:
                print(f"하트비트 전송 실패: {e}")
                self.connected = False

    def check_connection_timeout(self):
        """연결 타임아웃 확인 (5초)"""
        if not self.is_server:
            return

        current_time = pygame.time.get_ticks()
        timeout_threshold = 5000  # 5초로 단축

        disconnected_clients = []
        for client in self.clients[:]:
            player_id = client['id']
            last_hb = self.client_heartbeats.get(player_id, 0)
            if current_time - last_hb > timeout_threshold:
                print(f"플레이어 {player_id} 타임아웃")
                disconnected_clients.append(player_id)

        if disconnected_clients:
            with self.lock:
                for player_id in disconnected_clients:
                    self.clients = [c for c in self.clients if c['id'] != player_id]
                    if player_id in self.client_heartbeats:
                        del self.client_heartbeats[player_id]

    def send_data(self, data):
        """데이터 전송"""
        if not self.connected:
            return False

        try:
            data['player_id'] = self.player_id

            if self.is_server:
                # 서버: 모든 클라이언트에게 브로드캐스트
                for client in self.clients[:]:
                    if not self._send_data_with_length(client['conn'], data):
                        print(f"플레이어 {client['id']} 전송 실패")
                        # 전송 실패 시 연결 끊김으로 처리하지 않음 (하트비트에서 처리)
            else:
                # 클라이언트: 서버로 전송
                if not self._send_data_with_length(self.connection, data):
                    self.connected = False
                    return False
            return True
        except Exception as e:
            print(f"데이터 전송 실패: {e}")
            self.connected = False
            return False

    def get_received_data(self):
        """수신된 데이터 가져오기"""
        with self.lock:
            data = self.received_data
            if self.is_server:
                self.received_data = []
            else:
                self.received_data = None
            return data

    def get_player_count(self):
        """현재 플레이어 수"""
        if self.is_server:
            return len(self.clients) + 1  # 클라이언트 + 서버
        return 0

    def close(self):
        """연결 종료"""
        self.connected = False

        if self.is_server:
            for client in self.clients:
                try:
                    client['conn'].close()
                except:
                    pass
            self.clients = []

        if self.connection:
            try:
                self.connection.close()
            except:
                pass

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

class MultiPlayerTetris:
    """멀티플레이 테트리스 게임 (4인 Tetrio 스타일)"""
    def __init__(self, network_manager, player_count=2):
        self.network = network_manager
        self.my_id = network_manager.player_id
        self.player_count = player_count  # 실제 연결된 플레이어 수

        # 4명의 게임 상태
        self.games = [Tetris(is_multiplayer=True) for _ in range(4)]
        self.player_alive = [i < player_count for i in range(4)]  # 연결된 플레이어만 alive
        self.player_connected = [i < player_count for i in range(4)]  # 연결 상태
        self.player_names = ["P1", "P2", "P3", "P4"]
        self.player_rank = [0, 0, 0, 0]  # 순위 (0 = 아직 게임 중)

        self.game_over = False
        self.my_rank = 0
        self.finish_count = 0

        # 공격 시스템
        self.pending_garbage = [0, 0, 0, 0]  # 각 플레이어가 받을 쓰레기
        self.attack_animations = []  # 공격 애니메이션 [(from, to, damage, timer)]

        # 타겟팅 시스템 (3명 이상일 때 사용)
        self.current_target = self._get_next_target()  # 현재 공격 대상
        self.target_change_timer = 0  # 타겟 변경 타이머
        self.target_change_interval = 2000  # 2초마다 타겟 변경
        self.target_changed_flash = 0  # 타겟 변경 시 플래시 효과

        # 서버용: 모든 플레이어 상태 저장
        self.all_player_states = {}

    def _get_next_target(self):
        """다음 공격 대상 선택"""
        alive = [i for i in range(self.player_count) if self.player_alive[i] and i != self.my_id]
        if alive:
            return random.choice(alive)
        return None

    def _get_all_targets(self):
        """모든 살아있는 상대 반환"""
        return [i for i in range(self.player_count) if self.player_alive[i] and i != self.my_id]

    def calculate_attack_damage(self, lines_cleared):
        """공격 데미지 계산 - 지운 라인의 절반 (올림)"""
        if lines_cleared == 0:
            return 0
        # 지운 라인의 절반 (최소 1)
        return max(1, (lines_cleared + 1) // 2)

    def add_garbage_lines(self, player_id, count):
        """쓰레기 줄 추가"""
        game = self.games[player_id]
        for _ in range(count):
            game.grid.pop(0)
            hole_pos = random.randint(0, TETRIS_GRID_WIDTH - 1)
            garbage = [COLORS['dark_gray'] if i != hole_pos else 0 for i in range(TETRIS_GRID_WIDTH)]
            game.grid.append(garbage)

    def update(self, dt):
        """게임 업데이트"""
        if self.game_over:
            return

        # 하트비트 전송
        self.network.send_heartbeat()

        # 연결 타임아웃 확인 (서버만)
        self.network.check_connection_timeout()

        my_game = self.games[self.my_id]

        # 타겟팅 시스템 업데이트 (3명 이상일 때)
        if self.player_count >= 3:
            self.target_change_timer += dt
            if self.target_changed_flash > 0:
                self.target_changed_flash -= dt

            if self.target_change_timer >= self.target_change_interval:
                self.target_change_timer = 0
                # 현재 타겟이 죽었거나 타이머 만료시 새 타겟 선택
                alive_targets = self._get_all_targets()
                if alive_targets:
                    old_target = self.current_target
                    # 현재 타겟 제외하고 선택 (가능하면)
                    other_targets = [t for t in alive_targets if t != self.current_target]
                    if other_targets:
                        self.current_target = random.choice(other_targets)
                    elif alive_targets:
                        self.current_target = random.choice(alive_targets)
                    # 타겟이 바뀌었으면 플래시 효과
                    if old_target != self.current_target:
                        self.target_changed_flash = 500  # 0.5초 플래시

            # 현재 타겟이 죽었으면 즉시 변경
            if self.current_target is not None and not self.player_alive[self.current_target]:
                self.current_target = self._get_next_target()
                self.target_changed_flash = 500

        # 내 게임 오버 체크
        if my_game.game_over and self.player_alive[self.my_id]:
            self.player_alive[self.my_id] = False
            self.finish_count += 1
            self.player_rank[self.my_id] = self.player_count - self.finish_count + 1
            self.my_rank = self.player_rank[self.my_id]

        # 생존자 1명 남으면 게임 종료 (매 프레임 체크)
        alive_count = sum(1 for i in range(self.player_count) if self.player_alive[i])
        if alive_count <= 1 and not self.game_over:
            self.game_over = True
            # 마지막 생존자에게 1등 부여
            for i in range(self.player_count):
                if self.player_alive[i] and self.player_rank[i] == 0:
                    self.player_rank[i] = 1
                    if i == self.my_id:
                        self.my_rank = 1

        # 내 게임 업데이트 (살아있을 때만)
        prev_lines = my_game.lines_cleared
        if self.player_alive[self.my_id]:
            my_game.update(dt)

        # 공격 계산
        attack_damage = 0
        attack_target = None
        if my_game.lines_cleared > prev_lines:
            cleared = my_game.lines_cleared - prev_lines
            attack_damage = self.calculate_attack_damage(cleared)
            # 2명일 때는 상대에게, 3명 이상일 때는 현재 타겟에게
            if self.player_count == 2:
                targets = self._get_all_targets()
                attack_target = targets[0] if targets else None
            else:
                attack_target = self.current_target

        # 쓰레기 줄 추가
        if self.pending_garbage[self.my_id] > 0:
            self.add_garbage_lines(self.my_id, self.pending_garbage[self.my_id])
            self.pending_garbage[self.my_id] = 0

        # 현재 블록 정보도 포함
        current_block_data = None
        if my_game.current_block:
            current_block_data = {
                'shape': my_game.current_block.shape,
                'color': my_game.current_block.color,
                'x': my_game.current_block.x,
                'y': my_game.current_block.y
            }

        # 데이터 송수신
        state = {
            'type': 'game_state',
            'grid': my_game.grid,
            'score': my_game.score,
            'lines': my_game.lines_cleared,
            'combo': my_game.combo,
            'game_over': my_game.game_over,
            'attack': attack_damage,
            'attack_target': attack_target,
            'rank': self.player_rank[self.my_id],
            'current_block': current_block_data,
            'my_target': self.current_target  # 내 현재 타겟 정보
        }

        if self.network.is_server:
            # 서버: 자신의 상태 저장
            self.all_player_states[self.my_id] = state

            # 클라이언트 데이터 수신 및 저장
            data = self.network.get_received_data()
            if data:
                for msg in data:
                    pid = msg.get('player_id', 0)
                    if pid != self.my_id and msg.get('type') == 'game_state':
                        self.all_player_states[pid] = msg
                        self._process_player_data(msg)

            # 모든 플레이어 상태를 브로드캐스트
            broadcast_data = {
                'type': 'broadcast',
                'states': self.all_player_states,
                'player_count': self.player_count
            }
            self.network.send_data(broadcast_data)
        else:
            # 클라이언트: 자신의 상태를 서버로 전송
            self.network.send_data(state)

            # 서버로부터 브로드캐스트 데이터 수신
            data = self.network.get_received_data()
            if data and isinstance(data, dict):
                if data.get('type') == 'broadcast':
                    states = data.get('states', {})
                    for pid_str, player_state in states.items():
                        pid = int(pid_str) if isinstance(pid_str, str) else pid_str
                        if pid != self.my_id and player_state.get('type') == 'game_state':
                            self._process_player_data(player_state, pid)
                    # 플레이어 수 업데이트
                    self.player_count = data.get('player_count', self.player_count)

        # 공격 애니메이션 업데이트
        self.attack_animations = [(f, t, d, tm-1) for f, t, d, tm in self.attack_animations if tm > 1]

    def _process_player_data(self, data, override_pid=None):
        """플레이어 데이터 처리"""
        pid = override_pid if override_pid is not None else data.get('player_id', 0)
        if pid == self.my_id or pid >= 4:
            return

        game = self.games[pid]
        if 'grid' in data:
            game.grid = [row[:] for row in data['grid']]
        game.score = data.get('score', 0)
        game.lines_cleared = data.get('lines', 0)
        game.combo = data.get('combo', -1)

        # 현재 블록 정보 업데이트
        current_block_data = data.get('current_block')
        if current_block_data:
            # 임시 블록 객체 생성 (표시용)
            class TempBlock:
                def __init__(self, shape, color, x, y):
                    self.shape = shape
                    self.color = color
                    self.x = x
                    self.y = y
            game.current_block = TempBlock(
                current_block_data['shape'],
                tuple(current_block_data['color']) if isinstance(current_block_data['color'], list) else current_block_data['color'],
                current_block_data['x'],
                current_block_data['y']
            )

        # 연결 상태 업데이트
        self.player_connected[pid] = True

        # 공격 받기 (타겟팅 시스템 적용)
        attack = data.get('attack', 0)
        attack_target = data.get('attack_target')
        if attack > 0 and attack_target is not None:
            # 지정된 타겟에게만 공격
            if attack_target == self.my_id and self.player_alive[self.my_id]:
                self.pending_garbage[self.my_id] += attack
                self.attack_animations.append((pid, self.my_id, attack, 60))

        # 탈락 체크
        if data.get('game_over') and self.player_alive[pid]:
            self.player_alive[pid] = False
            self.finish_count += 1
            self.player_rank[pid] = self.player_count - self.finish_count + 1

    def handle_event(self, event):
        """이벤트 처리"""
        return self.games[self.my_id].handle_event(event)

    def draw(self):
        """화면 그리기 (본인: 왼쪽 크게, 다른 플레이어: 오른쪽 작게)"""
        WINDOW.fill((20, 20, 30))  # 어두운 배경

        # 본인 게임 화면 (왼쪽, 크게) - 기존 싱글플레이어 크기
        main_x = 50
        main_y = 50
        main_block_size = TETRIS_BLOCK_SIZE  # 30

        # 다른 플레이어 화면 (오른쪽, 작게)
        side_x = GAME_WIDTH + 30
        side_y = 30

        # 플레이어 수에 따라 블록 크기와 간격 조정
        other_count = self.player_count - 1  # 나를 제외한 플레이어 수
        if other_count <= 1:
            side_block_size = 12
            side_spacing = 280
        elif other_count == 2:
            side_block_size = 10
            side_spacing = 230
        else:
            side_block_size = 8
            side_spacing = 185

        # 색상
        colors = [COLORS['cyan'], COLORS['orange'], COLORS['lime'], COLORS['pink']]

        # 본인 화면 그리기 (크게)
        my_game = self.games[self.my_id]
        self._draw_main_player(my_game, (main_x, main_y), self.my_id, colors[self.my_id])

        # 다른 플레이어들 화면 그리기 (연결된 플레이어만, 오른쪽에 세로로)
        side_idx = 0
        for i in range(self.player_count):
            if i != self.my_id:
                pos = (side_x, side_y + side_idx * side_spacing)
                self._draw_small_player(self.games[i], pos, i, colors[i], side_block_size)
                side_idx += 1

        # 관전 모드 표시 (내가 죽었지만 게임이 아직 안 끝났을 때)
        if not self.player_alive[self.my_id] and not self.game_over:
            # 반투명 오버레이
            overlay = pygame.Surface((GAME_WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            WINDOW.blit(overlay, (0, 0))

            # 관전 중 메시지
            spectate_text = FONTS['large'].render("관전 중", True, COLORS['white'])
            spectate_rect = spectate_text.get_rect(center=(GAME_WIDTH//2 + 50, HEIGHT//2 - 30))
            WINDOW.blit(spectate_text, spectate_rect)

            # 순위 표시
            rank_text = ["1st", "2nd", "3rd", "4th"]
            if self.my_rank > 0 and self.my_rank <= len(rank_text):
                rank_msg = FONTS['medium'].render(f"당신의 순위: {rank_text[self.my_rank-1]}", True, COLORS['yellow'])
                rank_rect = rank_msg.get_rect(center=(GAME_WIDTH//2 + 50, HEIGHT//2 + 20))
                WINDOW.blit(rank_msg, rank_rect)

        # 게임 오버 시 순위 표시
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            WINDOW.blit(overlay, (0, 0))

            # 순위 표시
            rank_colors = [COLORS['gold'], (192, 192, 192), (205, 127, 50), COLORS['white']]
            rank_text = ["1st", "2nd", "3rd", "4th"]

            if self.my_rank > 0 and self.my_rank <= len(rank_text):
                title = FONTS['large'].render(f"순위: {rank_text[self.my_rank-1]}", True, rank_colors[self.my_rank-1])
                title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
                WINDOW.blit(title, title_rect)

            # 전체 순위
            y_offset = HEIGHT//2
            for i in range(self.player_count):
                if self.player_rank[i] > 0:
                    rank_idx = self.player_rank[i] - 1
                    if rank_idx < len(rank_text):
                        player_text = f"{rank_text[rank_idx]} - Player {i+1}"
                        color = rank_colors[rank_idx] if i == self.my_id else COLORS['white']
                        text = FONTS['small'].render(player_text, True, color)
                        text_rect = text.get_rect(center=(WIDTH//2, y_offset + rank_idx * 30))
                        WINDOW.blit(text, text_rect)

            sub_text = FONTS['small'].render("ESC: 메뉴로", True, COLORS['white'])
            sub_rect = sub_text.get_rect(center=(WIDTH//2, HEIGHT - 50))
            WINDOW.blit(sub_text, sub_rect)

        pygame.display.update()

    def _draw_main_player(self, game, pos, player_id, color):
        """본인 화면 그리기 (크게, 싱글플레이어 스타일)"""
        x, y = pos
        block_size = TETRIS_BLOCK_SIZE  # 30
        grid_width = TETRIS_GRID_WIDTH * block_size
        grid_height = TETRIS_GRID_HEIGHT * block_size

        # 그리드 배경
        grid_rect = pygame.Rect(x, y, grid_width, grid_height)
        pygame.draw.rect(WINDOW, (40, 40, 40), grid_rect)

        # 그리드 선
        for gx in range(TETRIS_GRID_WIDTH + 1):
            pygame.draw.line(WINDOW, (60, 60, 60),
                           (x + gx * block_size, y),
                           (x + gx * block_size, y + grid_height))
        for gy in range(TETRIS_GRID_HEIGHT + 1):
            pygame.draw.line(WINDOW, (60, 60, 60),
                           (x, y + gy * block_size),
                           (x + grid_width, y + gy * block_size))

        # 고정된 블록들
        for row in range(TETRIS_GRID_HEIGHT):
            for col in range(TETRIS_GRID_WIDTH):
                if game.grid[row][col]:
                    rect = pygame.Rect(
                        x + col * block_size + 1,
                        y + row * block_size + 1,
                        block_size - 2,
                        block_size - 2
                    )
                    pygame.draw.rect(WINDOW, game.grid[row][col], rect)
                    pygame.draw.rect(WINDOW, COLORS['white'], rect, 2)

        # 현재 블록
        if not game.game_over and game.current_block:
            for row, line in enumerate(game.current_block.shape):
                for col, cell in enumerate(line):
                    if cell:
                        rect = pygame.Rect(
                            x + (game.current_block.x + col) * block_size + 1,
                            y + (game.current_block.y + row) * block_size + 1,
                            block_size - 2,
                            block_size - 2
                        )
                        pygame.draw.rect(WINDOW, game.current_block.color, rect)
                        pygame.draw.rect(WINDOW, COLORS['white'], rect, 2)

        # 테두리
        pygame.draw.rect(WINDOW, color, grid_rect, 4)

        # 우측 패널 정보
        panel_x = x + grid_width + 20
        panel_y = y

        # 플레이어 정보
        name_text = FONTS['medium'].render(f"P{player_id+1} (YOU)", True, color)
        WINDOW.blit(name_text, (panel_x, panel_y))
        panel_y += 40

        # 생존 플레이어 수
        alive_count = sum(1 for i in range(self.player_count) if self.player_alive[i])
        alive_text = FONTS['small'].render(f"생존: {alive_count}/{self.player_count}", True, COLORS['font'])
        WINDOW.blit(alive_text, (panel_x, panel_y))
        panel_y += 35

        # 홀드 블록 표시
        WINDOW.blit(FONTS['small'].render("홀드 [C]:", True, COLORS['font']), (panel_x, panel_y))
        panel_y += 25
        if game.hold_block:
            hold_shape = TETRIS_SHAPES[game.hold_block]
            hold_color = TETRIS_COLORS[game.hold_block]
            preview_size = 15
            for py, row in enumerate(hold_shape):
                for px, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            panel_x + px * preview_size,
                            panel_y + py * preview_size,
                            preview_size - 2,
                            preview_size - 2
                        )
                        color_to_use = hold_color if game.can_hold else (80, 80, 80)
                        pygame.draw.rect(WINDOW, color_to_use, rect)
                        pygame.draw.rect(WINDOW, COLORS['white'], rect, 1)
            panel_y += len(hold_shape) * preview_size + 10
        else:
            empty_text = FONTS['tiny'].render("비어있음", True, (100, 100, 100))
            WINDOW.blit(empty_text, (panel_x, panel_y))
            panel_y += 25
        panel_y += 10

        # 콤보
        if game.combo >= 0:
            WINDOW.blit(FONTS['small'].render("콤보:", True, COLORS['yellow']), (panel_x, panel_y))
            WINDOW.blit(FONTS['small'].render(f"x{game.combo + 1}", True, COLORS['yellow']), (panel_x, panel_y + 25))
            panel_y += 60

        # B2B
        if game.back_to_back:
            WINDOW.blit(FONTS['small'].render("B2B!", True, COLORS['gold']), (panel_x, panel_y))
            panel_y += 35

        # 대기 중인 쓰레기 줄 표시
        if self.pending_garbage[self.my_id] > 0:
            garbage_text = FONTS['small'].render(f"공격 대기: {self.pending_garbage[self.my_id]}줄", True, COLORS['red'])
            WINDOW.blit(garbage_text, (panel_x, panel_y))
            panel_y += 35

        # 다음 블록 5개 미리보기
        WINDOW.blit(FONTS['small'].render("다음:", True, COLORS['font']), (panel_x, panel_y))
        panel_y += 30

        preview_size = 15
        for i, shape_name in enumerate(game.next_pieces[:5]):
            next_shape = TETRIS_SHAPES[shape_name]
            next_color = TETRIS_COLORS[shape_name]

            for py, row in enumerate(next_shape):
                for px, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            panel_x + 20 + px * preview_size,
                            panel_y + py * preview_size,
                            preview_size - 2,
                            preview_size - 2
                        )
                        pygame.draw.rect(WINDOW, next_color, rect)
                        pygame.draw.rect(WINDOW, COLORS['white'], rect, 1)

            panel_y += len(next_shape) * preview_size + 15

    def _draw_small_player(self, game, pos, player_id, color, block_size):
        """다른 플레이어 화면 그리기 (작게)"""
        x, y = pos
        grid_width = TETRIS_GRID_WIDTH * block_size
        grid_height = TETRIS_GRID_HEIGHT * block_size

        # 타겟 여부 확인
        is_target = (self.player_count >= 3 and self.current_target == player_id and self.player_alive[player_id])

        # 배경
        bg_rect = pygame.Rect(x-5, y-5, grid_width+10, grid_height+10)
        pygame.draw.rect(WINDOW, (40, 40, 50), bg_rect, border_radius=5)

        # 게임 영역 배경
        game_rect = pygame.Rect(x, y, grid_width, grid_height)
        pygame.draw.rect(WINDOW, (30, 30, 40), game_rect)

        # 격자선 그리기
        grid_line_color = (60, 60, 70)
        for gx in range(TETRIS_GRID_WIDTH + 1):
            pygame.draw.line(WINDOW, grid_line_color,
                           (x + gx * block_size, y),
                           (x + gx * block_size, y + grid_height))
        for gy in range(TETRIS_GRID_HEIGHT + 1):
            pygame.draw.line(WINDOW, grid_line_color,
                           (x, y + gy * block_size),
                           (x + grid_width, y + gy * block_size))

        # 테두리
        pygame.draw.rect(WINDOW, color, bg_rect, 2, border_radius=5)

        # 플레이어 정보
        name = f"P{player_id+1}"
        name_text = FONTS['small'].render(name, True, color)
        WINDOW.blit(name_text, (x, y - 25))

        # 스코프 표시 (타겟일 때)
        if is_target:
            cx, cy = x + grid_width // 2, y + grid_height // 2
            scope_size = min(grid_width, grid_height) // 3
            scope_color = (255, 50, 50)
            # 원
            pygame.draw.circle(WINDOW, scope_color, (cx, cy), scope_size, 2)
            pygame.draw.circle(WINDOW, scope_color, (cx, cy), scope_size // 2, 1)
            # 십자선
            pygame.draw.line(WINDOW, scope_color, (cx - scope_size - 10, cy), (cx + scope_size + 10, cy), 2)
            pygame.draw.line(WINDOW, scope_color, (cx, cy - scope_size - 10), (cx, cy + scope_size + 10), 2)

        # 탈락 표시
        if not self.player_alive[player_id]:
            ko_text = FONTS['medium'].render("K.O.", True, COLORS['red'])
            ko_rect = ko_text.get_rect(center=(x + grid_width//2, y + grid_height//2))
            WINDOW.blit(ko_text, ko_rect)
            return

        # 그리드
        for row in range(TETRIS_GRID_HEIGHT):
            for col in range(TETRIS_GRID_WIDTH):
                cell_x = x + col * block_size
                cell_y = y + row * block_size
                if game.grid[row][col]:
                    pygame.draw.rect(WINDOW, game.grid[row][col],
                                   (cell_x+1, cell_y+1, block_size-2, block_size-2))

        # 현재 블록
        if game.current_block and not game.game_over:
            for row, line in enumerate(game.current_block.shape):
                for col, cell in enumerate(line):
                    if cell:
                        block_x = x + (game.current_block.x + col) * block_size
                        block_y = y + (game.current_block.y + row) * block_size
                        pygame.draw.rect(WINDOW, game.current_block.color,
                                       (block_x+1, block_y+1, block_size-2, block_size-2))


def run_tetris_multiplayer_setup():
    """멀티플레이 설정 화면"""
    clock = pygame.time.Clock()

    # 버튼
    server_btn = pygame.Rect(WIDTH//2 - 200, 200, 400, 60)
    client_btn = pygame.Rect(WIDTH//2 - 200, 280, 400, 60)
    back_btn = pygame.Rect(WIDTH//2 - 200, 360, 400, 60)

    # IP 입력 (클라이언트용)
    ip_input = ""
    entering_ip = False

    while True:
        clock.tick(FPS)
        WINDOW.fill(COLORS['bg'])

        # 제목
        title = FONTS['large'].render("테트리스 멀티플레이", True, COLORS['font'])
        title_rect = title.get_rect(center=(WIDTH//2, 100))
        WINDOW.blit(title, title_rect)

        # 버튼 그리기
        mouse_pos = pygame.mouse.get_pos()

        # 서버 버튼
        color = COLORS['outline'] if server_btn.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(WINDOW, color, server_btn, border_radius=10)
        pygame.draw.rect(WINDOW, COLORS['font'], server_btn, 3, border_radius=10)
        server_text = FONTS['medium'].render("서버 열기 (방 만들기)", True, COLORS['font'])
        server_rect = server_text.get_rect(center=server_btn.center)
        WINDOW.blit(server_text, server_rect)

        # 클라이언트 버튼
        color = COLORS['outline'] if client_btn.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(WINDOW, color, client_btn, border_radius=10)
        pygame.draw.rect(WINDOW, COLORS['font'], client_btn, 3, border_radius=10)
        client_text = FONTS['medium'].render("서버 접속 (방 참가)", True, COLORS['font'])
        client_rect = client_text.get_rect(center=client_btn.center)
        WINDOW.blit(client_text, client_rect)

        # 뒤로가기 버튼
        color = COLORS['outline'] if back_btn.collidepoint(mouse_pos) else COLORS['white']
        pygame.draw.rect(WINDOW, color, back_btn, border_radius=10)
        pygame.draw.rect(WINDOW, COLORS['font'], back_btn, 3, border_radius=10)
        back_text = FONTS['medium'].render("뒤로가기", True, COLORS['font'])
        back_rect = back_text.get_rect(center=back_btn.center)
        WINDOW.blit(back_text, back_rect)

        # IP 입력창 (클라이언트 모드)
        if entering_ip:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            WINDOW.blit(overlay, (0, 0))

            input_box = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 30, 400, 60)
            pygame.draw.rect(WINDOW, COLORS['white'], input_box, border_radius=10)
            pygame.draw.rect(WINDOW, COLORS['font'], input_box, 3, border_radius=10)

            prompt_text = FONTS['small'].render("서버 IP 입력 (예: 192.168.0.1)", True, COLORS['white'])
            prompt_rect = prompt_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
            WINDOW.blit(prompt_text, prompt_rect)

            ip_text = FONTS['medium'].render(ip_input, True, COLORS['font'])
            ip_rect = ip_text.get_rect(center=input_box.center)
            WINDOW.blit(ip_text, ip_rect)

            help_text = FONTS['tiny'].render("Enter: 접속 | ESC: 취소 | localhost = 같은 컴퓨터", True, COLORS['white'])
            help_rect = help_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
            WINDOW.blit(help_text, help_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if entering_ip:
                    if event.key == pygame.K_ESCAPE:
                        entering_ip = False
                        ip_input = ""
                    elif event.key == pygame.K_RETURN:
                        if ip_input:
                            return ('client', ip_input)
                        entering_ip = False
                    elif event.key == pygame.K_BACKSPACE:
                        ip_input = ip_input[:-1]
                    elif event.unicode.isprintable() and len(ip_input) < 30:
                        ip_input += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        return MENU

            if event.type == pygame.MOUSEBUTTONDOWN and not entering_ip:
                if server_btn.collidepoint(event.pos):
                    return ('server', 'localhost')
                elif client_btn.collidepoint(event.pos):
                    entering_ip = True
                    ip_input = "localhost"
                elif back_btn.collidepoint(event.pos):
                    return MENU

def _show_error_screen(message):
    """에러 화면 표시 및 대기"""
    WINDOW.fill(COLORS['bg'])
    error_text = FONTS['medium'].render(message, True, COLORS['red'])
    error_rect = error_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    WINDOW.blit(error_text, error_rect)
    help_text = FONTS['small'].render("ESC: 메뉴로", True, COLORS['font'])
    help_rect = help_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
    WINDOW.blit(help_text, help_rect)
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return MENU

def _waiting_room(network, is_server):
    """대기실 (2-4명 플레이어)"""
    clock = pygame.time.Clock()
    local_ip = "localhost"
    client_player_count = 1  # 클라이언트가 표시할 플레이어 수

    if is_server:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except:
            pass

    while True:
        clock.tick(FPS)

        if is_server:
            player_count = network.get_player_count()
            # 서버: 클라이언트들에게 플레이어 수 브로드캐스트
            network.send_data({'type': 'player_count', 'count': player_count})
        else:
            player_count = client_player_count

        # 클라이언트: 서버로부터 데이터 수신
        if not is_server:
            data = network.get_received_data()
            if data and isinstance(data, dict):
                if data.get('type') == 'game_start':
                    return data.get('player_count', 2)  # 플레이어 수 반환
                elif data.get('type') == 'player_count':
                    client_player_count = data.get('count', 1)
                    player_count = client_player_count

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                network.close()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    network.close()
                    return MENU
                # 스페이스바: 게임 시작 (서버만, 최소 2명)
                if event.key == pygame.K_SPACE and is_server and player_count >= 2:
                    # 클라이언트들에게 게임 시작 신호 전송 (플레이어 수 포함)
                    network.send_data({'type': 'game_start', 'player_count': player_count})
                    return player_count  # 플레이어 수 반환

        # 새 연결 시도 (서버만, 최대 4명)
        if is_server and player_count < 4:
            network.accept_connection()

        # 화면 그리기
        WINDOW.fill(COLORS['bg'])

        # 제목
        title = FONTS['large'].render("대기실", True, COLORS['font'])
        title_rect = title.get_rect(center=(WIDTH//2, 100))
        WINDOW.blit(title, title_rect)

        # 서버 IP (서버만)
        if is_server:
            ip_text = FONTS['medium'].render(f"서버 IP: {local_ip}", True, COLORS['blue'])
            ip_rect = ip_text.get_rect(center=(WIDTH//2, 180))
            WINDOW.blit(ip_text, ip_rect)

        # 플레이어 수
        count_text = FONTS['large'].render(f"플레이어: {player_count}/4", True, COLORS['gold'])
        count_rect = count_text.get_rect(center=(WIDTH//2, 280))
        WINDOW.blit(count_text, count_rect)

        # 상태 메시지
        if is_server:
            if player_count < 2:
                status = "플레이어 대기 중... (최소 2명 필요)"
                color = COLORS['red']
            else:
                status = "스페이스바를 눌러 게임 시작!"
                color = COLORS['green']
        else:
            status = "호스트가 게임을 시작하기를 기다리는 중..."
            color = COLORS['font']

        status_text = FONTS['medium'].render(status, True, color)
        status_rect = status_text.get_rect(center=(WIDTH//2, 380))
        WINDOW.blit(status_text, status_rect)

        # 도움말
        help_text = FONTS['small'].render("ESC: 취소", True, COLORS['font'])
        help_rect = help_text.get_rect(center=(WIDTH//2, HEIGHT - 50))
        WINDOW.blit(help_text, help_rect)

        pygame.display.update()

def run_tetris_multiplayer():
    """멀티플레이 테트리스 실행 (4인 Tetrio 스타일)"""
    # 1. 설정 화면
    setup_result = run_tetris_multiplayer_setup()
    if setup_result == MENU or setup_result is None:
        return setup_result

    mode, host = setup_result
    is_server = (mode == 'server')
    network = NetworkManager(is_server=is_server, host=host, port=5555)
    clock = pygame.time.Clock()

    # 2. 연결 시작
    WINDOW.fill(COLORS['bg'])
    status = "서버 시작 중..." if is_server else "서버 연결 중..."
    status_text = FONTS['large'].render(status, True, COLORS['font'])
    WINDOW.blit(status_text, status_text.get_rect(center=(WIDTH//2, HEIGHT//2)))
    if not is_server:
        ip_text = FONTS['medium'].render(f"IP: {host}", True, COLORS['blue'])
        WINDOW.blit(ip_text, ip_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))
    pygame.display.update()

    # 연결 시도
    success = network.start_server() if is_server else network.connect_to_server()
    if not success:
        network.close()
        return _show_error_screen("서버 시작 실패!" if is_server else "서버 연결 실패!")

    # 3. 대기실
    result = _waiting_room(network, is_server)
    if result == MENU or result is None:
        return result

    # result는 이제 플레이어 수
    player_count = result if isinstance(result, int) else 2

    # 4. 게임 시작 카운트다운
    for i in range(3, 0, -1):
        WINDOW.fill(COLORS['bg'])
        countdown_text = FONTS['large'].render(str(i), True, COLORS['gold'])
        WINDOW.blit(countdown_text, countdown_text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        pygame.display.update()
        pygame.time.delay(1000)

    # 5. 게임 루프
    game = MultiPlayerTetris(network, player_count)

    while True:
        dt = clock.tick(FPS)

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                network.close()
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                network.close()
                return MENU

            result = game.handle_event(event)
            if result not in [GAME_TETRIS, TETRIS_MULTI]:
                network.close()
                return result

        # 연결 끊김 체크
        if not network.connected:
            network.close()
            return _show_error_screen("연결이 끊어졌습니다!")

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
    game_over_timer = 0
    entering_pw, pw_input = False, ""
    start_time, elapsed = None, 0

    lb = LeaderboardManager.load(GAME_BREAKOUT, difficulty)
    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)

        # 게임 오버 후 5초 자동 메뉴 복귀
        if game_over:
            game_over_timer += 1
            if game_over_timer >= 300:  # 5초 (60 FPS * 5)
                return MENU
        
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
                lb = LeaderboardManager.update(GAME_BREAKOUT, int(elapsed), difficulty, student_id=CURRENT_STUDENT_ID)
        
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
        
        # 3라운드마다 테마 변경
        if stage <= 3:
            word_pool = WORD_POOLS['fruits']
        elif stage <= 6:
            word_pool = WORD_POOLS['fruits'] + WORD_POOLS['animals']
        elif stage <= 9:
            word_pool = WORD_POOLS['animals'] + WORD_POOLS['school']
        elif stage <= 12:
            word_pool = WORD_POOLS['school'] + WORD_POOLS['food']
        elif stage <= 15:
            word_pool = WORD_POOLS['food'] + WORD_POOLS['nature']
        elif stage <= 18:
            word_pool = WORD_POOLS['nature'] + WORD_POOLS['nature2']
        elif stage <= 21:
            word_pool = WORD_POOLS['nature2'] + WORD_POOLS['space']
        elif stage <= 24:
            word_pool = WORD_POOLS['space'] + WORD_POOLS['ocean']
        elif stage <= 27:
            word_pool = WORD_POOLS['ocean'] + WORD_POOLS['jobs']
        elif stage <= 30:
            word_pool = WORD_POOLS['jobs'] + WORD_POOLS['world']
        else:
            # 30 이상은 모든 단어 풀 사용
            word_pool = (WORD_POOLS['fruits'] + WORD_POOLS['animals'] +
                        WORD_POOLS['school'] + WORD_POOLS['food'] +
                        WORD_POOLS['nature'] + WORD_POOLS['nature2'] +
                        WORD_POOLS['space'] + WORD_POOLS['ocean'] +
                        WORD_POOLS['jobs'] + WORD_POOLS['world'])

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
    game_over_timer = 0
    entering_pw, pw_input = False, ""
    start_time, elapsed = pygame.time.get_ticks(), 0

    lb = LeaderboardManager.load(GAME_TYPING)
    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)

        # 게임 오버 후 5초 자동 메뉴 복귀
        if game_over:
            game_over_timer += 1
            if game_over_timer >= 300:  # 5초 (60 FPS * 5)
                pygame.key.stop_text_input()
                return MENU
        
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
                    spawn_delay = max(45, 90 - stage * 5)
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
                lb = LeaderboardManager.update(GAME_TYPING, score, stage=stage, student_id=CURRENT_STUDENT_ID)
        
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
        self.game_over_timer = 0
        self.entering_pw = False
        self.pw_input = ""
        self.leaderboard = LeaderboardManager.load(GAME_BLOCKBLAST)

        # 현재 사용 가능한 3개의 블록
        self.available_pieces = self.generate_new_pieces()
        self.selected_piece_idx = None
        self.dragging = False
        self.mouse_x = 0
        self.mouse_y = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # 애니메이션 및 효과
        self.clearing_rows = []  # 제거 중인 행
        self.clearing_cols = []  # 제거 중인 열
        self.clear_animation_timer = 0
        self.combo_count = 0
        self.combo_display_timer = 0
        self.perfect_display_timer = 0
        self.is_new_record = False
        self.record_display_timer = 0

        # 추가 시각 효과
        self.background_time = 0  # 배경 애니메이션용 타이머
        self.screen_shake_intensity = 0  # 화면 흔들림 강도
        self.screen_shake_timer = 0  # 화면 흔들림 타이머
        self.pulse_effects = []  # 펄스 효과 리스트 [(x, y, timer), ...]
        self.game_over_fade = 0  # 게임 오버 페이드 아웃
        self.hovered_piece_idx = None  # 호버 중인 블록 인덱스
        self.need_game_over_check = False  # 게임오버 체크 필요 플래그
    
    def new_piece(self):
        """새로운 블록 생성 (가중치 적용)"""
        # 가중치를 고려한 블록 풀 생성
        if self.score < 150:
            # 초반: 쉬운 블록만
            weighted_shapes = BLOCKBLAST_SHAPES_EASY * BLOCKBLAST_WEIGHTS['easy']
        elif self.score < 400:
            # 중반: 쉬운 블록 많이, 보통 블록 조금
            weighted_shapes = (BLOCKBLAST_SHAPES_EASY * BLOCKBLAST_WEIGHTS['easy'] +
                             BLOCKBLAST_SHAPES_NORMAL * BLOCKBLAST_WEIGHTS['normal'])
        elif self.score < 700:
            # 후반: 쉬운, 보통, L자형, 어려운 블록 균형있게
            weighted_shapes = (BLOCKBLAST_SHAPES_EASY * BLOCKBLAST_WEIGHTS['easy'] +
                             BLOCKBLAST_SHAPES_NORMAL * BLOCKBLAST_WEIGHTS['normal'] +
                             BLOCKBLAST_SHAPES_LSHAPE * BLOCKBLAST_WEIGHTS['lshape'] +
                             BLOCKBLAST_SHAPES_HARD * BLOCKBLAST_WEIGHTS['hard'])
        else:
            # 최후반: 모든 블록 (가중치 적용)
            weighted_shapes = (BLOCKBLAST_SHAPES_EASY * BLOCKBLAST_WEIGHTS['easy'] +
                             BLOCKBLAST_SHAPES_NORMAL * BLOCKBLAST_WEIGHTS['normal'] +
                             BLOCKBLAST_SHAPES_LSHAPE * BLOCKBLAST_WEIGHTS['lshape'] +
                             BLOCKBLAST_SHAPES_HARD * BLOCKBLAST_WEIGHTS['hard'])

        shape = random.choice(weighted_shapes)
        return BlockBlastPiece(shape)

    def can_place_anywhere(self, piece):
        """블록을 그리드 어디든 놓을 수 있는지 확인"""
        for r in range(BLOCKBLAST_GRID_SIZE):
            for c in range(BLOCKBLAST_GRID_SIZE):
                if self.can_place(piece, r, c):
                    return True
        return False

    def generate_new_pieces(self):
        """3개의 새 블록을 생성 (최소 1개는 설치 가능하도록 보장)"""
        MAX_ATTEMPTS = 50  # 최대 시도 횟수

        for attempt in range(MAX_ATTEMPTS):
            pieces = [self.new_piece() for _ in range(3)]

            # 최소 1개는 설치 가능한지 확인
            if any(self.can_place_anywhere(piece) for piece in pieces):
                return pieces

        # 최대 시도 횟수 초과 시, 강제로 쉬운 블록 추가
        # (이론적으로 거의 발생하지 않지만 안전장치)
        pieces = [self.new_piece(), self.new_piece()]
        easy_shape = random.choice(BLOCKBLAST_SHAPES_EASY)
        pieces.append(BlockBlastPiece(easy_shape))
        return pieces

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
        """완성된 행과 열 제거 (애니메이션 포함)"""
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

        if rows_to_clear or cols_to_clear:
            # 애니메이션 시작
            self.clearing_rows = rows_to_clear
            self.clearing_cols = cols_to_clear
            self.clear_animation_timer = 30  # 애니메이션 프레임 수 (더 길게)

            # 파티클 효과 추가 (더 화려하게)
            for r in rows_to_clear:
                for c in range(BLOCKBLAST_GRID_SIZE):
                    if self.grid[r][c] != 0:
                        x = BLOCKBLAST_OFFSET_X + c * BLOCKBLAST_CELL_SIZE + BLOCKBLAST_CELL_SIZE // 2
                        y = BLOCKBLAST_OFFSET_Y + r * BLOCKBLAST_CELL_SIZE + BLOCKBLAST_CELL_SIZE // 2
                        PARTICLE_SYSTEM.add_explosion(x, y, self.grid[r][c], count=25)
                        PARTICLE_SYSTEM.add_sparkle(x, y, count=15)

            for c in cols_to_clear:
                for r in range(BLOCKBLAST_GRID_SIZE):
                    if self.grid[r][c] != 0:
                        x = BLOCKBLAST_OFFSET_X + c * BLOCKBLAST_CELL_SIZE + BLOCKBLAST_CELL_SIZE // 2
                        y = BLOCKBLAST_OFFSET_Y + r * BLOCKBLAST_CELL_SIZE + BLOCKBLAST_CELL_SIZE // 2
                        PARTICLE_SYSTEM.add_explosion(x, y, self.grid[r][c], count=25)
                        PARTICLE_SYSTEM.add_sparkle(x, y, count=15)

            # 콤보 카운트
            self.combo_count += 1
            self.combo_display_timer = 120

            # 화면 흔들림 효과 (콤보에 따라 강도 증가)
            if self.combo_count > 1:
                self.screen_shake_intensity = min(10, 3 + self.combo_count)
                self.screen_shake_timer = 20

            # 점수 계산
            cleared_count = len(rows_to_clear) + len(cols_to_clear)
            base_score = cleared_count * 100
            combo_bonus = self.combo_count * 50 if self.combo_count > 1 else 0
            multi_clear_bonus = (cleared_count - 1) * 50 if cleared_count > 1 else 0

            total_score = base_score + combo_bonus + multi_clear_bonus
            self.score += total_score

            # 떠오르는 점수 텍스트
            center_x = BLOCKBLAST_OFFSET_X + (BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE) // 2
            center_y = BLOCKBLAST_OFFSET_Y + (BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE) // 2
            FLOATING_TEXT_SYSTEM.add_text(center_x, center_y - 50, f"+{total_score}", COLORS['gold'], 'large')
        else:
            # 콤보 리셋
            self.combo_count = 0

    def update_animation(self):
        """애니메이션 업데이트"""
        # 배경 애니메이션 타이머
        self.background_time += 1

        # 화면 흔들림 업데이트
        if self.screen_shake_timer > 0:
            self.screen_shake_timer -= 1
            if self.screen_shake_timer == 0:
                self.screen_shake_intensity = 0

        # 펄스 효과 업데이트
        self.pulse_effects = [(x, y, t - 1) for x, y, t in self.pulse_effects if t > 0]

        # 게임 오버 페이드 아웃
        if self.game_over and self.game_over_fade < 200:
            self.game_over_fade += 2

        if self.clear_animation_timer > 0:
            self.clear_animation_timer -= 1
            if self.clear_animation_timer == 0:
                # 애니메이션 끝나면 실제로 제거
                for r in self.clearing_rows:
                    for c in range(BLOCKBLAST_GRID_SIZE):
                        self.grid[r][c] = 0

                for c in self.clearing_cols:
                    for r in range(BLOCKBLAST_GRID_SIZE):
                        self.grid[r][c] = 0

                self.clearing_rows = []
                self.clearing_cols = []

                # PERFECT 체크 (모든 블록이 제거되었는지 확인)
                all_cleared = all(self.grid[r][c] == 0 for r in range(BLOCKBLAST_GRID_SIZE) for c in range(BLOCKBLAST_GRID_SIZE))
                if all_cleared:
                    self.perfect_display_timer = 180  # 3초 동안 표시
                    perfect_bonus = 1500
                    self.score += perfect_bonus
                    # 화면 중앙에 색종이 효과 (더 화려하게)
                    center_x = BLOCKBLAST_OFFSET_X + (BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE) // 2
                    center_y = BLOCKBLAST_OFFSET_Y + (BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE) // 2
                    PARTICLE_SYSTEM.add_confetti(center_x, center_y, count=100)
                    PARTICLE_SYSTEM.add_sparkle(center_x, center_y, count=30)
                    # 떠오르는 텍스트
                    FLOATING_TEXT_SYSTEM.add_text(center_x, center_y, "+1500", COLORS['green'], 'huge')
                    # 화면 흔들림
                    self.screen_shake_intensity = 15
                    self.screen_shake_timer = 30

                # 줄 제거 후 게임오버 체크 (중요!)
                if self.need_game_over_check:
                    self.need_game_over_check = False
                    if self.check_game_over():
                        self.game_over = True
                        self.leaderboard = LeaderboardManager.update(GAME_BLOCKBLAST, self.score, student_id=CURRENT_STUDENT_ID)

        # 콤보 표시 타이머
        if self.combo_display_timer > 0:
            self.combo_display_timer -= 1

        # PERFECT 표시 타이머
        if self.perfect_display_timer > 0:
            self.perfect_display_timer -= 1

        # 신기록 표시 타이머
        if self.record_display_timer > 0:
            self.record_display_timer -= 1
    
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
        # 화면 흔들림 오프셋 계산
        shake_x = 0
        shake_y = 0
        if self.screen_shake_intensity > 0:
            shake_x = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_y = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)

        # 배경 그라데이션 애니메이션
        # 시간에 따라 부드럽게 변하는 색상
        bg_wave = math.sin(self.background_time * 0.02) * 0.5 + 0.5  # 0~1 사이 값
        bg_r = int(235 + bg_wave * 10)
        bg_g = int(240 + bg_wave * 10)
        bg_b = int(245 + bg_wave * 10)
        WINDOW.fill((bg_r, bg_g, bg_b))

        # 그리드 배경 (화면 흔들림 적용)
        grid_rect = pygame.Rect(
            BLOCKBLAST_OFFSET_X + shake_x,
            BLOCKBLAST_OFFSET_Y + shake_y,
            BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE,
            BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE
        )
        pygame.draw.rect(WINDOW, (255, 255, 255), grid_rect)
        
        # 그리드 선 (화면 흔들림 적용)
        for i in range(BLOCKBLAST_GRID_SIZE + 1):
            # 수평선
            pygame.draw.line(
                WINDOW, BLOCKBLAST_GRID_COLOR,
                (BLOCKBLAST_OFFSET_X + shake_x, BLOCKBLAST_OFFSET_Y + shake_y + i * BLOCKBLAST_CELL_SIZE),
                (BLOCKBLAST_OFFSET_X + shake_x + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE,
                 BLOCKBLAST_OFFSET_Y + shake_y + i * BLOCKBLAST_CELL_SIZE),
                2
            )
            # 수직선
            pygame.draw.line(
                WINDOW, BLOCKBLAST_GRID_COLOR,
                (BLOCKBLAST_OFFSET_X + shake_x + i * BLOCKBLAST_CELL_SIZE, BLOCKBLAST_OFFSET_Y + shake_y),
                (BLOCKBLAST_OFFSET_X + shake_x + i * BLOCKBLAST_CELL_SIZE,
                 BLOCKBLAST_OFFSET_Y + shake_y + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE),
                2
            )
        
        # 펄스 효과 그리기 (블록보다 먼저)
        for pulse_x, pulse_y, pulse_timer in self.pulse_effects:
            radius = int((30 - pulse_timer) * 2)  # 펄스가 커지는 반지름
            alpha = int(255 * (pulse_timer / 30))  # 점점 투명해짐
            if radius > 0 and alpha > 0:
                pulse_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(pulse_surf, (255, 215, 0, alpha), (radius, radius), radius, 3)
                WINDOW.blit(pulse_surf, (int(pulse_x + shake_x - radius), int(pulse_y + shake_y - radius)))

        # 배치된 블록들 (화면 흔들림 적용)
        for r in range(BLOCKBLAST_GRID_SIZE):
            for c in range(BLOCKBLAST_GRID_SIZE):
                if self.grid[r][c] != 0:
                    # 제거 애니메이션 중인 블록은 깜빡이는 효과
                    is_clearing = (r in self.clearing_rows or c in self.clearing_cols)

                    rect = pygame.Rect(
                        BLOCKBLAST_OFFSET_X + shake_x + c * BLOCKBLAST_CELL_SIZE + 1,
                        BLOCKBLAST_OFFSET_Y + shake_y + r * BLOCKBLAST_CELL_SIZE + 1,
                        BLOCKBLAST_CELL_SIZE - 2,
                        BLOCKBLAST_CELL_SIZE - 2
                    )

                    if is_clearing and self.clear_animation_timer > 0:
                        # 깜빡이는 효과 (사인파 사용)
                        flash_intensity = int(128 + 127 * math.sin(self.clear_animation_timer * 0.5))
                        flash_color = (255, 255, flash_intensity)
                        pygame.draw.rect(WINDOW, flash_color, rect, border_radius=5)
                        pygame.draw.rect(WINDOW, COLORS['gold'], rect, 3, border_radius=5)
                    else:
                        pygame.draw.rect(WINDOW, self.grid[r][c], rect, border_radius=5)
                        pygame.draw.rect(WINDOW, COLORS['white'], rect, 2, border_radius=5)
        
        # 배치 가능한 위치 하이라이트 (화면 흔들림 적용)
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
                                        BLOCKBLAST_OFFSET_X + shake_x + c * BLOCKBLAST_CELL_SIZE + 1,
                                        BLOCKBLAST_OFFSET_Y + shake_y + r * BLOCKBLAST_CELL_SIZE + 1,
                                        BLOCKBLAST_CELL_SIZE - 2,
                                        BLOCKBLAST_CELL_SIZE - 2
                                    )
                                    surf = pygame.Surface((BLOCKBLAST_CELL_SIZE - 2, BLOCKBLAST_CELL_SIZE - 2), pygame.SRCALPHA)
                                    pygame.draw.rect(surf, (0, 255, 0, 120), (0, 0, BLOCKBLAST_CELL_SIZE - 2, BLOCKBLAST_CELL_SIZE - 2), border_radius=5)
                                    WINDOW.blit(surf, rect)
        
        # 테두리
        pygame.draw.rect(WINDOW, COLORS['outline'], grid_rect, 4)
        pygame.draw.line(WINDOW, COLORS['outline'], (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 3)
        
        # 사용 가능한 블록들 표시
        piece_area_y = BLOCKBLAST_OFFSET_Y + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE + 20
        piece_spacing = GAME_WIDTH // 3
        piece_cell_size = 40  # 블록 표시 크기

        # 호버 중인 블록 확인
        self.hovered_piece_idx = None
        mouse_pos = pygame.mouse.get_pos()

        for idx, piece in enumerate(self.available_pieces):
            if piece is None:
                continue

            # 블록을 드래그 중이 아닐 때만 표시
            if self.dragging and idx == self.selected_piece_idx:
                continue

            # 블록을 중앙에 배치
            piece_center_x = piece_spacing * idx + piece_spacing // 2
            piece_x = piece_center_x - (piece.width * piece_cell_size) // 2
            piece_y = piece_area_y

            # 호버 체크
            is_hovered = False
            if not self.dragging:
                if (piece_x <= mouse_pos[0] <= piece_x + piece.width * piece_cell_size and
                    piece_y <= mouse_pos[1] <= piece_y + piece.height * piece_cell_size):
                    is_hovered = True
                    self.hovered_piece_idx = idx

            # 배치 가능 여부 확인
            can_be_placed = False
            for r in range(BLOCKBLAST_GRID_SIZE):
                for c in range(BLOCKBLAST_GRID_SIZE):
                    if self.can_place(piece, r, c):
                        can_be_placed = True
                        break
                if can_be_placed:
                    break

            # 호버 시 확대 효과
            display_size = piece_cell_size
            display_x = piece_x
            display_y = piece_y
            if is_hovered:
                display_size = int(piece_cell_size * 1.1)  # 10% 확대
                # 중앙에서 확대되도록 위치 조정
                display_x = piece_center_x - (piece.width * display_size) // 2
                display_y = piece_y - (display_size - piece_cell_size) // 2

            # 배치 불가능하면 회색으로 표시
            alpha = 255 if can_be_placed else 100
            piece.draw(display_x, display_y, display_size, alpha)

        # 드래그 중인 블록 (마우스 중심에 표시)
        if self.dragging and self.selected_piece_idx is not None:
            piece = self.available_pieces[self.selected_piece_idx]
            if piece:
                # 블록의 중심이 마우스 위치에 오도록
                draw_x = self.mouse_x - (piece.width * piece_cell_size) // 2
                draw_y = self.mouse_y - (piece.height * piece_cell_size) // 2
                piece.draw(draw_x, draw_y, piece_cell_size)
        
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

        # 파티클 시스템 그리기
        PARTICLE_SYSTEM.draw(WINDOW)

        # 떠오르는 텍스트 그리기
        FLOATING_TEXT_SYSTEM.draw(WINDOW)

        # PERFECT 메시지
        if self.perfect_display_timer > 0:
            # 크기 애니메이션 (처음에 크게 나타났다가 작아짐)
            scale = 1.0 + (self.perfect_display_timer / 180.0) * 0.5
            perfect_text = "PERFECT!"
            # 큰 폰트로 표시
            text_surf = FONTS['huge'].render(perfect_text, True, COLORS['gold'])
            text_surf = pygame.transform.scale(text_surf,
                (int(text_surf.get_width() * scale), int(text_surf.get_height() * scale)))
            text_rect = text_surf.get_rect(center=(GAME_WIDTH // 2, 150))
            # 그림자 효과
            shadow_surf = FONTS['huge'].render(perfect_text, True, COLORS['black'])
            shadow_surf = pygame.transform.scale(shadow_surf,
                (int(shadow_surf.get_width() * scale), int(shadow_surf.get_height() * scale)))
            WINDOW.blit(shadow_surf, (text_rect.x + 3, text_rect.y + 3))
            WINDOW.blit(text_surf, text_rect)
            # 보너스 점수 표시
            bonus_text = "+500"
            bonus_surf = FONTS['medium'].render(bonus_text, True, COLORS['green'])
            WINDOW.blit(bonus_surf, (text_rect.centerx - bonus_surf.get_width() // 2, text_rect.bottom + 10))

        # 콤보 메시지
        if self.combo_display_timer > 0 and self.combo_count > 1:
            combo_text = f"COMBO x{self.combo_count}!"
            combo_surf = FONTS['large'].render(combo_text, True, COLORS['orange'])
            combo_rect = combo_surf.get_rect(center=(GAME_WIDTH // 2, 220))
            # 그림자
            shadow_surf = FONTS['large'].render(combo_text, True, COLORS['black'])
            WINDOW.blit(shadow_surf, (combo_rect.x + 2, combo_rect.y + 2))
            WINDOW.blit(combo_surf, combo_rect)


        # 게임 오버 페이드 아웃 효과
        if self.game_over and self.game_over_fade > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.set_alpha(min(150, self.game_over_fade))
            fade_surf.fill((0, 0, 0))
            WINDOW.blit(fade_surf, (0, 0))

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
                piece_area_y = BLOCKBLAST_OFFSET_Y + BLOCKBLAST_GRID_SIZE * BLOCKBLAST_CELL_SIZE + 20
                piece_spacing = GAME_WIDTH // 3
                piece_cell_size = 40

                for idx, piece in enumerate(self.available_pieces):
                    if piece is None:
                        continue

                    # 블록을 중앙에 배치
                    piece_center_x = piece_spacing * idx + piece_spacing // 2
                    piece_x = piece_center_x - (piece.width * piece_cell_size) // 2
                    piece_y = piece_area_y

                    # 블록 영역 클릭 확인
                    if (piece_x <= event.pos[0] <= piece_x + piece.width * piece_cell_size and
                        piece_y <= event.pos[1] <= piece_y + piece.height * piece_cell_size):
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

                            # 펄스 효과 추가 (배치된 블록의 중심)
                            for row_idx, row in enumerate(piece.shape):
                                for col_idx, cell in enumerate(row):
                                    if cell:
                                        r = grid_row + row_idx
                                        c = grid_col + col_idx
                                        pulse_x = BLOCKBLAST_OFFSET_X + c * BLOCKBLAST_CELL_SIZE + BLOCKBLAST_CELL_SIZE // 2
                                        pulse_y = BLOCKBLAST_OFFSET_Y + r * BLOCKBLAST_CELL_SIZE + BLOCKBLAST_CELL_SIZE // 2
                                        self.pulse_effects.append((pulse_x, pulse_y, 30))

                            # 떠오르는 텍스트
                            center_x = BLOCKBLAST_OFFSET_X + grid_col * BLOCKBLAST_CELL_SIZE + (piece.width * BLOCKBLAST_CELL_SIZE) // 2
                            center_y = BLOCKBLAST_OFFSET_Y + grid_row * BLOCKBLAST_CELL_SIZE + (piece.height * BLOCKBLAST_CELL_SIZE) // 2
                            FLOATING_TEXT_SYSTEM.add_text(center_x, center_y, "+10", COLORS['blue'], 'small')

                            self.available_pieces[self.selected_piece_idx] = None

                            # 모든 블록을 사용했으면 새로 생성
                            if all(p is None for p in self.available_pieces):
                                self.available_pieces = self.generate_new_pieces()

                            # 게임 오버 확인 플래그 설정 (애니메이션 후 체크)
                            # 줄 제거 애니메이션이 있으면 나중에 체크, 없으면 즉시 체크
                            if self.clear_animation_timer > 0:
                                self.need_game_over_check = True
                            else:
                                # 줄 제거가 없었으면 즉시 게임오버 체크
                                if self.check_game_over():
                                    self.game_over = True
                                    self.leaderboard = LeaderboardManager.update(GAME_BLOCKBLAST, self.score, student_id=CURRENT_STUDENT_ID)
                
                self.dragging = False
                self.selected_piece_idx = None
        
        return GAME_BLOCKBLAST

def run_blockblast():
    """블록블라스트 게임 실행"""
    game = BlockBlast()
    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)

        # 게임 오버 후 5초 자동 메뉴 복귀
        if game.game_over:
            game.game_over_timer += 1
            if game.game_over_timer >= 300:  # 5초 (60 FPS * 5)
                PARTICLE_SYSTEM.clear()  # 파티클 초기화
                FLOATING_TEXT_SYSTEM.clear()  # 떠오르는 텍스트 초기화
                return MENU

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            result = game.handle_event(event)
            if result != GAME_BLOCKBLAST:
                PARTICLE_SYSTEM.clear()  # 파티클 초기화
                FLOATING_TEXT_SYSTEM.clear()  # 떠오르는 텍스트 초기화
                return result

        # 애니메이션 업데이트
        game.update_animation()
        PARTICLE_SYSTEM.update()
        FLOATING_TEXT_SYSTEM.update()

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
        LEADERBOARD: run_leaderboard,
        "tetris_mode_select": run_tetris_mode_select,
        TETRIS_MULTI: run_tetris_multiplayer
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
