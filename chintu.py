import pygame
import random
import numpy as np
import copy
import os

# Initialize Pygame
pygame.init()

# Game Constants
SIZE = WIDTH, HEIGHT = 400, 550  # Increased height for footer/instructions
GRID_SIZE = 4
TILE_SIZE = WIDTH // GRID_SIZE
FONT = pygame.font.SysFont("arial", 32, bold=True)
SMALL_FONT = pygame.font.SysFont("arial", 20)
BIG_FONT = pygame.font.SysFont("arial", 48, bold=True)

# Colors
BACKGROUND_COLOR = (187, 173, 160)
EMPTY_TILE_COLOR = (205, 193, 180)
TILE_COLORS = {
    2: (238, 228, 218), 4: (237, 224, 200), 8: (242, 177, 121),
    16: (245, 149, 99), 32: (246, 124, 95), 64: (246, 94, 59),
    128: (237, 207, 114), 256: (237, 204, 97), 512: (237, 200, 80),
    1024: (237, 197, 63), 2048: (237, 194, 46)
}
TEXT_COLOR = (119, 110, 101)
HEADER_HEIGHT = 120

# Initialize screen
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption("2048 AI - Press 'R' to Restart")

# File to store High Score
HIGHSCORE_FILE = "highscore.txt"

def load_high_score():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read())
        except:
            return 0
    return 0

def save_high_score(score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(score))

# Game class
class Game2048:
    def __init__(self):
        self.high_score = load_high_score()
        self.reset()

    def reset(self):
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
        self.score = 0
        self.game_over = False
        self.add_tile()
        self.add_tile()

    def add_tile(self):
        empty = list(zip(*np.where(self.grid == 0)))
        if empty:
            x, y = random.choice(empty)
            self.grid[x][y] = 2 if random.random() < 0.9 else 4

    def update_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)

    def move(self, direction, simulate=False):
        # Returns True if moved, False otherwise. 
        # If simulate=True, it doesn't actually change the real game state (used for AI).
        if simulate:
            temp_grid = self.grid.copy()
            temp_score = self.score
        
        movements = []
        def merge(row):
            nonzero = row[row != 0]
            new_row = []
            score_add = 0
            skip = False
            for i in range(len(nonzero)):
                if skip:
                    skip = False
                    continue
                if i + 1 < len(nonzero) and nonzero[i] == nonzero[i + 1]:
                    new_row.append(nonzero[i] * 2)
                    score_add += nonzero[i] * 2
                    skip = True
                else:
                    new_row.append(nonzero[i])
            return np.array(new_row + [0] * (GRID_SIZE - len(new_row))), score_add

        current_grid = self.grid if not simulate else temp_grid
        original_grid = current_grid.copy()
        earned_score = 0

        if direction == 'up':
            current_grid = current_grid.T
            for i in range(GRID_SIZE):
                current_grid[i], s = merge(current_grid[i])
                earned_score += s
            current_grid = current_grid.T

        elif direction == 'down':
            current_grid = np.flip(current_grid.T, axis=1)
            for i in range(GRID_SIZE):
                current_grid[i], s = merge(current_grid[i])
                earned_score += s
            current_grid = np.flip(current_grid.T, axis=0)

        elif direction == 'left':
            for i in range(GRID_SIZE):
                current_grid[i], s = merge(current_grid[i])
                earned_score += s

        elif direction == 'right':
            current_grid = np.flip(current_grid, axis=1)
            for i in range(GRID_SIZE):
                current_grid[i], s = merge(current_grid[i])
                earned_score += s
            current_grid = np.flip(current_grid, axis=1)

        moved = not np.array_equal(original_grid, current_grid)
        
        if not simulate:
            self.grid = current_grid
            self.score += earned_score
            self.update_high_score()
            if moved:
                self.add_tile()
        
        return moved

    def is_game_over_check(self):
        if np.any(self.grid == 0): return False
        for dir in ['up', 'down', 'left', 'right']:
            temp = copy.deepcopy(self)
            if temp.move(dir, simulate=False): # We use a deepcopy, so simulate=False is fine here
                return False
        return True

    def get_possible_moves(self):
        moves = []
        for dir in ['up', 'down', 'left', 'right']:
            temp = copy.deepcopy(self)
            if temp.move(dir, simulate=False):
                moves.append(dir)
        return moves

    # ---------------- AI LOGIC ----------------
    def get_board_heuristic(self, grid):
        """
        Calculates a score for the board based on a 'Snake' weight matrix.
        This forces the AI to keep the largest tile in the top-left corner
        and chain descending numbers.
        """
        # Weight matrix favoring top-left corner
        weights = np.array([
            [65536, 32768, 16384, 8192],
            [  512,  1024,  2048, 4096],
            [  256,   128,    64,   32],
            [    2,     4,     8,   16]
        ])
        
        # Calculate score: Sum(Tile Value * Weight)
        score = np.sum(grid * weights)
        
        # Penalize for number of empty tiles (fewer empty tiles = bad)
        empty_penalty = (16 - np.count_nonzero(grid)) * 1000
        
        return score + empty_penalty

    def ai_suggest_move(self):
        best_score = -float('inf')
        best_move = None
        
        possible_moves = self.get_possible_moves()
        if not possible_moves:
            return None

        # Look 1 step ahead (simulate move -> evaluate board)
        # To make it "Precious", we don't just look at immediate score,
        # we look at the STRUCTURE of the board using get_board_heuristic.
        for move in possible_moves:
            temp_game = copy.deepcopy(self)
            temp_game.move(move, simulate=False)
            
            # Evaluate the resulting board
            score = self.get_board_heuristic(temp_game.grid)
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move

