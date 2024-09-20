import sqlite3
from datetime import datetime
import pytz 

def to_est(dt_str):
    """Convert a UTC datetime string to EST/EDT timezone."""
    utc_time = datetime.strptime(dt_str[:-1], "%Y-%m-%dT%H:%M:%S") if dt_str.endswith('Z') else datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    est = pytz.timezone('US/Eastern')
    return utc_time.astimezone(est)

def store_odds(data):
    conn = sqlite3.connect('odds.db')
    c = conn.cursor()
    
    for game in data:
        commence_dttm = to_est(game['commence_time'])
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Assume odds for home and away teams are in 'bookmakers' -> 'outcomes' in the game data
        for bookmaker in game['bookmakers']:
            if bookmaker['key'] == 'pinnacle':
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':  # Assuming 'h2h' contains the home and away team odds
                        odds_home = market['outcomes'][0]['price']  # First outcome is home team
                        odds_away = market['outcomes'][1]['price']  # Second outcome is away team
                        
                        # Insert the relevant data into the table
                        c.execute('INSERT OR REPLACE INTO pinnacle_lines (event_time, home_team, away_team, odds_home_team, odds_away_team) VALUES (?, ?, ?, ?, ?)', 
                                  (commence_dttm, home_team, away_team, odds_home, odds_away))
    
    conn.commit()
    conn.close()


def remove_commenced_games():
    conn = sqlite3.connect('odds.db')
    c = conn.cursor()
    
    # Get current time in EST/EDT
    current_time = datetime.now(pytz.timezone('US/Eastern'))
    
    # Remove games that have already commenced
    c.execute('DELETE FROM pinnacle_lines WHERE event_time < ?', (current_time,))
    
    conn.commit()
    conn.close()

def process_db(data):
    remove_commenced_games()
    store_odds(data)
