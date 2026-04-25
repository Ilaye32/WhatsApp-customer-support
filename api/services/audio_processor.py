import logging
from typing import Tuple
from io import BytesIO
import wave
import asyncio
import groq
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s : %(message)s"
)

logger = logging.getLogger("GroqSTTBot")
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))  # Fixed


def convert_raw_pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000,
                            channels: int = 1, sample_width: int = 2) -> bytes:
    logger.info(f"Converting {len(pcm_data)} bytes of raw PCM to WAV "
                f"({sample_rate}Hz, {channels}ch, {sample_width*8}bit)")
    wav_buffer = BytesIO()
    try:
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        wav_bytes = wav_buffer.getvalue()
        logger.info(f"WAV conversion successful: {len(wav_bytes)} bytes")
        return wav_bytes
    except Exception as e:
        logger.error(f"WAV conversion failed: {e}", exc_info=True)
        raise


def detect_audio_format(audio_data: bytes) -> Tuple[str, str, bool]:
    if len(audio_data) < 4:
        logger.warning("Audio data too short to detect format")
        return "audio/wav", "audio.wav", True

    magic_bytes = audio_data[:4]
    hex_magic = magic_bytes.hex()

    if magic_bytes == b'\x00\x00\x00\x00' or hex_magic == "00000000":
        return "audio/wav", "audio.wav", True
    if magic_bytes == b'\x1a\x45\xdf\xa3':
        return "audio/webm", "audio.webm", False
    elif magic_bytes[:4] == b'RIFF':
        return "audio/wav", "audio.wav", False
    elif len(audio_data) > 8 and audio_data[4:8] == b'ftyp':
        return "audio/mp4", "audio.mp4", False
    elif magic_bytes[:4] == b'OggS':
        return "audio/ogg", "audio.ogg", False
    elif magic_bytes[:3] == b'ID3' or magic_bytes[:2] in [b'\xff\xfb', b'\xff\xf3']:
        return "audio/mp3", "audio.mp3", False
    else:
        logger.warning(f"Unknown audio format (magic bytes: {hex_magic}), treating as raw PCM")
        return "audio/wav", "audio.wav", True


async def process_audio(audio_data: bytes) -> str:
    """
    Validates, converts if needed, and transcribes audio.
    Returns the transcription text.
    """
    import io

    size_mb = len(audio_data) / (1024 * 1024)
    logger.info(f"Processing audio: {size_mb:.2f} MB")

    if size_mb > 25:
        raise ValueError("Audio is too long, please use text.")
    if size_mb < 0.0001:
        raise ValueError("Audio too short. Please record a longer message.")

    mime_type, filename, is_raw_pcm = detect_audio_format(audio_data)
    logger.info(f"Detected format: {mime_type}, is_raw_pcm={is_raw_pcm}")

    if is_raw_pcm:
        logger.info("Converting raw PCM to WAV")
        converted_audio = convert_raw_pcm_to_wav(audio_data)
        filename = "audio.wav"
    else:
        converted_audio = audio_data

    audio_file = io.BytesIO(converted_audio)
    logger.info("Starting transcription")

    transcription = await asyncio.to_thread(
        groq_client.audio.transcriptions.create,
        file=(filename, audio_file),
        model="whisper-large-v3",
        response_format="text",
        language="en"
    )

    text = transcription if isinstance(transcription, str) else transcription.text  # Fixed

    if not text or not text.strip():
        raise ValueError("No speech detected in audio.")

    logger.info(f"Transcription successful: {text[:50]}")
    return text.strip()
