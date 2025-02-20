# Musicfy 
<img src=https://github.com/user-attachments/assets/9d3d438b-72d4-4abd-8110-b42a1cea5dd8 width="200"/>

An App that creates Spotify Playlists according to Genre and Mood and sends them to What's Up.

In order for the script to work you need to get a Client ID and a 
Client Secret from Spotify Developer Dashboard:

Go to the Spotify Developer Dashboard: https://developer.spotify.com/

Log in with your Spotify account.

Create a new application. Just fill in the form.

Under the "Redirect URIs" field, add your redirect URI. 
This can be a local URI like http://127.0.0.1:3000 for development purposes.

Under the API section, choose the Web API.

After creating the Spotify Developer Application you can get your 
Client ID and Client Secret from the Dashboard's Basic Information
Don't forget to log in to Spotify, in order for your token to be created.

You also need an account to https://www.twilio.com/ and Mistral AI

Save your secrets on your .env file

In order for your Flask to go public, you can use a forwarder like ngrok and paste your virtual URL to 
Twillo's sandbox settings.

The user must scan the QRcode on your Willo's sandbox page and then send the word 
songs or
podcasts or
help
and the music/podcasts he wants to listen to, for example: songs indie 90s upbeat, or poscasts crime etc.
and after a few seconds he gets the AI created Spotify playlist on his What's Up
