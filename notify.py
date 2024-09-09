import os, requests

from dotenv import load_dotenv

load_dotenv()
server = os.getenv("SERVER", "https://ntfy.sh")


def send_ntfy(topic, message):
    """
    Send a notification with ntfy.
    """
    url = f'{server}/{topic}'
    response = requests.post(url, data=message)
    
    if response.status_code == 200:
        print("Notification sent successfully!")
    else:
        print(f"Failed to send notification: {response.status_code} - {response.text}")
