import argparse
import asyncio
import json
import os
import signal
import sys
import uuid

import numpy as np

try:
    import sounddevice as sd
except ImportError:
    print("Please install sounddevice first. You can use")
    print()
    print("  pip install sounddevice")
    print()
    sys.exit(-1)

try:
    import websockets
except ImportError:
    print("please run:")
    print("")
    print("  pip3 install websockets")
    print("")
    sys.exit(-1)


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
    return selected_device["index"]


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

    async for response in ws:
        try:
            response_data = json.loads(response)

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
        except Exception as e:
            if isinstance(e, websockets.exceptions.ConnectionClosedOK):
                print("WebSocket connection closed.")
            else:
                print(f"An error occurred: {e}")

    return complete_sentences


async def run(server_addr: str, device: int, stop_event: asyncio.Event):
    # Fetch API key and customer ID from environment variables
    api_key = os.environ.get("API_KEY")
    customer_id = os.environ.get("CUSTOMER_ID")

    if not api_key or not customer_id:
        print("Please set API key and customer ID in environment variables.")
        return

    request_headers = {
        "x-api-key": api_key,
        "x-customer-id": customer_id,
    }

    async with websockets.connect(
        f"{server_addr}", extra_headers=request_headers
    ) as ws:
        await ws.send(
            json.dumps(
                {
                    "config": {
                        "sample_rate": 16000,
                        "transaction_id": str(uuid.uuid4()),
                        "model": "hi-general-v2-8khz",
                        # Change the model based on your preference
                        # Kannada - kn-general-v2-8khz
                        # Hindi - hi-general-v2-8khz
                    }
                }
            )
        )

        receive_task = asyncio.create_task(receive_transcription(ws))

        try:
            async for indata, status in inputstream_generator(device=device):
                if status:
                    print(status)
                await ws.send(indata.tobytes())  # Send raw bytes directly
                if stop_event.is_set():
                    break
        except asyncio.CancelledError:
            print("Run task cancelled")
            raise
        except Exception as e:
            print(f"An error occurred in run: {e}")
        finally:
            await ws.send('{"eof": 1}')
            await receive_task


async def main():
    args = get_args()

    server_addr = args.server_addr
    device = select_device()

    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("\nCaught Ctrl+C. Exiting")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        await run(
            server_addr=server_addr,
            device=device,
            stop_event=stop_event,
        )
    except asyncio.CancelledError:
        print("Main task cancelled")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCaught Ctrl+C. Exiting")
