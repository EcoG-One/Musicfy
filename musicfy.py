from twilio.rest import Client
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
# Set up credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
# Spotify credentials
# CLIENT_ID = "aa83fbce48084687a171b50465900891"
# CLIENT_SECRET = "55ef74a61e384628a939aceb8584eec5"
REDIRECT_URI = "http://127.0.0.1:3000"
SCOPE = 'playlist-modify-public'

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = "+14155238886"
YOUR_WHATSAPP_NUMBER = "+4915901299525"

# Authenticate Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))

# OpenAI API setup
base_url = "https://api.aimlapi.com/v1"
api_key = "fdc7e528621d4914bc32586ced14e752"
api = OpenAI(api_key=api_key, base_url=base_url)

# System and user prompts for OpenAI
system_prompt = "You are an AI assistant who knows everything."
user_prompt = (
    "Provide a Python list named 'karaoke_list' containing 15 EDM songs from the 2020s suitable for Spotify. "
    "Each entry should be a list with two elements: the track name and the artist. "
    "Format the output as: rock_list = [['track name', 'artist'], ...]"
)

def search_track(track_name):
    '''
    Searches for the Spotify URI of a given track name.
    :param track_name: a song title
    :return: the Spotify URI of the track_name
    '''
    results = sp.search(q=track_name, type='track', limit=1)
    if results['tracks']['items']:
        return results['tracks']['items'][0]['uri']
    else:
        return None

def create_track_uris(track_list):
    '''
    Transforms a song list to a URIs list.
    :param track_list: our playlist
    :return: a list of the Spotify URIs of the songs in track_list
    '''
    track_uris = []
    for track_name in track_list:
        track = search_track(track_name)
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

def create_playlist_with_mistral_api():
    '''
    Uses Mistral API to generate a playlist and returns track URIs.
    :return: a list of Spotify track URIs
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
                try:
                    # Split by the first occurrence of "', '"
                    track_name, artist = item.split("', '")
                    track_name = track_name.strip("'")
                    artist = artist.strip("'")
                    playlist_data.append(f"{track_name} by {artist}")
                except ValueError:
                    print(f"Skipping item with unexpected format: {item}")

        # Get Spotify URIs for the tracks
        track_uris = create_track_uris(playlist_data)
        return track_uris
    else:
        print("Error: Could not find the list in the response.")
        return []


def send_whatsapp_message(message):
    '''
    Sends a WhatsApp message using Twilio.
    :param message: The message to send
    '''
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{YOUR_WHATSAPP_NUMBER}"
        )
        print(f"WhatsApp message sent successfully! Message SID: {message.sid}")
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")

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
    playlist_name = "AI-Generated Rock Playlist"
    track_uris = create_playlist_with_mistral_api()

    if track_uris:
        playlist_link = transfer_to_spotify(playlist_name, track_uris)
        print(f"Playlist '{playlist_name}' created successfully! Link: {playlist_link}")

        # Send the playlist link via WhatsApp
        whatsapp_message = f"Here's your new Spotify playlist: {playlist_link}"
        send_whatsapp_message(whatsapp_message)
    else:
        print("Failed to create playlist.")