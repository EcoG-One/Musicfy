from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp/incoming", methods=["POST"])
def receive_whatsapp_message():
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "").strip()

    print(f"Received message from {from_number}: {incoming_msg}")

    # Respond to the message (optional)
    response = MessagingResponse()
    response.message("Message received")

    return str(response)

@app.route("/whatsapp/messageStatus", methods=["POST"])
def message_status_callback():
    message_sid = request.values.get("MessageSid", "").strip()
    message_status = request.values.get("MessageStatus", "").strip()

    print(f"Message SID: {message_sid} has status: {message_status}")

    return "Status received", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3030)