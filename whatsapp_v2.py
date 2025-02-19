from twilio.rest import Client
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from flask import Flask, request
from dotenv import load_dotenv

#from save_to_file store_message

CONVERSATION_FILE = os.path.join(os.path.dirname(__file__), "conversations.json")

# Spotify credentials
load_dotenv()
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = "http://127.0.0.1:3000"
SCOPE = 'playlist-modify-public'

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "+14155238886"
#YOUR_WHATSAPP_NUMBER = "+4917660771012"

# Authenticate Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))

app = Flask(__name__)
# app.secret_key = os.urandom()

# OpenAI API setup
base_url = "https://api.aimlapi.com/v1"
api_key = "fdc7e528621d4914bc32586ced14e752"
api = OpenAI(api_key=api_key, base_url=base_url)

#KEEP FOR TESTING! The prompt needs to be specific
system_prompt = "You are an AI assistant who knows everything."

@app.route("/whatsapp/incoming", methods=['POST'])
def receive_message():
    print("Webhook received!")
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")
    print(f"Incoming message: {incoming_msg}")
    print(f"Sender (raw): {sender}")

    if not incoming_msg:
        print(f"Warning: No message received from {sender}")
        return "⚠️ No message received but connection established ✅", 200

    new_number = sender[9:]  # Extract the clean number (remove "whatsapp:")
    print(f"Sender (cleaned): {new_number}")

        # 1. Check for initial choice (songs or podcasts)
    if "songs" in incoming_msg.lower():
        media_type = "songs"
        request.media_type = media_type # Make media_type available for later requests
        response_text = "Great! You've chosen songs. Now, please provide some prompts (e.g., 'rock energetic 90s')."
        send_whatsapp_message(new_number, response_text)  # Send initial response
        return "OK", 200  # Important: Return early after initial choice

    elif "podcasts" in incoming_msg.lower():
        media_type = "podcasts"
        request.media_type = media_type # Make media_type available for later requests
        response_text = "Great! You've chosen podcasts. Now, please provide some prompts (e.g., 'crime, nature, comedy')"
        send_whatsapp_message(new_number, response_text)  # Send initial response
        return "OK", 200  # Important: Return early after initial choice
        # 2. If no initial choice is made, ask for it
    elif not hasattr(request, 'media_type'): # or if media_type is None
        response_text = "Please choose either 'songs' or 'podcasts'."
        send_whatsapp_message(new_number, response_text)
        return "OK", 200

    return "OK", 200


def process_incoming_message(message):
    message = message.lower()
    prompts = message.split()  # Split the message into individual words
    if len(prompts) > 0: # Check if there are any prompts
        return prompts
    else:
        return None  # Return None if no prompts are found


def create_user_prompt(prompts, media_type):
    """
    Creates the user prompt for the Mistral API using the extracted prompts.
    """
    prompt_string = " ".join(prompts)# Join prompts with spaces
    if media_type == "songs":
        user_prompt = (
        f"Provide a Python list named 'AI-playlist' containing 15 random only {prompt_string} songs suitable for Spotify. "
        "Each entry should be a list with two elements: the track name and the artist. "
        "Format the output as: playlist = [['track name', 'artist'], ...]"
    )
    elif media_type == "podcast":
        user_prompt = (
            f"Provide a Python list named 'AI-Podcast-Playlist' containing 15 random {prompt_string} podcasts from Spotify. "
            f"Format the output as: playlist = [['podcast name'], ...]"
        )
    return user_prompt

def search_podcast(name):
    '''
    Search for a podcast by name
    :param name: the name of the podcast to search for
    :return: the podcast uri, None if it is not found
    '''
    query = f'show:{name}'
    results = sp.search(q=query, type='show', limit=1)
    if results['shows']['items']:
        podcast = results['shows']['items'][0]
        return {
            'name': podcast['name'],
            'publisher': podcast['publisher'],
            'description': podcast['description'],
            'uri': podcast['uri']
        }
    else:
        return None

def search_song(track_name):
    '''
    Search for a song by title and artist
    :param track_name: a Tuple with the song title and artist
    :return: a Dictionary with the song name, artist, album and uri,
                None, if song not found
    '''
    title = track_name[0]
    artist = track_name [1]
    query = f'track:{title} artist:{artist}'
    results = sp.search(q=query, type='track', limit=1)
    if results['tracks']['items']:
        song = results['tracks']['items'][0]
        return {
            'name': song['name'],
            'artist': song['artists'][0]['name'],
            'album': song['album']['name'],
            'uri': song['uri']
        }
    else:
        return None


def create_track_uris(track_list, media_type):
    '''
    Transforms a song list to a URIs list.
    :param track_list: our playlist
    :return: a list of the Spotify URIs of the songs in track_list
    '''
    track_uris = []
    for track_name in track_list:
        if media_type == 'songs':
            track = search_song(track_name)
        else:
            track = search_podcast(track_name)
        if track is not None:
            track_uris.append(track)
    return track_uris

def transfer_to_spotify(playlist_name, track_uris):
    '''
    Creates a Spotify playlist and transfers songs to it.
    :param playlist_name: the name of the Spotify playlist to be created
    :param track_uris: a list of the Spotify URIs of the songs
    '''
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name)
    sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)

def create_playlist_with_mistral_api(user_prompt, media_type): # Modified to take user_prompt
    '''
    Uses Mistral API to generate a playlist and returns track URIs.
    '''
    completion = api.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}, # Use dynamic user_prompt
        ],
        temperature=0.7,
        max_tokens=512,
    )

    response = completion.choices[0].message.content

    # Extract the list part from the response
    list_start = response.find('[')
    list_end = response.rfind(']')
    if list_start != -1 and list_end != -1:
        list_str = response[list_start:list_end + 1]
        # Parse the list string into a Python list
        playlist_data = []
        items = list_str.split('],')
        for item in items:
            item = item.strip().strip('[]')
            if item:
                if media_type == "songs":
                    try:
                        # Split by the first occurrence of "', '"
                        track_name, artist = item.split("', '")
                        track_name = track_name.strip("'")
                        artist = artist.strip("'")
                        playlist_data.append(f"{track_name} by {artist}")
                    except ValueError:
                        print(f"Skipping item with unexpected format: {item}")
                else:            # media_type == "podcasts":
                    playlist_data.append(item)

        # Get Spotify URIs for the tracks
        track_uris = create_track_uris(playlist_data, media_type)
        return track_uris
    else:
        print("Error: Could not find the list in the response.")
        return []


def send_whatsapp_message(to_number, message_body):
    '''
    Sends a WhatsApp message using Twilio.
    '''
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            body=message_body,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{to_number}",
        )
        print(f"WhatsApp message sent successfully! Message SID: {message.sid, to_number}")
        return message.sid
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")
        return None
    finally:
        if "message" in locals():
            del message


# Modify the transfer_to_spotify function to return the playlist link
def transfer_to_spotify(playlist_name, track_uris):
    '''
    Creates a Spotify playlist and transfers songs to it.
    :param playlist_name: the name of the Spotify playlist to be created
    :param track_uris: a list of the Spotify URIs of the songs
    :return: the Spotify playlist link
    '''
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name)
    sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
    return playlist['external_urls']['spotify']

# Main execution
if __name__ == "__main__":
    app.run(port=3030, debug=True)