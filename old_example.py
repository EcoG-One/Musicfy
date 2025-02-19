from transfer_playlist import *
'''
This is just an example of how to use the functions os Transfer_playlist
'''
# Search a song
track_name = 'Shape of You'
track_uri = search_track(track_name)
if track_uri:
    print(f'Track URI for "{track_name}": {track_uri}')
else:
    print(f'Track "{track_name}" not found.')

# List of song URIs to add to the playlist
track_uris = [
    'spotify:track:4cOdK2wGLETKBW3PvgPWqT',
    'spotify:track:1301WleyT98MSxVHPZCA6M',
    'spotify:track:7qiZfU4dY1lWllzX7mPBI3'
]
# Transfer the playlist
transfer_to_spotify('Test Playlist', track_uris)