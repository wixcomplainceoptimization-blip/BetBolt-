import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for BetBolt bot"""
    
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    # API Configuration
    ODDS_API_KEY = os.getenv('ODDS_API_KEY')
    if not ODDS_API_KEY:
        raise ValueError("ODDS_API_KEY not found in environment variables")
    
    ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
    ODDS_API_SPORT = "soccer"  # or "basketball", "baseball", etc.
    
    # Default Settings
    DEFAULT_LEAGUES = os.getenv('DEFAULT_LEAGUES', 'england_premier_league,spain_la_liga,italy_serie_a').split(',')
    REFRESH_INTERVAL = int(os.getenv('REFRESH_INTERVAL', '300'))
    
    # Bot Settings
    MAX_PREDICTIONS_DISPLAY = 5
    CACHE_TIMEOUT = 60  # seconds
    
    # Supported Bookmakers
    SUPPORTED_BOOKMAKERS = ['pinnacle', 'bet365', 'williamhill', 'unibet']
    
    # League Name Mappings for display
    LEAGUE_NAMES = {
        'england_premier_league': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League',
        'spain_la_liga': '🇪🇸 La Liga',
        'italy_serie_a': '🇮🇹 Serie A',
        'germany_bundesliga': '🇩🇪 Bundesliga',
        'france_ligue_one': '🇫🇷 Ligue 1',
        'netherlands_eredivisie': '🇳🇱 Eredivisie',
        'portugal_primeira_liga': '🇵🇹 Primeira Liga',
        'brazil_campeonato': '🇧🇷 Brasileirão',
    }
