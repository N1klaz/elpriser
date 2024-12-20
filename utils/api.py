import requests
from datetime import datetime, timedelta

class ElprisAPI:
    """API client for fetching electricity prices from elprisetjustnu.se"""
    
    BASE_URL = "https://www.elprisetjustnu.se/api/v1/prices/{year}/{date}_SE{region}.json"
    
    @staticmethod
    def fetch_prices(date=None, region=3):
        """
        Fetch electricity prices for a specific date and region
        
        Args:
            date (datetime, optional): Date to fetch prices for. Defaults to today
            region (int, optional): Price region (1-4). Defaults to 3 (Stockholm)
        """
        if date is None:
          date = datetime.now()
        
     # Check if date is more than one day in the future
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        if date.date() > tomorrow.date():
            return None
        
        try:
            response = requests.get(ElprisAPI.BASE_URL.format(
                year=date.year,
                date=date.strftime("%m-%d"),
                region=region
            ))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return None     
    
    @staticmethod
    def fetch_prices_tomorrow(region=3):
        """
        Fetch electricity prices for tomorrow if available
        Note: Tomorrow's prices are typically published around 13:00
        
        Args:
            region (int): Price region (1-4)
        """
        tomorrow = datetime.now() + timedelta(days=1)
        
        # Only try to fetch tomorrow's prices after 13:00
        if datetime.now().hour >= 13:
            return ElprisAPI.fetch_prices(tomorrow, region)
        return None
    
    @staticmethod
    def fetch_yesterday_prices(region=3):
        """
        Fetch electricity prices for yesterday
        """
        yesterday = datetime.now() - timedelta(days=1)
        return ElprisAPI.fetch_prices(yesterday, region)