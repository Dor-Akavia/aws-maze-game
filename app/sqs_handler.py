import boto3
import json
import os
from typing import Optional, Dict
import threading
import time


class SQSHandler:
    """Handles SQS communication for player movements."""
    
    def __init__(self):
        self.sqs_client = boto3.client(
            'sqs',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.queue_url = os.getenv('SQS_QUEUE_URL')
        self.running = False
        self.listener_thread = None
        self.movement_callback = None
        
    def send_movement(self, direction: str, player_x: int, player_y: int, stage: int) -> bool:
        """
        Send player movement to SQS queue.
        
        Args:
            direction: Movement direction (UP, DOWN, LEFT, RIGHT)
            player_x: Current player X position
            player_y: Current player Y position
            stage: Current stage number
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            message_body = {
                'direction': direction,
                'player_x': player_x,
                'player_y': player_y,
                'stage': stage,
                'timestamp': time.time()
            }
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            print(f"Movement sent to SQS: {direction} at ({player_x}, {player_y})")
            return True
        except Exception as e:
            print(f"Error sending message to SQS: {e}")
            return False
    
    def receive_movement(self) -> Optional[Dict]:
        """
        Receive a single movement message from SQS queue.
        
        Returns:
            Dictionary containing movement data or None
        """
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5
            )
            
            if 'Messages' in response:
                message = response['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                
                # Parse message body
                message_data = json.loads(message['Body'])
                
                # Delete message from queue
                self.sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
                
                return message_data
            return None
        except Exception as e:
            print(f"Error receiving message from SQS: {e}")
            return None
    
    def start_listener(self, callback):
        """
        Start a background thread to listen for SQS messages.
        
        Args:
            callback: Function to call when a message is received
        """
        self.movement_callback = callback
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        print("SQS listener started")
    
    def stop_listener(self):
        """Stop the SQS listener thread."""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=2)
        print("SQS listener stopped")
    
    def _listen_loop(self):
        """Internal loop for listening to SQS messages."""
        while self.running:
            try:
                message = self.receive_movement()
                if message and self.movement_callback:
                    self.movement_callback(message)
            except Exception as e:
                print(f"Error in SQS listener loop: {e}")
                time.sleep(1)
    
    def purge_queue(self):
        """Purge all messages from the queue (useful for testing)."""
        try:
            self.sqs_client.purge_queue(QueueUrl=self.queue_url)
            print("SQS queue purged")
            return True
        except Exception as e:
            print(f"Error purging queue: {e}")
            return False
