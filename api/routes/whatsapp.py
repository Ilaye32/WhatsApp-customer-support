from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.background import BackgroundTasks
from api.services.whatsapp_messager import (
    send_whatsapp_message,
    download_whatsapp_image,
    download_whatsapp_audio,
)
from api.services.audio_processor import process_audio
import os
from dotenv import load_dotenv
from main import run_agent

load_dotenv()

router = APIRouter()
MAX_MESSAGE_LENGTH = 2000


@router.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    background_tasks.add_task(process_whatsapp_message, data)
    return {"status": "received"}


async def process_whatsapp_message(data: dict):
    entry = data.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    print(f"Value: {value}")

    if "messages" not in value:
        return

    messages = value["messages"]
    if not messages:
        return

    message = messages[0]
    from_number = message["from"]
    message_type = message.get("type", "text")

    image_bytes = None
    mime_type = None
    user_text = ""

    if message_type == "text":
        user_text = message["text"]["body"]
        print(f"User text: {user_text}")
        if len(user_text) > MAX_MESSAGE_LENGTH:
            send_whatsapp_message(
                to=from_number,
                body="Your message is too long. Please send a shorter message.",
            )
            return

    elif message_type == "image":
        media_id = message["image"]["id"]
        caption = message["image"].get("caption", "")
        user_text = caption if caption else "What is in this image?"
        print(f"Received image, caption: {user_text}")
        try:
            image_bytes, mime_type = download_whatsapp_image(media_id)
            print(f"Downloaded image: {len(image_bytes)} bytes, type: {mime_type}")
        except Exception as e:
            print(f"Failed to download image: {e}")
            send_whatsapp_message(
                to=from_number,
                body="Sorry, I could not download your image. Please try again.",
            )
            return

    elif message_type == "audio":
        media_id = message["audio"]["id"]
        print(f"Received voice message, media_id: {media_id}")
        try:
            audio_bytes = download_whatsapp_audio(media_id)
            print(f"Downloaded audio: {len(audio_bytes)} bytes")
            # Transcribe audio to text — agent treats it like a normal text message
            user_text = await process_audio(audio_bytes)
            print(f"Transcribed audio: {user_text}")
        except ValueError as e:
            # Validation errors (too short, too long, no speech)
            send_whatsapp_message(to=from_number, body=str(e))
            return
        except Exception as e:
            print(f"Audio processing failed: {e}")
            send_whatsapp_message(
                to=from_number,
                body="Sorry, I could not process your voice message. Please try again or send a text.",
            )
            return

    else:
        send_whatsapp_message(
            to=from_number,
            body="Sorry, I can only process text, images, and voice messages at the moment.",
        )
        return

    response = await run_agent(
        user_message=user_text,
        from_number=from_number,
        image_bytes=image_bytes,
        mime_type=mime_type,
    )
    send_whatsapp_message(to=from_number, body=response)


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")
