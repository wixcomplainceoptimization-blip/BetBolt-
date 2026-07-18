import requests
import json
from datetime import datetime, timedelta
from cachetools import cached, TTLCache
from config import Config

# Cache to reduce API calls
cache = TTLCache(maxsize=100, ttl=Config.CACHE_TIMEOUT)

class OddsAPI:
    """Handles all API calls to The Odds API"""
    
    def __init__(self):
        self.api_key = Config.ODDS_API_KEY
        self.base_url = Config.ODDS_API_BASE_URL
    
    @cached(cache)
    def get_sports(self):
        """Get list of available sports"""
        url = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching sports: {e}")
            return []
    
    @cached(cache)
    def get_odds(self, sport='soccer', region='eu', markets='h2h'):
        """Get odds for a specific sport"""
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'region': region,
            'markets': markets,
            'dateFormat': 'iso'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching odds: {e}")
            return []
    
    def get_predictions(self, matches):
        """Analyze matches and generate predictions"""
        predictions = []
        
        for match in matches:
            try:
                # Skip if no bookmakers
                if not match.get('bookmakers'):
                    continue
                
                # Get the best odds for each outcome
                best_home = 0
                best_away = 0
                best_draw = 0
                
                for bookmaker in match['bookmakers']:
                    if bookmaker['key'] not in Config.SUPPORTED_BOOKMAKERS:
                        continue
                    
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            outcomes = market['outcomes']
                            for outcome in outcomes:
                                if outcome['name'] == match['home_team']:
                                    best_home = max(best_home, outcome['price'])
                                elif outcome['name'] == match['away_team']:
                                    best_away = max(best_away, outcome['price'])
                                elif outcome['name'] == 'Draw':
                                    best_draw = max(best_draw, outcome['price'])
                
                # Calculate implied probabilities
                if best_home > 0 and best_away > 0 and best_draw > 0:
                    home_prob = (1 / best_home) * 100
                    draw_prob = (1 / best_draw) * 100
                    away_prob = (1 / best_away) * 100
                    
                    # Normalize to 100%
                    total = home_prob + draw_prob + away_prob
                    home_prob = (home_prob / total) * 100
                    draw_prob = (draw_prob / total) * 100
                    away_prob = (away_prob / total) * 100
                    
                    # Determine prediction
                    outcomes = [
                        ('Home Win', home_prob, best_home),
                        ('Draw', draw_prob, best_draw),
                        ('Away Win', away_prob, best_away)
                    ]
                    outcomes.sort(key=lambda x: x[1], reverse=True)
                    
                    # Calculate confidence level
                    confidence = outcomes[0][1] - outcomes[1][1]
                    
                    predictions.append({
                        'match': f"{match['home_team']} vs {match['away_team']}",
                        'league': match.get('sport_title', 'Unknown League'),
                        'best_odds': {
                            'home': best_home,
                            'draw': best_draw,
                            'away': best_away
                        },
                        'probabilities': {
                            'home': round(home_prob, 1),
                            'draw': round(draw_prob, 1),
                            'away': round(away_prob, 1)
                        },
                        'prediction': outcomes[0][0],
                        'confidence': round(confidence, 1),
                        'commence_time': match.get('commence_time')
                    })
            
            except Exception as e:
                print(f"Error analyzing match: {e}")
                continue
        
        # Sort by confidence (highest first)
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return predictions
    
    def format_prediction_message(self, prediction, index=0):
        """Format a single prediction for display"""
        emoji = '🏆' if index == 0 else '⭐'
        
        message = f"""
{emoji} *{prediction['match']}*
📊 *League:* {prediction['league']}

*Best Odds:*
• Home: {prediction['best_odds']['home']:.2f}
• Draw: {prediction['best_odds']['draw']:.2f}
• Away: {prediction['best_odds']['away']:.2f}

*Probabilities:*
• Home: {prediction['probabilities']['home']}%
• Draw: {prediction['probabilities']['draw']}%
• Away: {prediction['probabilities']['away']}%

🎯 *Prediction:* {prediction['prediction']}
📈 *Confidence:* {prediction['confidence']}%
"""
        
        if prediction.get('commence_time'):
            try:
                start_time = datetime.fromisoformat(prediction['commence_time'].replace('Z', '+00:00'))
                time_str = start_time.strftime('%Y-%m-%d %H:%M UTC')
                message += f"\n⏰ *Match Time:* {time_str}"
            except:
                pass
        
        return message
