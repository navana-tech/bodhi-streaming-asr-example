import asyncio
import os
import logging
from dotenv import load_dotenv
from bodhi import (
    BodhiClient,
    TranscriptionConfig,
    TranscriptionResponse,
    LiveTranscriptionEvents,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load credentials from .env file
load_dotenv()
API_KEY = os.getenv("BODHI_API_KEY")
CUSTOMER_ID = os.getenv("BODHI_CUSTOMER_ID")


async def on_transcript(response: TranscriptionResponse):
    logging.info(f"Transcript: {response.text}")


async def on_utterance_end(response: TranscriptionResponse):
    logging.info(f"UtteranceEnd: {response}")


async def on_speech_started(response: TranscriptionResponse):
    logging.info(f"SpeechStarted: {response}")


async def on_error(e: Exception):
    logging.error(f"Error: {str(e)}")


async def on_close():
    logging.info("WebSocket connection closed.")


async def main():
    if not API_KEY or not CUSTOMER_ID:
        logging.error(
            "Please set BODHI_API_KEY and BODHI_CUSTOMER_ID environment variables"
        )
        raise ValueError(
            "Please set BODHI_API_KEY and BODHI_CUSTOMER_ID environment variables"
        )

    client = BodhiClient(api_key=API_KEY, customer_id=CUSTOMER_ID)

    # Register event listeners
    client.on(LiveTranscriptionEvents.Transcript, on_transcript)
    client.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
    client.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
    client.on(LiveTranscriptionEvents.Error, on_error)
    client.on(LiveTranscriptionEvents.Close, on_close)

    # Example configuration
    config = TranscriptionConfig(
        model="hi-banking-v2-8khz",
    )

    # Example with remote URL
    audio_url = "https://bodhi.navana.ai/audios/loan.wav"  # Replace with your audio URL

    try:
        # For remote URL transcription, events will be emitted during the transcribe_remote_url call
        result = await client.transcribe_remote_url(audio_url, config=config)
        logging.info("Remote URL transcription finished.")
        logging.info("Final result: %s", result)
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
