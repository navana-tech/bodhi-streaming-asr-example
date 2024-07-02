import websockets
import argparse
import asyncio
import wave
import sys
import json
import os
import uuid
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


# Helper function for argument parsing
def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text


# Asynchronous function to receive transcription from the server
async def receive_transcription(ws):
    complete_sentences = []
    while True:
        response = await ws.recv()
        try:
            response_data = json.loads(response)

            # Complete response from the ASR server contains json data
            # print(response_data)
            # sample response: {'call_id': 'ffae3d29833c', 'segment_id': '966339932cc3', 'eos': False, 'type': 'partial', 'text': 'मुझे'}

            # Unique identifier associated with every streaming connection
            call_id = response_data["call_id"]

            # Unique identifier associated with every speech segment during the entire active socket connection
            # Usually a speech segment is 4-10 seconds long
            segment_id = response_data["segment_id"]

            # Partial transcript corresponding to every streaming audio chunk
            # Complete transcript generated for each speech segment when speech segment end is reached
            transcript_type = response_data["type"]

            # Transcript text
            transcript_text = response_data["text"]

            # If 'eos' is True, marks the end of the streaming connection
            end_of_stream = response_data["eos"]

            if transcript_type == "complete" and transcript_text != "":
                complete_sentences.append(response_data["text"])

            print(
                f"Received data: Call_id={call_id}, "
                f"Segment_id={segment_id}, "
                f"EOS={end_of_stream}, "
                f"Type={transcript_type}, "
                f"Text={transcript_text}"
            )

            if response_data["eos"]:
                print("Complete transcript: ", ", ".join(complete_sentences))
                break
        except json.JSONDecodeError:
            print(f"Received a non-JSON response: {response}")


# function to send audio data to the server
async def send_audio(ws, wf, buffer_size, interval_seconds):
    while True:
        data = wf.readframes(buffer_size)
        if len(data) == 0:
            break
        await ws.send(data)
        await asyncio.sleep(interval_seconds)
    await ws.send('{"eof": 1}')


# function to run the test
async def run_test(api_key, customer_id):
    request_headers = {
        "x-api-key": api_key,
        "x-customer-id": customer_id,
    }
    chunk_duration_ms = 100

    async with websockets.connect(
        args.uri, extra_headers=request_headers, ssl=ssl_context
    ) as ws:

        wf = wave.open(args.file, "rb")
        (channels, sample_width, sample_rate, num_samples, _, _) = wf.getparams()
        print(
            f"Channels = {channels}, Sample Rate = {sample_rate} Hz, Sample width = {sample_width} bytes",
            file=sys.stderr,
        )

        # Sending initial configuration to the server
        await ws.send(
            json.dumps(
                {
                    "config": {
                        "sample_rate": sample_rate,
                        "transaction_id": str(uuid.uuid4()),
                        "model": "hi-general-v2-8khz",
                        # Change the model based on your preference
                        # Kannada - kn-general-v2-8khz
                        # Hindi - hi-general-v2-8khz
                        # Marathi - mr-general-v2-8khz
                        # Tamil - ta-general-v2-8khz
                        # Bengali - bn-general-v2-8khz
                        # English - en-general-v2-8khz
                    }
                }
            )
        )

        buffer_size = int(sample_rate * chunk_duration_ms / 1000)
        interval_seconds = chunk_duration_ms / 1000.0

        send_task = asyncio.create_task(
            send_audio(ws, wf, buffer_size, interval_seconds)
        )
        recv_task = asyncio.create_task(receive_transcription(ws))

        await asyncio.gather(send_task, recv_task)


# Main asynchronous function
async def main():
    global args

    # Fetch API key and customer ID from environment variables
    api_key = os.environ.get("API_KEY")
    customer_id = os.environ.get("CUSTOMER_ID")

    if not api_key or not customer_id:
        print("Please set API key and customer ID in environment variables.")
        return

    parser = argparse.ArgumentParser(add_help=False)

    args, remaining = parser.parse_known_args()

    parser = argparse.ArgumentParser(
        description="ASR Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser],
    )
    parser.add_argument(
        "-u",
        "--uri",
        type=str,
        metavar="URL",
        help="Server URL",
        default="wss://bodhi.navana.ai",
    )
    parser.add_argument("-f", "--file", type=str, help="wave/audio file path")

    args = parser.parse_args(remaining)

    if args.file:
        await run_test(api_key, customer_id)

    if not args.file:
        print(
            "This script is meant to show how to connect to Navana Streaming Speech Recognition API endpoint through websockets\n"
        )
        print(
            "Please pass the file path as an argument to stream a prerecorded audio file\n"
        )
        print("How to run the script:")
        print("python3 streaming_client_demo.py -f streaming_demo.wav")


if __name__ == "__main__":
    asyncio.run(main())
