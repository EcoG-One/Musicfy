import json
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import schedule
import time
from threading import Thread

app = Flask(__name__)

# Twilio setup
account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
client = Client(account_sid, auth_token)

# Spotify setup
sp_oauth = SpotifyOAuth('your_client_id', 'your_client_secret', 'your_redirect_uri')
sp = spotipy.Spotify(auth_manager=sp_oauth)

# Mistral AI setup
mistral_api_key = 'your_mistral_api_key'
mistral_url = 'https://api.mistralai.com/your_endpoint'

# JSON storage
users_file = 'users.json'

def load_users():
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {"users": {}}

def save_users(data):
    with open(users_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_playlist_suggestions(user_input):
    response = requests.post(mistral_url, json={'input': user_input}, headers={'Authorization': f'Bearer {mistral_api_key}'})
    return response.json()

def create_spotify_playlist(suggestions):
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, 'Generated Playlist')
    playlist_id = playlist['id']

    # Add tracks to the playlist
    track_ids = [track['id'] for track in suggestions]
    sp.playlist_add_items(playlist_id, track_ids)

    return playlist['external_urls']['spotify']

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    msg = request.form.get('Body')
    from_number = request.form.get('From')
    resp = MessagingResponse()
    msg_resp = resp.message()

    # Load users data
    users_data = load_users()

    # Process the message with Mistral AI
    suggestions = get_playlist_suggestions(msg)

    # Create a Spotify playlist
    playlist_url = create_spotify_playlist(suggestions)

    # Store the playlist URL for the user
    users_data["users"][from_number] = playlist_url
    save_users(users_data)

    # Send the playlist link back to the user
    msg_resp.body(f'Here is your playlist: {playlist_url}')
    return str(resp)

def daily_playlist_creation():
    users_data = load_users()
    for user, playlist_url in users_data["users"].items():
        # Create a new playlist for the user
        suggestions = get_playlist_suggestions("daily playlist")
        new_playlist_url = create_spotify_playlist(suggestions)

        # Update the user's playlist URL
        users_data["users"][user] = new_playlist_url

        # Send the new playlist link to the user via WhatsApp
        client.messages.create(
            body=f'Here is your daily playlist: {new_playlist_url}',
            from_='whatsapp:+14155238886',
            to=user
        )

    save_users(users_data)

# Schedule the daily playlist creation
schedule.every().day.at("09:00").do(daily_playlist_creation)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.start()
    app.run(debug=True)