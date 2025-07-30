import pygame
import random
import os
import time
import glob
import sys

# Initialize Pygame
pygame.init()
pygame.font.init()

# Constants
BLOCK_SIZE = 30
GRID_WIDTH = 15
GRID_HEIGHT = 20
BUTTON_HEIGHT = 40
BUTTON_PADDING = 10

# Calculate window dimensions based on grid
WINDOW_WIDTH = int(10 * BLOCK_SIZE * 1.5)  
WINDOW_HEIGHT = GRID_HEIGHT * BLOCK_SIZE + 100  

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRANSPARENT_BLACK = (0, 0, 0, 128)
BUTTON_COLOR = (100, 100, 255)  
BUTTON_HOVER_COLOR = (150, 150, 255)  
LEFT_BUTTON_COLOR = (255, 165, 0)  
LEFT_BUTTON_HOVER = (255, 195, 77)  
ROTATE_COLOR = (100, 200, 100)  
ROTATE_HOVER_COLOR = (150, 255, 150)  
DROP_COLOR = (200, 100, 100)  
DROP_HOVER_COLOR = (255, 150, 150)  
BUTTON_TEXT_COLOR = (255, 255, 255)
BUTTON_BORDER_COLOR = (200, 200, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  
    [[1, 1], [1, 1]],  
    [[1, 1, 1], [0, 1, 0]],  
    [[1, 1, 1], [1, 0, 0]],  
    [[1, 1, 1], [0, 0, 1]],  
    [[1, 1, 0], [0, 1, 1]],  
    [[0, 1, 1], [1, 1, 0]]   
]

COLORS = [CYAN, YELLOW, MAGENTA, ORANGE, BLUE, GREEN, RED]

