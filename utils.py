import json
import re
from datetime import datetime

class Utils:
    """Helper functions for BetBolt"""
    
    @staticmethod
    def safe_float(value, default=0.0):
        """Safely convert to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value, default=0):
        """Safely convert to int"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def format_currency(amount, currency='USD'):
        """Format currency values"""
        return f"{currency} {amount:.2f}"
    
    @staticmethod
    def extract_league_from_text(text):
        """Extract league name from user message"""
        # Simple league detection
        leagues = {
            'premier': 'england_premier_league',
            'epl': 'england_premier_league',
            'la liga': 'spain_la_liga',
            'laliga': 'spain_la_liga',
            'serie a': 'italy_serie_a',
            'seriea': 'italy_serie_a',
            'bundesliga': 'germany_bundesliga',
            'ligue 1': 'france_ligue_one',
            'eredivisie': 'netherlands_eredivisie',
            'primeira': 'portugal_primeira_liga',
            'brasileirão': 'brazil_campeonato',
            'brasileirao': 'brazil_campeonato'
        }
        
        text_lower = text.lower()
        for key, value in leagues.items():
            if key in text_lower:
                return value
        
        return None
    
    @staticmethod
    def is_valid_command(text):
        """Check if text is a valid bot command"""
        command_pattern = r'^/[a-zA-Z0-9_]+'
        return bool(re.match(command_pattern, text))
