import requests
import os
from typing import Optional, Dict


class APIClient:
    """Handles communication with the API Gateway / Lambda backend."""
    
    def __init__(self):
        self.api_url = os.getenv('API_GATEWAY_URL')
        if not self.api_url:
            raise ValueError("API_GATEWAY_URL not set in environment variables")
        
        # Remove trailing slash if present
        self.api_url = self.api_url.rstrip('/')
        
    def get_level_data(self, stage_number: int) -> Optional[Dict]:
        """
        Fetch level data from the API.
        
        Args:
            stage_number: The stage number to retrieve (1-10)
            
        Returns:
            Dictionary containing stage data or None if failed
        """
        try:
            url = f"{self.api_url}/{stage_number}"
            print(f"Fetching level data from: {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success'):
                print(f"Successfully loaded stage {stage_number}")
                return data.get('data')
            else:
                print(f"API returned error: {data.get('error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching level data: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the API connection by fetching stage 1.
        
        Returns:
            True if connection successful, False otherwise
        """
        print(f"Testing API connection to: {self.api_url}")
        data = self.get_level_data(1)
        return data is not None
