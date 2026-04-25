import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


def send_whatsapp_message(to: str, body: str):
    """Calls the WhatsApp cloud API to send a text message."""
    url = f"https://graph.facebook.com/v15.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body}
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("Error sending message:", response.text)
        response.raise_for_status()


def download_whatsapp_image(media_id: str) -> tuple[bytes, str]:
    """Downloads an image from WhatsApp's media API. Returns (image_bytes, mime_type)."""
    headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
    meta_url = f"https://graph.facebook.com/v15.0/{media_id}"
    meta_response = requests.get(meta_url, headers=headers)
    meta_response.raise_for_status()
    media_data = meta_response.json()
    download_url = media_data["url"]
    mime_type = media_data.get("mime_type", "image/jpeg")
    image_response = requests.get(download_url, headers=headers)
    image_response.raise_for_status()
    return image_response.content, mime_type


def download_whatsapp_audio(media_id: str) -> bytes:
    """Downloads an audio message from WhatsApp's media API. Returns raw audio bytes."""
    headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
    meta_url = f"https://graph.facebook.com/v15.0/{media_id}"
    meta_response = requests.get(meta_url, headers=headers)
    meta_response.raise_for_status()
    download_url = meta_response.json()["url"]
    audio_response = requests.get(download_url, headers=headers)
    audio_response.raise_for_status()
    return audio_response.content
