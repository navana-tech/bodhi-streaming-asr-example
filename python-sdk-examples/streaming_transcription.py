import asyncio
import os
import asyncio
import wave
import logging
from dotenv import load_dotenv
from bodhi import (
    BodhiClient,
    TranscriptionConfig,
    TranscriptionResponse,
    LiveTranscriptionEvents,
    EOF_SIGNAL,
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

    try:

        # Example: Stream audio data in chunks
        # In a real application, this could be from a microphone or other source
        audio_file = os.path.join(os.path.dirname(__file__), "loan.wav")
        if not os.path.exists(audio_file):
            logging.error(f"Audio file not found: {audio_file}")
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        with wave.open(audio_file, "rb") as wf:
            sample_rate = wf.getframerate()
            # Update config with the actual sample rate
            config.sample_rate = sample_rate
            logging.info(f"Using sample rate: {sample_rate}")

            # Start streaming session with config
            await client.start_connection(config=config)

            REALTIME_RESOLUTION = 0.02  # 20ms
            byte_rate = sample_rate * wf.getsampwidth() * wf.getnchannels()
            data = wf.readframes(wf.getnframes())
            audio_cursor = 0

            while len(data):
                i = int(byte_rate * REALTIME_RESOLUTION)
                chunk, data = data[:i], data[i:]
                await client.send_audio_stream(chunk)
                audio_cursor += REALTIME_RESOLUTION
                await asyncio.sleep(REALTIME_RESOLUTION)

            await client.send_audio_stream(EOF_SIGNAL)

        # Finish streaming and get final results
        await client.close_connection()

    except Exception as e:
        print(f"Error during streaming: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        logging.error("Streaming task was cancelled.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
