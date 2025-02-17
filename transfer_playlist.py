import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

'''
In order for the script to work you need to get a Client ID and a 
Client Secret from Spotify Developer Dashboard:
Go to the Spotify Developer Dashboard: https://developer.spotify.com/
Log in with your Spotify account.
Create a new application. Just fill in the form.
Under the "Redirect URIs" field, add your redirect URI. 
This can be a local URI like http://localhost:8888/callback 
or http://127.0.0.1:3000 for development purposes.
Under the API section, choose the Web API.
After creating the Spotify Developer Application you can get your 
Client ID and Client Secret from the Dashboard's Basic Information
Save them on your .env file
'''
# load variables from .env file
load_dotenv()
# Set up credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:3000'
# Alternative Redirect_URI = 'http://localhost:8888/callback'
SCOPE = 'playlist-modify-public'

# Authenticate and get access token
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))


def search_track(track_name):
    '''
    searches for the Spotify URI of a given track name
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
    transforms a song list to a URIs list
    :param track_list: our playlist
    :return: a list of the Spotify URIs of the songs in track_list
    '''
    track_uris = []
    for track_name in track_list:
        track = search_track(track_name)
        if track is not None:
            track_uris.append(track)


def transfer_to_spotify(playlist_name, track_uris):
    '''
    Creates a Spotify playlist and transfers songs to it
    :param playlist_name: the name of the Spotify playlist to be created
    :param track_uris: a list of the Spotify URIs of the songs
    '''
    # Create a new playlist
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name)

    # Add tracks to the playlist
    sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)

