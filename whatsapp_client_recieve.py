from flask import Flask, request
import os
from dotenv import load_dotenv
from twilio.rest import Client
from whatsapp_client_send import send_whatsapp_message
from save_to_file import save_message
import json


# Load environment variables
load_dotenv()

# Twilio Credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
to_whatsapp_number = "whatsapp:" + os.getenv("TO_WHATSAPP_NUMBER")
from_whatsapp_number = "whatsapp:" + os.getenv("TWILIO_WHATSAPP_NUMBER")



spotify_link = "https://open.spotify.com/playlist/37i9dQZEVXcFO6iZOPEu9z"

# Initialize Twilio Client
client = Client(account_sid, auth_token)

# Flask App
app = Flask(__name__)

@app.route("/whatsapp/incoming", methods=['POST'])
def receive_message():
    """
    Handles incoming WhatsApp messages.
    """
    incoming_msg = request.form.get("Body")  # Message text
    sender = request.form.get("From")  # Sender's WhatsApp number (Twilio sandbox number)

    if not incoming_msg:
        print(f" Warning: No message received from {sender}")
        return "⚠️ No message received but connection established ✅", 200  # Avoid 500 error, return 200 OK

    print(f"✅ Received message from {sender}: {incoming_msg}")

    # Respond based on message content
    if "hello" in incoming_msg.lower():
        response_text = spotify_link
        save_message(sender, incoming_msg)
        save_message(sender, response_text)
    elif "weather" in incoming_msg.lower():
        response_text = "Currently, I cannot fetch weather updates, but I'm here to chat!"
    else:
        response_text = "I'm just a bot, but I'm happy to chat with you! 😊"

    # Send response
    send_whatsapp_message(from_whatsapp_number, to_whatsapp_number, response_text)
   # send_whatsapp_message(sender, response_text)

    return "OK", 200

if __name__ == "__main__":
    app.run(port=3030, debug=True)
