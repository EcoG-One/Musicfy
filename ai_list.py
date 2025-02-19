import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = "http://127.0.0.1:3000"
SCOPE = 'playlist-modify-public'

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
    "Provide a Python list named 'rock_list' containing 15 popular rock songs suitable for Spotify. "
    "Each entry should be a list with two elements: the track name and the artist. "
    "Format the output as: rock_list = [['track name', 'artist'], ...]"
)

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


def create_track_uris(track_list):
    '''
    Transforms a song list to a URIs list.
    :param track_list: our playlist
    :return: a list of the Spotify URIs of the songs in track_list
    '''
    track_uris = []
    for track_name in track_list:
        song = search_song(track_name)
        if song is not None:
            track_uris.append(song['uri'])
    return track_uris


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
                    playlist_data.append((track_name, artist))
                except ValueError:
                    print(f"Skipping item with unexpected format: {item}")

        # Get Spotify URIs for the tracks
        track_uris = create_track_uris(playlist_data)
        return track_uris
    else:
        print("Error: Could not find the list in the response.")
        return []

# Main execution
if __name__ == "__main__":
    playlist_name = "AI-Generated Rock Playlist"
    track_uris = create_playlist_with_mistral_api()

    if track_uris:
        transfer_to_spotify(playlist_name, track_uris)
        print(playlist_name)
        print(f"Playlist '{playlist_name}' created successfully!")
    else:
        print("Failed to create playlist.")