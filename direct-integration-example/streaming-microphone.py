import argparse
import asyncio
import json
import os
import signal
import sys
import uuid

import numpy as np

EOF_MESSAGE = '{"eof": 1}'

try:
    import sounddevice as sd
except ImportError:
    print("Please install sounddevice first. You can use")
    print()
    print("  pip install sounddevice")
    print()
    sys.exit(-1)

import aiohttp
from aiohttp import WSMsgType


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--server-addr",
        type=str,
        default="wss://bodhi.navana.ai",
        help="Address of the server",
    )

    return parser.parse_args()


def select_device():
    devices = sd.query_devices()
    input_devices = [device for device in devices if device["max_input_channels"] > 0]

    if len(input_devices) == 1:
        selected_device = input_devices[0]
        print(f'Only one input device available: {selected_device["name"]}')
    else:
        print("Available input devices:")
        for idx, device in enumerate(input_devices):
            print(f"{idx}: {device['name']}")

        selected_device_idx = int(input("Select input device (number): "))
        selected_device = input_devices[selected_device_idx]

    print(f'Selected device: {selected_device["name"]}')
    return selected_device["index"], int(selected_device["default_samplerate"])


async def inputstream_generator(device, channels=1, samplerate=16000):
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))

    print()
    print("Bodhi Server Connected! Please speak")

    stream = sd.InputStream(
        callback=callback,
        device=device,
        channels=channels,
        dtype="int16",
        samplerate=samplerate,
        blocksize=int(0.05 * samplerate),
    )

    with stream:
        while True:
            indata, status = await q_in.get()
            yield indata, status


async def receive_transcription(ws):
    complete_sentences = []

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            response_data = json.loads(msg.data)

            error = response_data.get("error")
            if error is not None:
                print(
                    f"Server Error: Type={response_data.get('error')}, Message={response_data.get('message')}, Code={response_data.get('code')}, Timestamp={response_data.get('timestamp')}",
                    file=sys.stderr,
                )
                break

            call_id = response_data["call_id"]
            segment_id = response_data["segment_id"]
            transcript_type = response_data["type"]
            transcript_text = response_data["text"]
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
        elif msg.type == WSMsgType.CLOSE:
            print("WebSocket connection closed by server.")
            break
        elif msg.type == WSMsgType.ERROR:
            print(f"WebSocket error: {msg.data}")
            break

    return complete_sentences


async def run(
    server_addr: str, device: int, samplerate: int, stop_event: asyncio.Event
):
    # Fetch API key and customer ID from environment variables
    api_key = os.environ.get("API_KEY")
    customer_id = os.environ.get("CUSTOMER_ID")

    if not api_key or not customer_id:
        print("Please set API key and customer ID in environment variables.")
        return

    request_headers = {"x-api-key": api_key, "x-customer-id": customer_id}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(
                f"{server_addr}", headers=request_headers
            ) as ws:
                await ws.send_str(
                    json.dumps(
                        {
                            "config": {
                                "sample_rate": samplerate,
                                "transaction_id": str(uuid.uuid4()),
                                "model": "hi-general-v2-8khz",
                                # Change the model based on your preference
                                # Kannada - kn-general-v2-8khz
                                # Hindi - hi-general-v2-8khz
                            }
                        }
                    )
                )

                send_task = asyncio.create_task(
                    send_audio(
                        ws,
                        inputstream_generator(device=device, samplerate=samplerate),
                        stop_event,
                    )
                )
                recv_task = asyncio.create_task(receive_transcription(ws))

                done, pending = await asyncio.wait(
                    [send_task, recv_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                # Ensure the receive task is awaited if it's still running
                if not recv_task.done():
                    await recv_task

                await ws.send_str(EOF_MESSAGE)

        except aiohttp.WSServerHandshakeError as e:
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


async def send_audio(ws, input_generator, stop_event):
    try:
        async for indata, status in input_generator:
            if status:
                print(status)
            await ws.send_bytes(indata.tobytes())
            if stop_event.is_set():
                break
    except asyncio.CancelledError:
        print("Send audio task cancelled.")
    except Exception as e:
        print(f"An error occurred in send_audio: {e}")
    finally:
        pass


async def main():
    args = get_args()

    server_addr = args.server_addr
    device, samplerate = select_device()
    print(f"Using device {device} with samplerate {samplerate}")

    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("\nCaught Ctrl+C. Exiting")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        await run(
            server_addr=server_addr,
            device=device,
            samplerate=samplerate,
            stop_event=stop_event,
        )

    except asyncio.CancelledError:
        print("Main task cancelled")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCaught Ctrl+C. Exiting")
