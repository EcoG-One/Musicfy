from dotenv import load_dotenv
import os
from twilio.rest import Client

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
to_whatsapp_number = "whatsapp:" + os.getenv("TO_WHATSAPP_NUMBER")
from_whatsapp_number = "whatsapp:" + os.getenv("TWILIO_WHATSAPP_NUMBER")

client = Client(account_sid, auth_token)

def send_whatsapp_message(sender_number, receiver_number, message_body):
    """
    Sends a WhatsApp message using Twilio API.
    :param sender_number: Twilio WhatsApp sender (must be sandbox number)
    :param receiver_number: Recipient's WhatsApp number (e.g., whatsapp:+1234567890)
    :param message_body: Message text
    :return: Message SID if successful, None if an error occurs
    """
    try:
        message = client.messages.create(
            from_=sender_number,
            to=receiver_number,
            body=message_body
        )
        print(f"Message sent successfully! SID: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Failed to send message: {e}")
        return None


message_text = ("Hello from Musicfy. Tell me what you want to listen. "
                "Please respond with max four words, describing the music style, "
                "the mood and optionally the era or the country. \n"
                "For Example: Pop, happy, Italian \n"
                "or 80s, dance \n"
                "or Classic Rock, chill.")
send_whatsapp_message(from_whatsapp_number, to_whatsapp_number, message_text)