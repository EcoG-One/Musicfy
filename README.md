# Musicfy
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

Save your secrets on your .env file
