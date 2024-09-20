from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from scripts.get_data import fetch_odds,process_games 
from scripts.dbactions import process_db
import json 
from datetime import datetime

app = Flask(__name__)

def retrieve_data(): 
    quota = 0
    sports = ['americanfootball_nfl']
    processed_sports = {}
    
    for sport in sports:
        # Fetch odds and ensure two values are always returned, default quota_last_used to 0 if not returned
        result = fetch_odds(sport)
        if isinstance(result, tuple):
            curr_data, quota_last_used = result
        else:
            curr_data, quota_last_used = result, 0
        
        quota += quota_last_used
        
        # Process data into the database
        process_db(curr_data)
        
        # Process games, not database, to get the processed games
        processed_games = process_games(curr_data)
        
        # Add processed games to the results
        processed_sports[sport] = processed_games     
        processed_sports['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Write the processed games to a JSON file
    with open('data/processed_games.json', 'w') as f:
        json.dump(processed_sports, f)
    
    print("Last used quota: " + str(quota))
    
@app.route('/')
def home():
    sport_key = request.args.get('sport', 'baseball_mlb')
    
    games = fetch_odds(sport_key)
    
    # # Print the games to check the structure of the data
    # print(games)
    
    if games is None or isinstance(games, str):
        # Handle the case where games is not valid
        print(f"Error fetching games: {games}")
        return render_template('error.html', message="Failed to fetch game data.")
    
    # Process the games if valid
    processed_games = process_games(games)
    print("Fetched odds")
    
    # Load processed games from the file
    with open('data/processed_games.json', 'r') as f:
        data = json.load(f)
        
    return render_template('odds.html', games=processed_games, sport=sport_key, last_updated=data['last_update'])

#Initial run
retrieve_data()

# Setup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=retrieve_data, trigger="interval", minutes=20)
scheduler.start()
