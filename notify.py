"""
Description: Send notifications with ntfy.
Date Created: 2024-09-01
Date Modified: 2024-09-12
Author: SPolton
Modified By: SPolton
Version: 1.1.0
"""

import os, requests

from dotenv import load_dotenv
from logging import getLogger

load_dotenv()
ntfy_server = os.getenv("NTFY_SERVER", "https://ntfy.sh")

logger = getLogger(__name__)

def send_ntfy(topic, message, title=None, priority=None, tags=None, link=None, img=None):
    """
    Send a notification with ntfy. https://docs.ntfy.sh/publish/

    Details:
    - topic: Required - Topics are created on the fly by subscribing or publishing to them.
                        Since there is no sign-up, the topic is essentially a password,
                        so pick something that is not easy to guess
    - message: Required - The main message body of the notification text.
    - title: Default is typically set to the topic short URL (e.g. ntfy.sh/mytopic)
    - priority: Defines how urgent a message is when the device is notified.
                Range from 5 (High) to 1 (Low) priority, default is 3.
    - tags: Prepended title or message with emojis. See https://docs.ntfy.sh/publish/#tags-emojis
    - link: The URL to open when the notification is clicked.
    - img: Attach an image file or image link (Browers and Android only).
    """
    if topic and message:
        ntfy_url = f"{ntfy_server}/{topic}"
        message_encoded = str(message).encode(encoding="utf-8")
        
        headers = {}
        if title:
            headers["Title"] = str(title)
        if priority:
            headers["Priority"] = str(priority)
        if tags:
            if isinstance(tags, str):
                tags = tags.replace(" ", "")
            elif isinstance(tags, list):
                tags = ",".join(tags)
            headers["Tags"] = str(tags)
        if link:
            headers["Click"] = str(link)
        if img:
            headers["Attach"] = str(img)
        
        response = requests.post(ntfy_url, data=message_encoded, headers=headers)
        
        if response.status_code == 200:
            logger.info("ntfy notification sent successfully!")
        else:
            logger.error(f"Failed to send ntfy notification: {response.status_code} - {response.text}")
    else:
        logger.warning("ntfy notification not sent. Topic and/or Message is empty.")