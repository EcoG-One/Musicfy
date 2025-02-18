import json
response = ''' I'm an AI and I don't have the ability to create Spotify playlists directly, but I can certainly suggest a list of slow rock songs for you to create your own chilling playlist on Spotify. Here are my recommendations:

1. "Wonderwall" - Oasis
2. "Blackbird" - The Beatles
3. "The Sound of Silence" - Simon & Garfunkel
4. "Stairway to Heaven" - Led Zeppelin
5. "More Than Words" - Extreme
6. "Tears in Heaven" - Eric Clapton
7. "Wish You Were Here" - Pink Floyd
8. "Angie" - The Rolling Stones
9. "I Will Always Love You" - Whitney Houston (Slow Rock Version)
10. "Bohemian Rhapsody" - Queen (Acoustic Version)
11. "Hallelujah" - Leonard Cohen
12. "Sweet Child O' Mine" - Guns N' Roses (Acoustic Version)
13. "Dust in the Wind" - Kansas
14. "November Rain'''

clean_response = response.split('\n\n')[1]
very_clean_response = clean_response.replace("'", '"')
playlist = json.loads(very_clean_response)
titles = []
for song in playlist:
    titles.append(song['track_name'])
    print(song['track_name'])
