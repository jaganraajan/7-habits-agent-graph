import os
from typing import Optional

from twilio.rest import Client
from langchain_core.tools import tool

sid = os.environ["TWILIO_ACCOUNT_SID"]
token = os.environ["TWILIO_AUTH_TOKEN"]
twilio_client = Client(sid, token)

@tool
def send_sms(body: str) -> str:
    """
    Send an SMS via Twilio to the user currently using the system.

    Args:
        body: Text message content.

    Returns:
        The Twilio Message SID upon success.
    """
    send_to = os.getenv("TWILIO_TO_NUMBER")
    msg = twilio_client.messages.create(to=send_to, from_=os.environ["TWILIO_FROM_NUMBER"], body=body)
    return msg.sid
