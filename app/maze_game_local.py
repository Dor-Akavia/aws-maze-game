import pygame
import sys
import sqlite3

"""
Local Development Version of Maze Game
This version uses SQLite instead of PostgreSQL and skips SQS
Perfect for testing the game logic without AWS infrastructure
"""

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CELL_SIZE = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GREEN = (0, 150, 0)

# Game states
STATE_PLAYING = "playing"
STATE_STAGE_COMPLETE = "stage_complete"
STATE_GAME_COMPLETE = "game_complete"


class LocalDatabaseHandler:
    """Local SQLite database handler for development."""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Create SQLite database with sample stages."""
        try:
            self.connection = sqlite3.connect(':memory:')
            self.cursor = self.connection.cursor()
            
            # Create table
            self.cursor.execute('''
                CREATE TABLE maze_stages (
                    stage_id INTEGER PRIMARY KEY,
                    stage_number INTEGER UNIQUE,
                    layout TEXT,
                    width INTEGER,
                    height INTEGER,
                    start_x INTEGER,
                    start_y INTEGER,
                    end_x INTEGER,
                    end_y INTEGER
                )
            ''')
            
            # Insert sample stages
            stages = [
                (1, '''###########
#S........#
#.########.
#.........#
########.##
#.........#
#.#######.#
#.........E
###########''', 11, 9, 1, 1, 9, 7),
                
                (2, '''#############
#S..........#
##.########.#
#..#......#.#
#.##.####.#.#
#....#....#.#
######.####.#
#...........E
#############''', 13, 9, 1, 1, 11, 7),
                
                (3, '''###############
#S............#
#.###########.#
#.#.........#.#
#.#.#######.#.#
#...#.....#...#
#####.###.###.#
#.............#
#.###########.#
#...........E.#
###############''', 15, 11, 1, 1, 12, 9),
            ]
            
            for stage_num, layout, width, height, sx, sy, ex, ey in stages:
                self.cursor.execute(
                    'INSERT INTO maze_stages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (stage_num, stage_num, layout, width, height, sx, sy, ex, ey)
                )
            
            self.connection.commit()
            print("Local database initialized with 3 sample stages")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def get_stage(self, stage_number):
        """Get stage data."""
        try:
            self.cursor.execute(
                'SELECT * FROM maze_stages WHERE stage_number = ?',
                (stage_number,)
            )
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'stage_id': result[0],
                    'stage_number': result[1],
                    'layout': result[2],
                    'width': result[3],
                    'height': result[4],
                    'start_x': result[5],
                    'start_y': result[6],
                    'end_x': result[7],
                    'end_y': result[8]
                }
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def disconnect(self):
        """Close connection."""
        if self.connection:
            self.connection.close()


class MazeGame:
    """Simplified maze game for local development."""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Maze Game - Local Dev Mode")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.db_handler = LocalDatabaseHandler()
        
        self.current_stage = 1
        self.total_stages = 3  # Only 3 stages in dev mode
        self.stage_data = None
        self.maze = []
        self.player_x = 0
        self.player_y = 0
        self.end_x = 0
        self.end_y = 0
        self.game_state = STATE_PLAYING
        self.running = True
        self.continue_button = None
        
    def initialize(self):
        """Initialize the game."""
        if not self.db_handler.connect():
            return False
        return self.load_stage(self.current_stage)
    
    def load_stage(self, stage_number):
        """Load a stage."""
        self.stage_data = self.db_handler.get_stage(stage_number)
        if not self.stage_data:
            print(f"Failed to load stage {stage_number}")
            return False
        
        self.maze = []
        lines = self.stage_data['layout'].strip().split('\n')
        for line in lines:
            self.maze.append(list(line))
        
        self.player_x = self.stage_data['start_x']
        self.player_y = self.stage_data['start_y']
        self.end_x = self.stage_data['end_x']
        self.end_y = self.stage_data['end_y']
        
        self.game_state = STATE_PLAYING
        print(f"Loaded stage {stage_number}")
        return True
    
    def handle_events(self):
        """Handle events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if self.game_state == STATE_PLAYING:
                    self.handle_movement(event.key)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == STATE_STAGE_COMPLETE:
                    if self.continue_button and self.continue_button.collidepoint(event.pos):
                        self.next_stage()
                elif self.game_state == STATE_GAME_COMPLETE:
                    if self.continue_button and self.continue_button.collidepoint(event.pos):
                        self.restart_game()
    
    def handle_movement(self, key):
        """Handle movement."""
        new_x, new_y = self.player_x, self.player_y
        
        if key == pygame.K_UP:
            new_y -= 1
        elif key == pygame.K_DOWN:
            new_y += 1
        elif key == pygame.K_LEFT:
            new_x -= 1
        elif key == pygame.K_RIGHT:
            new_x += 1
        
        if self.is_valid_move(new_x, new_y):
            self.player_x = new_x
            self.player_y = new_y
            
            if self.player_x == self.end_x and self.player_y == self.end_y:
                self.stage_completed()
    
    def is_valid_move(self, x, y):
        """Check if move is valid."""
        if y < 0 or y >= len(self.maze):
            return False
        if x < 0 or x >= len(self.maze[y]):
            return False
        return self.maze[y][x] != '#'
    
    def stage_completed(self):
        """Handle stage completion."""
        print(f"Stage {self.current_stage} completed!")
        
        if self.current_stage >= self.total_stages:
            self.game_state = STATE_GAME_COMPLETE
        else:
            self.game_state = STATE_STAGE_COMPLETE
    
    def next_stage(self):
        """Load next stage."""
        self.current_stage += 1
        if self.current_stage <= self.total_stages:
            self.load_stage(self.current_stage)
        else:
            self.game_state = STATE_GAME_COMPLETE
    
    def restart_game(self):
        """Restart game."""
        self.current_stage = 1
        self.load_stage(self.current_stage)
    
    def draw(self):
        """Draw the screen."""
        self.screen.fill(WHITE)
        
        if self.game_state == STATE_PLAYING:
            self.draw_maze()
            self.draw_ui()
        elif self.game_state == STATE_STAGE_COMPLETE:
            self.draw_stage_complete_popup()
        elif self.game_state == STATE_GAME_COMPLETE:
            self.draw_game_complete_popup()
        
        pygame.display.flip()
    
    def draw_maze(self):
        """Draw the maze."""
        maze_width = len(self.maze[0]) * CELL_SIZE
        maze_height = len(self.maze) * CELL_SIZE
        offset_x = (SCREEN_WIDTH - maze_width) // 2
        offset_y = (SCREEN_HEIGHT - maze_height) // 2 - 30
        
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                rect = pygame.Rect(
                    offset_x + x * CELL_SIZE,
                    offset_y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                
                if cell == '#':
                    pygame.draw.rect(self.screen, BLACK, rect)
                    pygame.draw.rect(self.screen, GRAY, rect, 1)
                else:
                    pygame.draw.rect(self.screen, WHITE, rect)
                    pygame.draw.rect(self.screen, LIGHT_GRAY, rect, 1)
                
                if x == self.end_x and y == self.end_y:
                    pygame.draw.rect(self.screen, GREEN, rect)
        
        player_rect = pygame.Rect(
            offset_x + self.player_x * CELL_SIZE,
            offset_y + self.player_y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.circle(self.screen, BLUE, player_rect.center, CELL_SIZE // 3)
    
    def draw_ui(self):
        """Draw UI."""
        stage_text = self.font.render(
            f"Stage {self.current_stage}/{self.total_stages} [DEV MODE]",
            True,
            BLACK
        )
        self.screen.blit(stage_text, (10, 10))
        
        instruction_text = self.small_font.render(
            "Use arrow keys to move",
            True,
            GRAY
        )
        self.screen.blit(instruction_text, (10, SCREEN_HEIGHT - 30))
    
    def draw_stage_complete_popup(self):
        """Draw stage complete popup."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (0, 0))
        
        popup_width = 400
        popup_height = 200
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2
        
        pygame.draw.rect(self.screen, LIGHT_GRAY, (popup_x, popup_y, popup_width, popup_height), border_radius=10)
        pygame.draw.rect(self.screen, BLACK, (popup_x, popup_y, popup_width, popup_height), 3, border_radius=10)
        
        congrats_text = self.font.render("Congratulations!", True, DARK_GREEN)
        text_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, popup_y + 60))
        self.screen.blit(congrats_text, text_rect)
        
        stage_text = self.small_font.render(f"You completed Stage {self.current_stage}!", True, BLACK)
        text_rect = stage_text.get_rect(center=(SCREEN_WIDTH // 2, popup_y + 100))
        self.screen.blit(stage_text, text_rect)
        
        button_width = 150
        button_height = 40
        button_x = (SCREEN_WIDTH - button_width) // 2
        button_y = popup_y + 140
        
        self.continue_button = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, GREEN, self.continue_button, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.continue_button, 2, border_radius=5)
        
        button_text = self.font.render("Continue", True, WHITE)
        text_rect = button_text.get_rect(center=self.continue_button.center)
        self.screen.blit(button_text, text_rect)
    
    def draw_game_complete_popup(self):
        """Draw game complete popup."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (0, 0))
        
        popup_width = 500
        popup_height = 250
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2
        
        pygame.draw.rect(self.screen, LIGHT_GRAY, (popup_x, popup_y, popup_width, popup_height), border_radius=10)
        pygame.draw.rect(self.screen, BLACK, (popup_x, popup_y, popup_width, popup_height), 3, border_radius=10)
        
        congrats_text = self.font.render("🎉 GAME COMPLETE! 🎉", True, DARK_GREEN)
        text_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, popup_y + 60))
        self.screen.blit(congrats_text, text_rect)
        
        complete_text = self.small_font.render(f"You completed all {self.total_stages} stages!", True, BLACK)
        text_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, popup_y + 100))
        self.screen.blit(complete_text, text_rect)
        
        done_text = self.small_font.render("Well done, maze master!", True, BLACK)
        text_rect = done_text.get_rect(center=(SCREEN_WIDTH // 2, popup_y + 130))
        self.screen.blit(done_text, text_rect)
        
        button_width = 180
        button_height = 40
        button_x = (SCREEN_WIDTH - button_width) // 2
        button_y = popup_y + 180
        
        self.continue_button = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, GREEN, self.continue_button, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.continue_button, 2, border_radius=5)
        
        button_text = self.font.render("Play Again", True, WHITE)
        text_rect = button_text.get_rect(center=self.continue_button.center)
        self.screen.blit(button_text, text_rect)
    
    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        self.cleanup()
    
    def cleanup(self):
        """Cleanup."""
        self.db_handler.disconnect()
        pygame.quit()


def main():
    """Main entry point."""
    print("===================================")
    print("Maze Game - Local Development Mode")
    print("===================================")
    print("This version runs without AWS infrastructure")
    print("Use arrow keys to navigate")
    print("")
    
    game = MazeGame()
    
    if not game.initialize():
        print("Failed to initialize game")
        sys.exit(1)
    
    game.run()


if __name__ == "__main__":
    main()
