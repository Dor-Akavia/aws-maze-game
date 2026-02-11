import psycopg2
from typing import Optional, Dict, List
import os


class DatabaseHandler:
    """Handles all database operations for the maze game."""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT', 5432),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            self.cursor = self.connection.cursor()
            print("Database connection established successfully")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def get_stage(self, stage_number: int) -> Optional[Dict]:
        """
        Retrieve a specific maze stage from the database.
        
        Args:
            stage_number: The stage number to retrieve (1-10)
            
        Returns:
            Dictionary containing stage data or None if not found
        """
        try:
            query = """
                SELECT stage_id, stage_number, layout, width, height, 
                       start_x, start_y, end_x, end_y
                FROM maze_stages
                WHERE stage_number = %s
            """
            self.cursor.execute(query, (stage_number,))
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
            print(f"Error retrieving stage: {e}")
            return None
    
    def get_all_stages(self) -> List[Dict]:
        """Retrieve all maze stages from the database."""
        try:
            query = """
                SELECT stage_id, stage_number, layout, width, height, 
                       start_x, start_y, end_x, end_y
                FROM maze_stages
                ORDER BY stage_number
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            stages = []
            for result in results:
                stages.append({
                    'stage_id': result[0],
                    'stage_number': result[1],
                    'layout': result[2],
                    'width': result[3],
                    'height': result[4],
                    'start_x': result[5],
                    'start_y': result[6],
                    'end_x': result[7],
                    'end_y': result[8]
                })
            return stages
        except Exception as e:
            print(f"Error retrieving all stages: {e}")
            return []
    
    def save_player_progress(self, player_name: str, current_stage: int, completed_stages: int):
        """Save or update player progress."""
        try:
            query = """
                INSERT INTO player_progress (player_name, current_stage, completed_stages, last_played)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (player_name)
                DO UPDATE SET 
                    current_stage = EXCLUDED.current_stage,
                    completed_stages = EXCLUDED.completed_stages,
                    last_played = EXCLUDED.last_played
            """
            self.cursor.execute(query, (player_name, current_stage, completed_stages))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error saving player progress: {e}")
            self.connection.rollback()
            return False
