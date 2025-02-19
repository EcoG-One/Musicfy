from twilio.rest import Client
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from flask import Flask, request
#import json
#from save_to_file import save_message

CONVERSATION_FILE = os.path.join(os.path.dirname(__file__), "conversations.json")

# Spotify credentials
CLIENT_ID = "aa83fbce48084687a171b50465900891"
CLIENT_SECRET = "55ef74a61e384628a939aceb8584eec5"
REDIRECT_URI = "http://127.0.0.1:3000"
SCOPE = 'playlist-modify-public'

# Twilio credentials
TWILIO_ACCOUNT_SID = "ACa276eee82417fb4243218ae63eb9d522"
TWILIO_AUTH_TOKEN = "949e34962a3e80de75b44a56406af6d4"
TWILIO_WHATSAPP_NUMBER = "+14155238886"
#YOUR_WHATSAPP_NUMBER = sender

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
    print("Webhook received!")  # Add this
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")

    print(f"Incoming message: {incoming_msg}")

    if not incoming_msg:
        print(f"Warning: No message received from {sender}")
        return "⚠️ No message received but connection established ✅", 200

    print(f"✅ Received message from {sender}: {incoming_msg}")

    # 1. Process the incoming message (prompts)
    prompts = process_incoming_message(incoming_msg)
    print(f"Prompts: {prompts}")

    if prompts:
        user_prompt = create_user_prompt(prompts)
        print(f"User prompt: {user_prompt}")
        track_uris = create_playlist_with_mistral_api(user_prompt)  # Pass user_prompt

        if track_uris:
            playlist_name = "AI-Generated Playlist"
            playlist_link = transfer_to_spotify(playlist_name, track_uris)
            response_text = f"Here's your playlist: {playlist_link}"
            print(sender, response_text)
            send_whatsapp_message(sender, response_text)  # Corrected line
        else:
            response_text = "Sorry, I couldn't create the playlist."
    else:
        response_text = "Please provide valid prompts."
        print(sender, response_text)
    send_whatsapp_message(sender, response_text)  # Corrected line
    return "OK", 200


def process_incoming_message(message):
    """
    Processes the incoming message and extracts the prompts.
    """
    message = message.lower()
    prompts = message.split()  # Split the message into individual words

    # Basic validation (you can make this more robust)
    if len(prompts) > 0: # Check if there are any prompts
        return prompts
    else:
        return None  # Return None if no prompts are found


def create_user_prompt(prompts):
    """
    Creates the user prompt for the Mistral API using the extracted prompts.
    """
    prompt_string = " ".join(prompts)  # Join prompts with spaces
    user_prompt = (
        f"Provide a Python list named 'AI-playlist' containing 15 random only {prompt_string} songs suitable for Spotify. "
        "Each entry should be a list with two elements: the track name and the artist. "
        "Format the output as: playlist = [['track name', 'artist'], ...]"
    )
    return user_prompt


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

def create_playlist_with_mistral_api(user_prompt): # Modified to take user_prompt
    '''
    Uses Mistral API to generate a playlist and returns track URIs.
    Now uses the provided user_prompt.
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
            to=to_number
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
    #playlist_name = "AI-Generated Rock Playlist"
    #track_uris = create_playlist_with_mistral_api()

    #if track_uris:
       # playlist_link = transfer_to_spotify(playlist_name, track_uris)
       # print(f"Playlist '{playlist_name}' created successfully! Link: {playlist_link}")

        # Send the
    # playlist link via WhatsApp
        #whatsapp_message = f"Here's your new Spotify playlist: {playlist_link}"
        #send_whatsapp_message(whatsapp_message)
    #else:
       # print("Failed to create playlist.")