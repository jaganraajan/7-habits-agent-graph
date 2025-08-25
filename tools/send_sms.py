import os
from typing import Optional

from twilio.rest import Client
from langchain_core.tools import tool

sid = os.environ["TWILIO_ACCOUNT_SID"]
token = os.environ["TWILIO_AUTH_TOKEN"]
twilio_client = Client(sid, token)

@tool
def send_sms(to: str, body: str) -> str:
    """
    Send an SMS via Twilio.

    Args:
        to: Destination phone number in E.164 format (e.g., "+15551234567").
        body: Text message content.

    Returns:
        The Twilio Message SID upon success.
    """
    msg = twilio_client.messages.create(to=to, from_=os.environ["TWILIO_FROM_NUMBER"], body=body)
    return msg.sid
