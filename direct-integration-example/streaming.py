import aiohttp
import asyncio
import wave
import sys
import json
import os
import uuid
import ssl
import argparse

EOF_MESSAGE = '{"eof": 1}'

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


# Helper function for argument parsing
def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text


async def receive_transcription(ws):
    complete_sentences = []
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                response_data = json.loads(msg.data)

                # server will return an error if anything goes wrong, check for that before proceeding with the logic
                error = response_data.get("error")

                if error is not None:
                    print(
                        f"Server Error: Type={response_data.get('error')}, Message={response_data.get('message')}, Code={response_data.get('code')}, Timestamp={response_data.get('timestamp')}",
                        file=sys.stderr,
                    )
                    break

                call_id = response_data.get("call_id")
                segment_id = response_data.get("segment_id")
                transcript_type = response_data.get("type")
                transcript_text = response_data.get("text")
                end_of_stream = response_data.get("eos", False)

                if transcript_type == "complete" and transcript_text != "":
                    complete_sentences.append(transcript_text)

                print(
                    f"Received data: Call_id={call_id}, "
                    f"Segment_id={segment_id}, "
                    f"EOS={end_of_stream}, "
                    f"Type={transcript_type}, "
                    f"Text={transcript_text}"
                )

                if end_of_stream:
                    print("Complete transcript: ", ", ".join(complete_sentences))
                    break

            except json.JSONDecodeError:
                print(f"Received a non-JSON response: {msg.data}")

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print(f"WebSocket error: {ws.exception()}")
            break
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            break


async def send_audio(ws, wf, sample_rate):
    REALTIME_RESOLUTION = 0.02  # 20ms
    byte_rate = sample_rate * wf.getsampwidth() * wf.getnchannels()

    data = wf.readframes(wf.getnframes())
    audio_cursor = 0

    while len(data):
        chunk_size = int(byte_rate * REALTIME_RESOLUTION)
        chunk, data = data[:chunk_size], data[chunk_size:]
        await ws.send_bytes(chunk)
        audio_cursor += REALTIME_RESOLUTION
        await asyncio.sleep(REALTIME_RESOLUTION)

    # Send EOF JSON message
    await ws.send_str(EOF_MESSAGE)


async def run_test(api_key, customer_id, uri, filepath):
    request_headers = {
        "x-api-key": api_key,
        "x-customer-id": customer_id,
    }
    connector = aiohttp.TCPConnector(
        ssl=ssl_context if uri.startswith("wss://") else None
    )

    async with aiohttp.ClientSession(
        connector=connector, headers=request_headers
    ) as session:
        try:
            async with session.ws_connect(uri) as ws:
                wf = wave.open(filepath, "rb")
                channels, sample_width, sample_rate, num_samples, _, _ = wf.getparams()
                print(
                    f"Channels = {channels}, Sample Rate = {sample_rate} Hz, Sample width = {sample_width} bytes",
                    file=sys.stderr,
                )

                # Send initial config
                config_msg = json.dumps(
                    {
                        "config": {
                            "sample_rate": sample_rate,
                            "transaction_id": str(uuid.uuid4()),
                            "model": "hi-banking-v2-8khz",
                            # Change the model based on your preference
                            # Kannada - kn-banking-v2-8khz
                            # Hindi - hi-banking-v2-8khz
                            # Marathi - mr-banking-v2-8khz
                            # Tamil - ta-banking-v2-8khz
                            # Bengali - bn-banking-v2-8khz
                            # English - en-banking-v2-8khz
                            # Gujarati - gu-banking-v2-8khz
                            # Malayalam - ml-banking-v2-8khz
                        }
                    }
                )
                await ws.send_str(config_msg)

                send_task = asyncio.create_task(send_audio(ws, wf, sample_rate))
                recv_task = asyncio.create_task(receive_transcription(ws))

                await asyncio.gather(send_task, recv_task)

        except aiohttp.WSServerHandshakeError as e:
            print(
                f"WebSocket handshake failed with status code: {e.status}",
                file=sys.stderr,
            )
            if e.status == 401:
                print("Invalid API key or customer ID.", file=sys.stderr)
            elif e.status == 402:
                print("Insufficient balance.", file=sys.stderr)
            elif e.status == 403:
                print("Customer has been deactivated", file=sys.stderr)
        except aiohttp.ClientConnectionError as e:
            print(f"Connection error: {str(e)}", file=sys.stderr)
        except Exception as e:
            print(f"An error occurred: {str(e)}", file=sys.stderr)
            import traceback

            print("Full error traceback:", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)


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
        await run_test(api_key, customer_id, args.uri, args.file)
    else:
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
