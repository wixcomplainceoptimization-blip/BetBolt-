import requests
import json
import time
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
        self.session = requests.Session()  # Use session for better performance
        
    @cached(cache)
    def get_sports(self):
        """Get list of available sports"""
        url = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("⚠️ API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching sports: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return []
    
    @cached(cache)
    def get_odds(self, sport='soccer', region='eu', markets='h2h'):
        """Get odds for a specific sport with better error handling"""
        try:
            url = f"{self.base_url}/sports/{sport}/odds"
            params = {
                'apiKey': self.api_key,
                'region': region,
                'markets': markets,
                'dateFormat': 'iso'
            }
            
            print(f"🔍 Fetching odds from: {url}")  # Debug log
            
            response = self.session.get(url, params=params, timeout=15)
            
            # Check if we hit rate limit
            if response.status_code == 429:
                print("⚠️ Rate limit hit! Waiting 5 seconds...")
                time.sleep(5)
                # Try again once
                response = self.session.get(url, params=params, timeout=15)
            
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Fetched {len(data)} matches")  # Debug log
            return data
            
        except requests.exceptions.Timeout:
            print("⚠️ API request timed out")
            return []
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("❌ Invalid API key! Please check your ODDS_API_KEY")
            elif response.status_code == 404:
                print("❌ Sport not found. Check the sport parameter")
            else:
                print(f"❌ HTTP error: {e}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON response: {e}")
            return []
    
    def get_predictions(self, matches):
        """Analyze matches and generate predictions with safe handling"""
        if not matches:
            print("⚠️ No matches provided for predictions")
            return []
        
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
                    if bookmaker.get('key') not in Config.SUPPORTED_BOOKMAKERS:
                        continue
                    
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'h2h':
                            outcomes = market.get('outcomes', [])
                            for outcome in outcomes:
                                outcome_name = outcome.get('name', '')
                                price = outcome.get('price', 0)
                                
                                if outcome_name == match.get('home_team', ''):
                                    best_home = max(best_home, price)
                                elif outcome_name == match.get('away_team', ''):
                                    best_away = max(best_away, price)
                                elif outcome_name == 'Draw':
                                    best_draw = max(best_draw, price)
                
                # Calculate implied probabilities
                if best_home > 0 and best_away > 0 and best_draw > 0:
                    home_prob = (1 / best_home) * 100
                    draw_prob = (1 / best_draw) * 100
                    away_prob = (1 / best_away) * 100
                    
                    # Normalize to 100%
                    total = home_prob + draw_prob + away_prob
                    if total > 0:
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
                        'match': f"{match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}",
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
                print(f"❌ Error analyzing match: {e}")
                continue
        
        # Sort by confidence (highest first)
        predictions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return predictions
    
    def format_prediction_message(self, prediction, index=0):
        """Format a single prediction for display with safe access"""
        try:
            emoji = '🏆' if index == 0 else '⭐'
            
            message = f"""
{emoji} *{prediction.get('match', 'Unknown Match')}*
📊 *League:* {prediction.get('league', 'Unknown League')}

*Best Odds:*
• Home: {prediction.get('best_odds', {}).get('home', 0):.2f}
• Draw: {prediction.get('best_odds', {}).get('draw', 0):.2f}
• Away: {prediction.get('best_odds', {}).get('away', 0):.2f}

*Probabilities:*
• Home: {prediction.get('probabilities', {}).get('home', 0)}%
• Draw: {prediction.get('probabilities', {}).get('draw', 0)}%
• Away: {prediction.get('probabilities', {}).get('away', 0)}%

🎯 *Prediction:* {prediction.get('prediction', 'Unknown')}
📈 *Confidence:* {prediction.get('confidence', 0)}%
"""
            
            if prediction.get('commence_time'):
                try:
                    start_time = datetime.fromisoformat(prediction['commence_time'].replace('Z', '+00:00'))
                    time_str = start_time.strftime('%Y-%m-%d %H:%M UTC')
                    message += f"\n⏰ *Match Time:* {time_str}"
                except:
                    pass
            
            return message
        except Exception as e:
            print(f"❌ Error formatting message: {e}")
            return "⚠️ Error formatting prediction"
