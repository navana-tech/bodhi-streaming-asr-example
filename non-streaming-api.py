import os
import requests
import uuid

# Ensure API_KEY and CUSTOMER_ID are set as global variables
API_KEY = os.getenv("API_KEY")
CUSTOMER_ID = os.getenv("CUSTOMER_ID")


# Function to transcribe audio using Bodhi API
def transcribe_audio(audio_file_path, model):
    """
    Transcribes audio file using Bodhi API.

    Parameters:
    - audio_file_path (str): Path to the audio file to transcribe.
    - model (str): Model name for transcription.".

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

    # Send POST request to Bodhi API
    response = requests.post(URL, headers=headers, data=payload, files=files)

    # Parse JSON string
    data = response.json()

    print(
        f"Received data: Call_id={data["call_id"]}, "
        f"Text={data["text"]}"
    )


# Example usage
if __name__ == "__main__":
    try:
        # Check if API_KEY and CUSTOMER_ID are available
        if not API_KEY or not CUSTOMER_ID:
            raise ValueError(
                "Please set API key and customer ID in environment variables."
            )

        audio_file_path = "loan.wav"
        model = "hi-general-v2-8khz"
        # Change the model based on your preference
        # Kannada - kn-general-v2-8khz
        # Hindi - hi-general-v2-8khz
        # Marathi - mr-general-v2-8khz
        # Tamil - ta-general-v2-8khz
        # Bengali - bn-general-v2-8khz
        # English - en-general-v2-8khz

        # Call transcribe_audio function with the audio file
        transcribe_audio(audio_file_path, model)

    except ValueError as e:
        print(e)
