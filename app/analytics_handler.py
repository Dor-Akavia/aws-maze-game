import boto3
import json
import os
import time
from typing import Optional


class AnalyticsHandler:
    """Handles sending game analytics to SQS (async logging)."""
    
    def __init__(self):
        self.sqs_client = boto3.client(
            'sqs',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.queue_url = os.getenv('SQS_QUEUE_URL')
        self.player_id = os.getenv('PLAYER_ID', 'anonymous')
        
        if not self.queue_url:
            print("Warning: SQS_QUEUE_URL not set. Analytics will not be sent.")
    
    def send_level_complete(self, stage_number: int, time_taken: float, moves_count: int) -> bool:
        """
        Send level completion analytics to SQS.
        
        Args:
            stage_number: The completed stage number
            time_taken: Time taken to complete (in seconds)
            moves_count: Number of moves made
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.queue_url:
            return False
        
        try:
            message_body = {
                'event_type': 'level_complete',
                'player_id': self.player_id,
                'stage_number': stage_number,
                'time_taken': time_taken,
                'moves_count': moves_count,
                'timestamp': time.time()
            }
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            print(f"Analytics sent: Stage {stage_number} completed in {time_taken:.1f}s with {moves_count} moves")
            return True
            
        except Exception as e:
            print(f"Error sending analytics to SQS: {e}")
            return False
    
    def send_game_complete(self, total_time: float, total_moves: int) -> bool:
        """
        Send game completion analytics to SQS.
        
        Args:
            total_time: Total time for all stages
            total_moves: Total moves made
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.queue_url:
            return False
        
        try:
            message_body = {
                'event_type': 'game_complete',
                'player_id': self.player_id,
                'total_time': total_time,
                'total_moves': total_moves,
                'timestamp': time.time()
            }
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            print(f"Game complete analytics sent: {total_time:.1f}s, {total_moves} moves")
            return True
            
        except Exception as e:
            print(f"Error sending game complete analytics: {e}")
            return False
    
    def send_game_start(self) -> bool:
        """
        Send game start event to SQS.
        
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.queue_url:
            return False
        
        try:
            message_body = {
                'event_type': 'game_start',
                'player_id': self.player_id,
                'timestamp': time.time()
            }
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            print("Game start event sent")
            return True
            
        except Exception as e:
            print(f"Error sending game start event: {e}")
            return False
