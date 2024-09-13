import os, requests

from dotenv import load_dotenv
from logging import getLogger

load_dotenv()
ntfy_server = os.getenv("NTFY_SERVER", "https://ntfy.sh")

logger = getLogger(__name__)

def send_ntfy(topic, message, title=None, priority=None, link=None, img=None):
    """Send a notification with ntfy."""
    if topic and message:
        ntfy_url = f'{ntfy_server}/{topic}'
        
        headers = {}
        if title:
            headers["Title"] = title
        if priority:
            headers["Priority"] = str(priority)
        if link:
            headers["Click"] = link
        if img:
            headers["Attach"] = img
        
        response = requests.post(ntfy_url, data=message, headers=headers)
        
        if response.status_code == 200:
            logger.info("ntfy notification sent successfully!")
        else:
            logger.error(f"Failed to send ntfy notification: {response.status_code} - {response.text}")
    else:
        logger.warning("ntfy notification not sent. Topic and/or Message is empty.")