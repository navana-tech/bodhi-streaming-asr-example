import os
import requests
import uuid
import argparse

# Ensure API_KEY and CUSTOMER_ID are set as global variables
API_KEY = os.getenv("API_KEY")
CUSTOMER_ID = os.getenv("CUSTOMER_ID")


# Function to transcribe audio using Bodhi API
def transcribe_audio(audio_file_path, model):
    """
    Transcribes audio file using Bodhi API.

    Parameters:
    - audio_file_path (str): Path to the audio file to transcribe.
    - model (str): Model name for transcription.

    Returns:
    - str: Response text from the API.
    """

    # Bodhi API endpoint URL
    URL = "https://bodhi.navana.ai/api/transcribe"

    # Generate unique transaction ID
    transaction_id = str(uuid.uuid4())

    # Payload for API request
    payload = {
        "transaction_id": transaction_id,
        "model": model,
    }

    # Files to be sent in the request
    files = {
        "audio_file": (
            os.path.basename(audio_file_path),
            open(audio_file_path, "rb"),
            "audio/wav",
        )
    }

    # Headers for authentication
    headers = {
        "x-customer-id": CUSTOMER_ID,
        "x-api-key": API_KEY,
    }

    try:
        # Send POST request to Bodhi API
        response = requests.post(URL, headers=headers, data=payload, files=files)
        response.raise_for_status()

        # Parse JSON string
        data = response.json()

        print(f"Received data: Call_id={data['call_id']}, Text={data['text']}")

    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio using Bodhi API.")
    parser.add_argument(
        "-f",
        dest="audio_file",
        required=True,
        help="Path to the audio file to transcribe",
    )
    parser.add_argument(
        "-m",
        dest="model",
        default="hi-general-v2-8khz",
        choices=[
            "kn-general-v2-8khz",
            "hi-general-v2-8khz",
            "mr-general-v2-8khz",
            "ta-general-v2-8khz",
            "bn-general-v2-8khz",
            "en-general-v2-8khz",
        ],
        help="Model name for transcription (default: hi-general-v2-8khz)",
    )

    args = parser.parse_args()

    try:
        # Check if API_KEY and CUSTOMER_ID are available
        if not API_KEY or not CUSTOMER_ID:
            raise ValueError(
                "Please set API key and customer ID in environment variables."
            )

        audio_file_path = args.audio_file
        model = args.model

        # Call transcribe_audio function with the audio file
        transcribe_audio(audio_file_path, model)

    except ValueError as e:
        print(e)
