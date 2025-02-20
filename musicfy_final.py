from twilio.rest import Client
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from flask import Flask, request
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv

load_dotenv()
CONVERSATION_FILE = os.path.join(os.path.dirname(__file__), "conversations.json")
# Set up credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = "http://127.0.0.1:3000"
SCOPE = 'playlist-modify-public'

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = "+14155238886"


# Authenticate Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))

app = Flask(__name__)


# OpenAI API setup
base_url = "https://api.aimlapi.com/v1"
api_key = "fdc7e528621d4914bc32586ced14e752"
api = OpenAI(api_key=api_key, base_url=base_url)

#KEEP FOR TESTING! The prompt needs to be specific
# System and user prompts for OpenAI
system_prompt = "You are an AI assistant who knows everything."
#user_prompt = (
   # "Provide a Python list named 'playlist' containing 15 only {incoming_msg} songs suitable for Spotify. "
   # "Each entry should be a list with two elements: the track name and the artist. "
   # "Format the output as: playlist = [['track name', 'artist'], ...]"
#)


@app.route("/whatsapp/incoming", methods=['POST'])
def receive_message():
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")
    print(f"Incoming message: {incoming_msg}")

    if not incoming_msg:
        print(f"Warning: No message received from {sender}")
        return "⚠️ No message received but connection established ✅", 200

    print(f"✅ Received message from {sender}: {incoming_msg}")

    playlist_type, prompts = process_incoming_message(incoming_msg)
    print(f"Playlist type: {playlist_type}, Prompts: {prompts}")

    if playlist_type:
        user_prompt = create_user_prompt(playlist_type, prompts)
        print(f"User prompt: {user_prompt}")
        track_uris = create_playlist_with_mistral_api(user_prompt, playlist_type == "podcast")

        if track_uris:
            playlist_name = f"AI-Generated {playlist_type.capitalize()} Playlist"
            playlist_link = transfer_to_spotify(playlist_name, track_uris)
            response_text = f"Here's your {playlist_type} playlist: {playlist_link}"
            print(sender, response_text)
            new_number = sender[9:]
            send_whatsapp_message(new_number, response_text)
        else:
            response_text = "Sorry, I couldn't create the playlist."
    else:
        response_text = "Please specify if you want a song or podcast playlist."

    return "OK", 200


def process_incoming_message(message):
    """
    Processes the incoming message and extracts the type of playlist and prompts.
    """
    message = message.lower()
    if "song" in message or "songs" in message or "music" in message:
        playlist_type = "song"
    elif "podcast" in message or "podcasts" in message:
        playlist_type = "podcast"
    else:
        return None, None  # Return both None if type can't be determined

    prompts = message.split()  # Split the message into individual words for further processing
    return playlist_type, prompts

def create_user_prompt(playlist_type, prompts):
    """
    Creates the user prompt for the Mistral API using the extracted prompts.
    """
    prompt_string = " ".join(prompts)  # Join prompts with spaces
    if playlist_type == "song":
        user_prompt = (
            f"Provide a Python list named 'AI-playlist' containing 15 random only {prompt_string} songs suitable for Spotify. "
            "Each entry should be a list with two elements: the track name and the artist. "
            "Format the output as: playlist = [['track name', 'artist'], ...]"
        )
    elif playlist_type == "podcast":
        user_prompt = (
            f"Provide a Python list named 'AI-playlist' containing 15 podcasts episodes of {prompt_string} podcasts suitable for Spotify. "
            "Each entry should be a list with two elements: the podcast name and the host or publisher. "
            "If the host is not known or there are multiple hosts, use the publisher instead. "
            "Format the output as: playlist = [['podcast name', 'host or publisher'], ...]"
        )
    return user_prompt


def search_podcast(name):
    '''
    Search for episodes of a podcast by name
    :param name: the name of the podcast to search for
    :return: a list of episode URIs or None if not found
    '''
    query = f'show:{name}'
    results = sp.search(q=query, type='show', limit=1)
    if results['shows']['items']:
        show_id = results['shows']['items'][0]['id']
        episodes = sp.show_episodes(show_id, limit=5)  # Get 5 episodes
        return [episode['uri'] for episode in episodes['items'] if 'uri' in episode]
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


def transfer_to_spotify(playlist_name, track_uris):
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name)
    print(f"Created playlist with ID: {playlist['id']}")  # Log the ID
    print(f"Attempting to add these URIs: {track_uris}")
    try:
        sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
        return playlist['external_urls']['spotify']
    except SpotifyException as e:
        print(f"Spotify Error adding items: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def create_playlist_with_mistral_api(user_prompt, is_podcast=False):
    '''
    Uses Mistral API to generate a playlist and returns track URIs.
    :param user_prompt: The prompt for the Mistral API
    :param is_podcast: Boolean indicating if the playlist should be for podcasts
    '''
    completion = api.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=512,
    )

    response = completion.choices[0].message.content

    list_start = response.find('[')
    list_end = response.rfind(']')
    if list_start != -1 and list_end != -1:
        list_str = response[list_start:list_end + 1]

        playlist_data = []
        items = list_str.split('],')
        for item in items:
            item = item.strip().strip('[]')
            if item:
                try:
                    # Split by the first occurrence of "', '"
                    name, creator = item.split("', '")
                    name = name.strip("'")
                    creator = creator.strip("'")
                    playlist_data.append((name, creator))
                except ValueError:
                    print(f"Skipping item with unexpected format: {item}")

        # Use different search functions based on the playlist type
        track_uris = []
        if is_podcast:
            for name, host in playlist_data:
                episodes = search_podcast(f"{name} {host}")
                if episodes:
                    track_uris.extend(episodes)
                else:
                    print(f"Could not find episodes for podcast: {name} by {host}")
        else:
            for track_name, artist in playlist_data:
                song = search_song((track_name, artist))
                if song:
                    track_uris.append(song['uri'])

        return track_uris
    else:
        print("Error: Could not find the list in the response.")
        return []


def send_whatsapp_message(to_number, message_body):
    '''
    Sends a WhatsApp message using Twilio.
    :param message: The message to send
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



def transfer_to_spotify(playlist_name, track_uris):
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name)
    print(f"Created playlist with ID: {playlist['id']}")
    print(f"Attempting to add these URIs: {track_uris}")

    valid_uris = [uri for uri in track_uris if isinstance(uri, str) and uri.startswith('spotify:')]

    if not valid_uris:
        print("No valid URIs found to add to the playlist.")
        return None

    try:
        sp.playlist_add_items(playlist_id=playlist['id'], items=valid_uris)
        return playlist['external_urls']['spotify']
    except SpotifyException as e:
        if e.http_status == 401:  # Unauthorized - token issue
            print("Authentication issue detected. Attempting token refresh.")
            sp.auth_manager.refresh_access_token()
            return transfer_to_spotify(playlist_name, track_uris)  # Retry after refresh
        print(f"Spotify Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Main execution
if __name__ == "__main__":
    app.run(port=3030, debug=True)