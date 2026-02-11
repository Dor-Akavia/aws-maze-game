import pygame
import sys
import os
import time
from dotenv import load_dotenv
from api_client import APIClient
from analytics_handler import AnalyticsHandler

# Load environment variables
load_dotenv()

# Game constants
SCREEN_WIDTH = int(os.getenv('SCREEN_WIDTH', 800))
SCREEN_HEIGHT = int(os.getenv('SCREEN_HEIGHT', 600))
CELL_SIZE = int(os.getenv('CELL_SIZE', 30))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GREEN = (0, 150, 0)
YELLOW = (255, 200, 0)

# Game states
STATE_PLAYING = "playing"
STATE_STAGE_COMPLETE = "stage_complete"
STATE_GAME_COMPLETE = "game_complete"


class MazeGame:
    """
    Main game class with Local-First architecture.
    
    - Movement is calculated locally (instant, no network delay)
    - Levels are fetched from API Gateway/Lambda at stage start
    - Analytics are sent to SQS asynchronously (fire and forget)
    """
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Maze Game - Local First")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Initialize API client and analytics handler
        self.api_client = APIClient()
        self.analytics = AnalyticsHandler()
        
        # Game state
        self.current_stage = 1
        self.total_stages = 10
        self.stage_data = None
        self.maze = []
        self.player_x = 0
        self.player_y = 0
        self.end_x = 0
        self.end_y = 0
        self.game_state = STATE_PLAYING
        self.running = True
        
        # Timing and statistics
        self.stage_start_time = 0
        self.stage_moves = 0
        self.total_moves = 0
        self.game_start_time = 0
        
        # UI elements
        self.continue_button = None
        
    def initialize(self):
        """Initialize the game by testing API connection and loading first stage."""
        print("=" * 50)
        print("Maze Game - Local-First Architecture")
        print("=" * 50)
        
        # Test API connection
        if not self.api_client.test_connection():
            print("\nERROR: Failed to connect to API")
            print("Please check your API_GATEWAY_URL in .env file")
            return False
        
        print("\n✓ API connection successful")
        
        # Send game start event
        self.game_start_time = time.time()
        self.analytics.send_game_start()
        
        # Load first stage
        return self.load_stage(self.current_stage)
    
    def load_stage(self, stage_number):
        """Load a specific stage from the API."""
        print(f"\nLoading stage {stage_number}...")
        
        # Fetch level data from API
        self.stage_data = self.api_client.get_level_data(stage_number)
        if not self.stage_data:
            print(f"Failed to load stage {stage_number}")
            return False
        
        # Parse maze layout
        self.maze = []
        lines = self.stage_data['layout'].strip().split('\n')
        for line in lines:
            self.maze.append(list(line))
        
        # Set player and end positions
        self.player_x = self.stage_data['start_x']
        self.player_y = self.stage_data['start_y']
        self.end_x = self.stage_data['end_x']
        self.end_y = self.stage_data['end_y']
        
        # Reset stage statistics
        self.stage_start_time = time.time()
        self.stage_moves = 0
        
        self.game_state = STATE_PLAYING
        print(f"✓ Stage {stage_number} loaded and ready")
        return True
    
    def handle_events(self):
        """Handle pygame events."""
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
        """
        Handle player movement locally (instant, no network delay).
        This is the core of the local-first architecture.
        """
        new_x, new_y = self.player_x, self.player_y
        
        if key == pygame.K_UP:
            new_y -= 1
        elif key == pygame.K_DOWN:
            new_y += 1
        elif key == pygame.K_LEFT:
            new_x -= 1
        elif key == pygame.K_RIGHT:
            new_x += 1
        else:
            return  # Not an arrow key
        
        # Validate move locally (instant collision detection)
        if self.is_valid_move(new_x, new_y):
            self.player_x = new_x
            self.player_y = new_y
            self.stage_moves += 1
            self.total_moves += 1
            
            # Check if player reached the end
            if self.player_x == self.end_x and self.player_y == self.end_y:
                self.stage_completed()
    
    def is_valid_move(self, x, y):
        """Check if a move to position (x, y) is valid (local collision detection)."""
        if y < 0 or y >= len(self.maze):
            return False
        if x < 0 or x >= len(self.maze[y]):
            return False
        
        cell = self.maze[y][x]
        return cell != '#'
    
    def stage_completed(self):
        """Handle stage completion and send analytics asynchronously."""
        stage_time = time.time() - self.stage_start_time
        
        print(f"\n✓ Stage {self.current_stage} completed!")
        print(f"  Time: {stage_time:.1f}s")
        print(f"  Moves: {self.stage_moves}")
        
        # Send analytics to SQS (async, fire and forget)
        self.analytics.send_level_complete(
            self.current_stage,
            stage_time,
            self.stage_moves
        )
        
        if self.current_stage >= self.total_stages:
            self.game_state = STATE_GAME_COMPLETE
            total_time = time.time() - self.game_start_time
            self.analytics.send_game_complete(total_time, self.total_moves)
        else:
            self.game_state = STATE_STAGE_COMPLETE
    
    def next_stage(self):
        """Load the next stage."""
        self.current_stage += 1
        if self.current_stage <= self.total_stages:
            self.load_stage(self.current_stage)
        else:
            self.game_state = STATE_GAME_COMPLETE
    
    def restart_game(self):
        """Restart the game from stage 1."""
        self.current_stage = 1
        self.total_moves = 0
        self.game_start_time = time.time()
        self.analytics.send_game_start()
        self.load_stage(self.current_stage)
    
    def draw(self):
        """Draw the game screen."""
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
        """Draw the maze on the screen."""
        # Calculate offset to center the maze
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
                
                # Draw end position
                if x == self.end_x and y == self.end_y:
                    pygame.draw.rect(self.screen, GREEN, rect)
        
        # Draw player
        player_rect = pygame.Rect(
            offset_x + self.player_x * CELL_SIZE,
            offset_y + self.player_y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.circle(
            self.screen,
            BLUE,
            player_rect.center,
            CELL_SIZE // 3
        )
    
    def draw_ui(self):
        """Draw UI elements."""
        # Stage number
        stage_text = self.font.render(
            f"Stage {self.current_stage}/{self.total_stages}",
            True,
            BLACK
        )
        self.screen.blit(stage_text, (10, 10))
        
        # Moves counter
        moves_text = self.small_font.render(
            f"Moves: {self.stage_moves}",
            True,
            GRAY
        )
        self.screen.blit(moves_text, (10, 50))
        
        # Timer
        elapsed = time.time() - self.stage_start_time
        timer_text = self.small_font.render(
            f"Time: {elapsed:.1f}s",
            True,
            GRAY
        )
        self.screen.blit(timer_text, (10, 75))
        
        # Instructions
        instruction_text = self.small_font.render(
            "Use arrow keys to move",
            True,
            GRAY
        )
        self.screen.blit(instruction_text, (10, SCREEN_HEIGHT - 30))
        
        # Local-first indicator
        local_text = self.small_font.render(
            "LOCAL-FIRST MODE",
            True,
            YELLOW
        )
        self.screen.blit(local_text, (SCREEN_WIDTH - 200, 10))
    
    def draw_stage_complete_popup(self):
        """Draw the stage completion popup."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (0, 0))
        
        popup_width = 400
        popup_height = 200
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2
        
        pygame.draw.rect(
            self.screen,
            LIGHT_GRAY,
            (popup_x, popup_y, popup_width, popup_height),
            border_radius=10
        )
        pygame.draw.rect(
            self.screen,
            BLACK,
            (popup_x, popup_y, popup_width, popup_height),
            3,
            border_radius=10
        )
        
        # Congratulations text
        congrats_text = self.font.render("Congratulations!", True, DARK_GREEN)
        text_rect = congrats_text.get_rect(
            center=(SCREEN_WIDTH // 2, popup_y + 60)
        )
        self.screen.blit(congrats_text, text_rect)
        
        # Stage complete text
        stage_text = self.small_font.render(
            f"You completed Stage {self.current_stage}!",
            True,
            BLACK
        )
        text_rect = stage_text.get_rect(
            center=(SCREEN_WIDTH // 2, popup_y + 100)
        )
        self.screen.blit(stage_text, text_rect)
        
        # Continue button
        button_width = 150
        button_height = 40
        button_x = (SCREEN_WIDTH - button_width) // 2
        button_y = popup_y + 140
        
        self.continue_button = pygame.Rect(
            button_x, button_y, button_width, button_height
        )
        
        pygame.draw.rect(
            self.screen,
            GREEN,
            self.continue_button,
            border_radius=5
        )
        pygame.draw.rect(
            self.screen,
            BLACK,
            self.continue_button,
            2,
            border_radius=5
        )
        
        button_text = self.font.render("Continue", True, WHITE)
        text_rect = button_text.get_rect(center=self.continue_button.center)
        self.screen.blit(button_text, text_rect)
    
    def draw_game_complete_popup(self):
        """Draw the game completion popup."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (0, 0))
        
        popup_width = 500
        popup_height = 300
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2
        
        pygame.draw.rect(
            self.screen,
            LIGHT_GRAY,
            (popup_x, popup_y, popup_width, popup_height),
            border_radius=10
        )
        pygame.draw.rect(
            self.screen,
            BLACK,
            (popup_x, popup_y, popup_width, popup_height),
            3,
            border_radius=10
        )
        
        # Congratulations text
        congrats_text = self.font.render("🎉 GAME COMPLETE! 🎉", True, DARK_GREEN)
        text_rect = congrats_text.get_rect(
            center=(SCREEN_WIDTH // 2, popup_y + 60)
        )
        self.screen.blit(congrats_text, text_rect)
        
        # Completion text
        complete_text = self.small_font.render(
            f"You completed all {self.total_stages} stages!",
            True,
            BLACK
        )
        text_rect = complete_text.get_rect(
            center=(SCREEN_WIDTH // 2, popup_y + 100)
        )
        self.screen.blit(complete_text, text_rect)
        
        # Statistics
        total_time = time.time() - self.game_start_time
        stats_text = self.small_font.render(
            f"Total moves: {self.total_moves} | Time: {total_time:.1f}s",
            True,
            BLACK
        )
        text_rect = stats_text.get_rect(
            center=(SCREEN_WIDTH // 2, popup_y + 130)
        )
        self.screen.blit(stats_text, text_rect)
        
        # Well done text
        done_text = self.small_font.render(
            "Well done, maze master!",
            True,
            BLACK
        )
        text_rect = done_text.get_rect(
            center=(SCREEN_WIDTH // 2, popup_y + 160)
        )
        self.screen.blit(done_text, text_rect)
        
        # Play again button
        button_width = 180
        button_height = 40
        button_x = (SCREEN_WIDTH - button_width) // 2
        button_y = popup_y + 220
        
        self.continue_button = pygame.Rect(
            button_x, button_y, button_width, button_height
        )
        
        pygame.draw.rect(
            self.screen,
            GREEN,
            self.continue_button,
            border_radius=5
        )
        pygame.draw.rect(
            self.screen,
            BLACK,
            self.continue_button,
            2,
            border_radius=5
        )
        
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
        """Clean up resources."""
        pygame.quit()


def main():
    """Main entry point for the game."""
    game = MazeGame()
    
    if not game.initialize():
        print("\nFailed to initialize game")
        print("\nPlease ensure:")
        print("1. You have deployed the infrastructure with Terraform")
        print("2. Your .env file has the correct API_GATEWAY_URL")
        print("3. The database has been initialized with schema.sql")
        sys.exit(1)
    
    print("\nStarting game...")
    print("Movement is LOCAL (instant, no network delay)")
    print("Analytics sent to SQS asynchronously")
    print("\nUse arrow keys to navigate the maze")
    print("=" * 50)
    
    game.run()


if __name__ == "__main__":
    main()