def load_random_background():
    """Load a random background image from the assets directory"""
    try:
        image_files = glob.glob(os.path.join('assets', '*.jpg'))
        if not image_files:
            return None
        
        image_path = random.choice(image_files)
        print(f"Loading background: {os.path.basename(image_path)}")
        return pygame.transform.scale(
            pygame.image.load(image_path),
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
    except:
        return None

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Tetris')
        
        # Try different fonts that might support Unicode better
        available_fonts = pygame.font.get_fonts()
        for font_name in ['segoeuisymbol', 'segoeui', 'arial', 'timesnewroman']:
            if font_name in available_fonts:
                self.font = pygame.font.SysFont(font_name, 24)
                break
        else:
            self.font = pygame.font.SysFont(None, 24)  
        
        self.game_surface = pygame.Surface((GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE), pygame.SRCALPHA)
        
        # Load background once at startup
        self.background = load_random_background()
        
        # Create buttons with adjusted width for narrower window
        button_width = (WINDOW_WIDTH - BUTTON_PADDING * 5) // 4
        button_y = WINDOW_HEIGHT - BUTTON_HEIGHT - BUTTON_PADDING * 2
        
        self.buttons = {
            'left': {'rect': pygame.Rect(BUTTON_PADDING, button_y, button_width, BUTTON_HEIGHT),
                    'text': '<', 'action': lambda: self.move_piece(-1, 0)},
            'right': {'rect': pygame.Rect(BUTTON_PADDING * 2 + button_width, button_y,
                                        button_width, BUTTON_HEIGHT),
                     'text': '>', 'action': lambda: self.move_piece(1, 0)},
            'rotate': {'rect': pygame.Rect(BUTTON_PADDING * 3 + button_width * 2, button_y,
                                         button_width, BUTTON_HEIGHT),
                      'text': '⟳', 'action': self.rotate_piece},  
            'down': {'rect': pygame.Rect(BUTTON_PADDING * 4 + button_width * 3, button_y,
                                       button_width, BUTTON_HEIGHT),
                    'text': 'v', 'action': self.drop_piece}
        }
        
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.current_piece = self.new_piece()
        self.game_over = False
        self.lines_to_clear = []
        self.is_clearing = False
        self.clear_start_time = 0

    def new_piece(self):
        """Create a new random piece"""
        shape = random.randint(0, len(SHAPES) - 1)
        return {
            'shape': SHAPES[shape],
            'color': COLORS[shape],
            'x': GRID_WIDTH // 2 - len(SHAPES[shape][0]) // 2,
            'y': 0
        }

    def is_valid_move(self, x, y, shape):
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    new_x = x + j
                    new_y = y + i
                    if (new_x < 0 or new_x >= GRID_WIDTH or 
                        new_y >= GRID_HEIGHT or 
                        (new_y >= 0 and self.grid[new_y][new_x] != BLACK)):
                        return False
        return True

    def add_piece_to_grid(self):
        """Add the current piece to the grid"""
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    self.grid[self.current_piece['y'] + i][self.current_piece['x'] + j] = self.current_piece['color']

    def clear_lines(self):
        """Check for completed lines and mark them for clearing"""
        self.lines_to_clear = []
        for i in range(GRID_HEIGHT):
            if all(cell != BLACK for cell in self.grid[i]):
                self.lines_to_clear.append(i)
        if self.lines_to_clear:
            self.is_clearing = True
            self.clear_start_time = time.time()
            self.score += len(self.lines_to_clear) * 100

    def remove_lines(self):
        """Remove completed lines and shift remaining lines down"""
        self.is_clearing = False
        # Remove lines from bottom to top
        for line in sorted(self.lines_to_clear, reverse=True):
            del self.grid[line]
            self.grid.insert(0, [BLACK] * GRID_WIDTH)
        self.lines_to_clear = []

    def rotate_piece(self):
        rotated_shape = list(zip(*reversed(self.current_piece['shape'])))
        old_shape = self.current_piece['shape']
        self.current_piece['shape'] = rotated_shape
        if not self.is_valid_move(self.current_piece['x'], self.current_piece['y'], self.current_piece['shape']):
            self.current_piece['shape'] = old_shape

    def check_collision(self, piece):
        """Return True if there is a collision"""
        for i, row in enumerate(piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    if (piece['x'] + j < 0 or piece['x'] + j >= GRID_WIDTH or
                        piece['y'] + i >= GRID_HEIGHT or
                        (piece['y'] + i >= 0 and self.grid[piece['y'] + i][piece['x'] + j] != BLACK)):
                        return True
        return False

    def move_piece(self, dx, dy):
        """Move the current piece if possible"""
        if self.game_over or self.is_clearing:
            return False
        
        new_x = self.current_piece['x'] + dx
        new_y = self.current_piece['y'] + dy
        
        # Save current position
        old_x = self.current_piece['x']
        old_y = self.current_piece['y']
        
        # Try new position
        self.current_piece['x'] = new_x
        self.current_piece['y'] = new_y
        
        if self.check_collision(self.current_piece):
            # Restore old position
            self.current_piece['x'] = old_x
            self.current_piece['y'] = old_y
            
            if dy > 0:  # Only lock piece if moving down
                self.add_piece_to_grid()
                self.clear_lines()
                if not self.is_clearing:
                    self.current_piece = self.new_piece()
                    if self.check_collision(self.current_piece):
                        self.game_over = True
            return False
        return True

    def drop_piece(self):
        """Drop the piece to the bottom instantly"""
        if self.game_over or self.is_clearing:
            return
        while not self.check_collision(self.current_piece):
            self.current_piece['y'] += 1
        self.current_piece['y'] -= 1
        self.add_piece_to_grid()
        if not self.is_clearing:
            self.clear_lines()
            if not self.is_clearing:  
                self.current_piece = self.new_piece()
                if self.check_collision(self.current_piece):
                    self.game_over = True

    def handle_button_click(self, pos):
        """Handle mouse clicks on buttons"""
        if self.game_over:
            return
            
        for button in self.buttons.values():
            if button['rect'].collidepoint(pos):
                button['action']()
                return  

    def draw_buttons(self):
        """Draw control buttons with distinct appearances"""
        # Draw control bar background
        control_bar = pygame.Rect(0, WINDOW_HEIGHT - BUTTON_HEIGHT - BUTTON_PADDING * 3,
                                WINDOW_WIDTH, BUTTON_HEIGHT + BUTTON_PADDING * 4)
        pygame.draw.rect(self.screen, (50, 50, 80), control_bar)
        
        mouse_pos = pygame.mouse.get_pos()
        for button_name, button in self.buttons.items():
            # Choose colors based on button type
            if button_name == 'left':
                base_color = LEFT_BUTTON_COLOR
                hover_color = LEFT_BUTTON_HOVER
                border_color = (255, 195, 77)
            elif button_name == 'rotate':
                base_color = ROTATE_COLOR
                hover_color = ROTATE_HOVER_COLOR
                border_color = (150, 255, 150)
            elif button_name == 'down':
                base_color = DROP_COLOR
                hover_color = DROP_HOVER_COLOR
                border_color = (255, 150, 150)
            else:
                base_color = BUTTON_COLOR
                hover_color = BUTTON_HOVER_COLOR
                border_color = BUTTON_BORDER_COLOR
            
            # Button background
            color = hover_color if button['rect'].collidepoint(mouse_pos) else base_color
            pygame.draw.rect(self.screen, color, button['rect'], border_radius=10)
            
            # Button border
            pygame.draw.rect(self.screen, border_color, button['rect'], 3, border_radius=10)
            
            # Button text with shadow
            text = self.font.render(button['text'], True, BUTTON_TEXT_COLOR)
            text_rect = text.get_rect(center=button['rect'].center)
            
            # Draw text shadow
            shadow_text = self.font.render(button['text'], True, (0, 0, 0))
            shadow_rect = text_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(shadow_text, shadow_rect)
            
            # Draw main text
            self.screen.blit(text, text_rect)

    def draw(self):
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BLACK)

        # Calculate the offset to center the game grid
        grid_offset_x = (WINDOW_WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2

        # Draw only the filled cells (pieces) in the grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] != BLACK:  
                    color = self.grid[y][x]
                    if y in self.lines_to_clear:
                        if int((time.time() - self.clear_start_time) * 4) % 2:
                            color = WHITE
                    pygame.draw.rect(self.screen, color,
                                   (grid_offset_x + x * BLOCK_SIZE,
                                    y * BLOCK_SIZE,
                                    BLOCK_SIZE - 1, BLOCK_SIZE - 1))

        # Draw current piece with offset
        if self.current_piece and not self.game_over:
            shape = self.current_piece['shape']
            color = self.current_piece['color']
            for y in range(len(shape)):
                for x in range(len(shape[y])):
                    if shape[y][x]:
                        pygame.draw.rect(self.screen, color,
                                       (grid_offset_x + (self.current_piece['x'] + x) * BLOCK_SIZE,
                                        (self.current_piece['y'] + y) * BLOCK_SIZE,
                                        BLOCK_SIZE - 1, BLOCK_SIZE - 1))

        # Draw score with offset
        score_text = self.font.render(f'Score: {self.score}', True, WHITE)
        score_shadow = self.font.render(f'Score: {self.score}', True, BLACK)
        # Draw score shadow
        self.screen.blit(score_shadow, (grid_offset_x + 2, 7))
        # Draw score text
        self.screen.blit(score_text, (grid_offset_x, 5))

        # Draw game over text with offset
        if self.game_over:
            game_over_text = self.font.render('Game Over!', True, WHITE)
            game_over_shadow = self.font.render('Game Over!', True, BLACK)
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            shadow_rect = text_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(game_over_shadow, shadow_rect)
            self.screen.blit(game_over_text, text_rect)

        # Draw buttons
        self.draw_buttons()
        
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        fall_time = 0
        fall_speed = 0.6
        running = True
        
        while running:
            dt = clock.tick(120)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                    break
                
                if event.type == pygame.KEYDOWN:
                    if not self.game_over:
                        if event.key == pygame.K_LEFT:
                            self.move_piece(-1, 0)
                        elif event.key == pygame.K_RIGHT:
                            self.move_piece(1, 0)
                        elif event.key == pygame.K_DOWN:
                            self.drop_piece()
                        elif event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                            self.rotate_piece()
                    if event.key == pygame.K_r:
                        self.__init__()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_button_click(event.pos)
            
            if not self.game_over and not self.is_clearing:
                # Handle automatic falling
                fall_time += dt
                if fall_time >= fall_speed * 1000:
                    self.move_piece(0, 1)
                    fall_time = 0
            
            if self.is_clearing:
                if time.time() - self.clear_start_time >= 0.5:
                    self.remove_lines()
                    if not self.game_over:
                        self.current_piece = self.new_piece()
            
            self.draw()

if __name__ == '__main__':
    tetris = Tetris()
    try:
        tetris.run()
    finally:
        pygame.quit()
        sys.exit()
