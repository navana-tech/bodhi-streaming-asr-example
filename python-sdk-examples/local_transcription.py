import asyncio
import os
import logging
from dotenv import load_dotenv
from bodhi import (
    BodhiClient,
    TranscriptionConfig,
    TranscriptionResponse,
)
from bodhi.events import LiveTranscriptionEvents

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

    # Example configuration with hotwords
    config = TranscriptionConfig(
        model="hi-banking-v2-8khz",
    )

    # Example with local file
    # generate absolute path of audio file
    audio_file = os.path.join(os.path.dirname(__file__), "loan.wav")
    if not os.path.exists(audio_file):
        logging.error(f"Audio file not found: {audio_file}")
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    try:
        # For local file transcription, the events will be emitted during the transcribe_local_file call
        result = await client.transcribe_local_file(audio_file, config=config)
        logging.info("Final result: %s", result)
        logging.info("Local file transcription finished.")
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
