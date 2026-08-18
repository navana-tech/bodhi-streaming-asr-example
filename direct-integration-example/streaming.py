import aiohttp
import asyncio
import wave
import sys
import json
import os
import uuid
import ssl
import time
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

    # Timestamp of the most recent partial per segment. The gap between that and the
    # "complete" for the same segment is roughly the endpointing delay, i.e. the
    # endpoint_silence_duration you configured plus network and compute overhead.
    # Watch this number while tuning endpoint_silence_duration.
    last_partial_at = {}

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

                endpoint_lag = "n/a"
                if transcript_type == "partial":
                    last_partial_at[segment_id] = time.monotonic()
                elif transcript_type == "complete":
                    started = last_partial_at.pop(segment_id, None)
                    if started is not None:
                        endpoint_lag = f"{time.monotonic() - started:.2f}s"
                    if transcript_text != "":
                        complete_sentences.append(transcript_text)

                print(
                    f"Received data: Call_id={call_id}, "
                    f"Segment_id={segment_id}, "
                    f"EOS={end_of_stream}, "
                    f"Type={transcript_type}, "
                    f"EndpointLag={endpoint_lag}, "
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

    while len(data):
        chunk_size = int(byte_rate * REALTIME_RESOLUTION)
        chunk, data = data[:chunk_size], data[chunk_size:]
        await ws.send_bytes(chunk)
        await asyncio.sleep(REALTIME_RESOLUTION)

    # Send EOF JSON message
    await ws.send_str(EOF_MESSAGE)


async def run_test(
    api_key, customer_id, uri, filepath, model, endpoint_silence_duration
):
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
                            # Pass a different model with -m / --model. See the full list
                            # in the repository README. All models except English,
                            # Gujarati and Odia are bilingual with English.
                            "model": model,
                            # Trailing silence, in seconds, after which the recognizer
                            # closes the utterance and emits a "complete" transcript.
                            # Default 0.44; the server clamps the value to 0.44 - 1.2.
                            # Lower  -> faster finals, but a natural pause can split a sentence.
                            # Higher -> tolerates pauses, at the cost of that much extra latency.
                            # Raise it in small steps (0.45, 0.5, 0.55) if your voice agent
                            # cuts callers off, and keep the lowest value that behaves well.
                            # https://navana.gitbook.io/bodhi/quickstart/streaming-websocket/advanced-features#configurable-endpoint-silence-threshold
                            "endpoint_silence_duration": endpoint_silence_duration,
                        }
                    }
                )
                print(
                    f"Using model={model}, "
                    f"endpoint_silence_duration={endpoint_silence_duration}s",
                    file=sys.stderr,
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
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="ASR model to use, e.g. hi-banking-v2-8khz (see README for the full list)",
        default="hi-banking-v2-8khz",
    )
    parser.add_argument(
        "-e",
        "--endpoint-silence-duration",
        type=float,
        metavar="SECONDS",
        help="Trailing silence after which an utterance is finalized (0.44 - 1.2 seconds)",
        default=0.44,
    )

    args = parser.parse_args(remaining)

    if args.file:
        await run_test(
            api_key,
            customer_id,
            args.uri,
            args.file,
            args.model,
            args.endpoint_silence_duration,
        )
    else:
        print(
            "This script is meant to show how to connect to Navana Streaming Speech Recognition API endpoint through websockets\n"
        )
        print(
            "Please pass the file path as an argument to stream a prerecorded audio file\n"
        )
        print("How to run the script:")
        print("python3 streaming.py -f ../loan.wav")
        print("python3 streaming.py -f ../loan.wav -m hi-banking-v2-8khz -e 0.6")


if __name__ == "__main__":
    asyncio.run(main())