# Draw Functions
def draw_grid(game, ai_move):
    screen.fill(BACKGROUND_COLOR)
    
    # Draw Tiles
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            value = game.grid[i][j]
            color = TILE_COLORS.get(value, (60, 58, 50)) if value != 0 else EMPTY_TILE_COLOR
            
            rect_x = j * TILE_SIZE + 5
            rect_y = i * TILE_SIZE + HEADER_HEIGHT + 5
            rect_w = TILE_SIZE - 10
            
            pygame.draw.rect(screen, color, (rect_x, rect_y, rect_w, rect_w), border_radius=8)
            
            if value:
                # Dynamic font size for large numbers
                font_to_use = BIG_FONT if value < 100 else (FONT if value < 1000 else pygame.font.SysFont("arial", 24, bold=True))
                text_color = (119, 110, 101) if value <= 4 else (249, 246, 242)
                
                text = font_to_use.render(str(value), True, text_color)
                rect = text.get_rect(center=(rect_x + rect_w // 2, rect_y + rect_w // 2))
                screen.blit(text, rect)

    # Draw Header Background
    pygame.draw.rect(screen, (250, 248, 239), (0, 0, WIDTH, HEADER_HEIGHT))
    
    # Scores
    score_label = SMALL_FONT.render("SCORE", True, TEXT_COLOR)
    score_val = FONT.render(str(game.score), True, TEXT_COLOR)
    screen.blit(score_label, (20, 15))
    screen.blit(score_val, (20, 35))

    high_label = SMALL_FONT.render("BEST", True, TEXT_COLOR)
    high_val = FONT.render(str(game.high_score), True, TEXT_COLOR)
    screen.blit(high_label, (200, 15))
    screen.blit(high_val, (200, 35))

    # AI Suggestion
    if not game.game_over:
        sugg_text = SMALL_FONT.render(f"AI Suggests: {str(ai_move).upper()}", True, (255, 99, 71))
        screen.blit(sugg_text, (20, 85))
        instr_text = SMALL_FONT.render("Press 'A' to auto-move", True, (100, 100, 100))
        screen.blit(instr_text, (200, 85))

    # Game Over Overlay
    if game.game_over:
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((255, 255, 255, 180)) # Transparent white
        screen.blit(s, (0,0))
        
        over_text = BIG_FONT.render("Game Over!", True, (119, 110, 101))
        screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 50))
        
        restart_text = FONT.render("Press 'R' to Restart", True, (119, 110, 101))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 20))

def main():
    game = Game2048()
    clock = pygame.time.Clock()
    running = True
    ai_move = game.ai_suggest_move()

    while running:
        # Check Game Over State each frame
        if not game.game_over and game.is_game_over_check():
            game.game_over = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                # Restart Handler
                if event.key == pygame.K_r:
                    game.reset()
                    ai_move = game.ai_suggest_move()
                
                # Gameplay Handlers (only if game not over)
                if not game.game_over:
                    moved = False
                    if event.key == pygame.K_UP:
                        moved = game.move('up')
                    elif event.key == pygame.K_DOWN:
                        moved = game.move('down')
                    elif event.key == pygame.K_LEFT:
                        moved = game.move('left')
                    elif event.key == pygame.K_RIGHT:
                        moved = game.move('right')
                    elif event.key == pygame.K_a:
                        # Auto-move with AI
                        if ai_move:
                            moved = game.move(ai_move)
                    
                    if moved:
                        ai_move = game.ai_suggest_move()

        draw_grid(game, ai_move)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
