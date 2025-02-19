import json
import os

CONVERSATION_FILE = "conversations.json"


def save_message(phone_number, text):
    """
    Saves a WhatsApp message under the corresponding phone number.

    :param phone_number: The phone number of the sender/receiver.
    :param text: The message text.
    """
    # Load existing messages if the file exists
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, "r") as file:
            conversations = json.load(file)
    else:
        conversations = {}

    # Append the new message under the correct phone number
    if phone_number not in conversations:
        conversations[phone_number] = []  # Create list if not existing

    conversations[phone_number].append(text)

    # Save updated messages back to the file
    with open(CONVERSATION_FILE, "w") as file:
        json.dump(conversations, file, indent=4)

    print(f"Message saved for {phone_number}: {text}")

