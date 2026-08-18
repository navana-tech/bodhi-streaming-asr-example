# Navana Streaming ASR Instructions

## How to use

### Connection Instructions for streaming

- **Endpoint:** Websocket streaming speech API endpoint

- `wss://bodhi.navana.ai`

- **Sample Script:**

- `streaming.py` (for static audio files)

- `streaming-microphone.py` (for real-time audio capture from the microphone)

### Connection Instructions for non streaming

- **Endpoint:** Websocket streaming speech API endpoint

- `https://bodhi.navana.ai/api/transcribe`

- **Sample Script:**

- `non-streaming-api.py` (for local audio files)

### Access Token

Store the authentication headers in env to access the streaming speech API endpoints:

```bash

$  export  API_KEY=YOUR_API_KEY

$  export  CUSTOMER_ID=YOUR_CUSTOMER_ID

```

### Brief Description of Response Format

The received response format will be a JSON object.

```json
{
  "call_id": "CALL_ID",

  "text": "TRANSCRIPT",

  "segment_id": "SEGMENT_ID",

  "eos": false,

  "type": "partial"
}
```

**Note**: This JSON structure outlines the fields returned in responses. However, `segment_id`, `eos`, and `type` are exclusive to streaming responses.

#### Keys Description

- **Call_id:**

- _Unique identifier associated with every streaming connection_

- **Segment_id:**

- _Unique identifier associated with every speech segment during the entire active socket connection_

- **Text:**

- _If type = "partial"_

- _Partial transcript corresponding to every streaming audio chunk_

- _Partial transcripts for every audio chunk (will be for a 100ms audio chunk if streaming audio packet size is 100ms)_

- _If type = "complete"_

- _Complete/final transcript generated for each speech segment_

- _Generated once per segment_id i.e., when the speech segment end is reached_

- **eos:**

- _If 'eos' is true, marks the end of the streaming connection_

#### Install packages

```bash

$  pip install -r requirements.txt

```

## Running Examples

```bash

$  python streaming.py -f ../loan.wav

OR

$  python streaming-microphone.py

OR

$  python3 non-streaming-api.py -f ../loan.wav

```

Options for `streaming.py`:

- `-f`: File name of the audio file to be streamed.

- `-m`: Model to transcribe with, e.g. `hi-banking-v2-8khz`. Defaults to `hi-banking-v2-8khz`. See the [model list](../README.md#available-asr-models).

- `-e`: `endpoint_silence_duration` in seconds (`0.44` - `1.2`). Defaults to `0.44`. See [Endpoint Silence Threshold](#endpoint-silence-threshold).

- `-u`: Server URL. Defaults to `wss://bodhi.navana.ai`.

`streaming-microphone.py` takes the same two tuning options as `--model` and `--endpoint-silence-duration`.


# Configuring the websocket

After connecting to the websocket, you are required to send a configuration object specifying the model you would like to interact with amongst other options. You can do so in the following fashion: 

```
await ws.send(
                json.dumps(
                    {
                        "config": {
                            "sample_rate": sample_rate, // Required - specify the sample rate of the audio being streamed to the server. 
                            "transaction_id": str(uuid.uuid4()), // Required - generate a unique UUID to tag the session
                            "model": "hi-general-v2-8khz", // Required - specify the model you would like to use 
                            "parse_number" : True, // Optional - convert text representing numbers into numericals
                            "exclude_partial": True,  // Optional - only provide complete responses
                            "endpoint_silence_duration": 0.44, // Optional - trailing silence, in seconds, after which an utterance is finalized (0.44 - 1.2, default 0.44)
                        }
                    }
                )
            )
```

# Endpoint Silence Threshold

`endpoint_silence_duration` controls **endpointing**: how much trailing silence the recognizer waits for before it closes an utterance and emits a `complete` transcript. For a voice agent, that final transcript is the cue to respond, so this parameter directly trades response latency against interrupting the caller.

| Property        | Value                                                          |
| --------------- | -------------------------------------------------------------- |
| Unit            | Seconds                                                        |
| Default         | `0.44` — applied when the parameter is not provided            |
| Minimum         | `0.44` — any lower value is automatically clamped up to `0.44` |
| Maximum         | `1.2` — any higher value is automatically capped at `1.2`      |

Both streaming scripts expose it as a flag, so you can compare settings against the same audio without editing code:

```bash

$  python streaming.py -f ../loan.wav -e 0.44   # default: fastest finals

$  python streaming.py -f ../loan.wav -e 0.8    # tolerates longer pauses

$  python streaming-microphone.py --endpoint-silence-duration 0.8

```

Each response line prints an `EndpointLag` value — the time between the last `partial` and the `complete` for that segment, which is approximately `endpoint_silence_duration` plus network and compute overhead. Use it to see the effect of a change.

How to tune it:

- If the agent **cuts callers off**, or one sentence arrives as several `complete` segments, the threshold is too low. Raise it in small steps (`0.45`, `0.5`, `0.55`).
- If the agent **responds too late**, lower it back towards `0.44`.
- Keep the lowest value at which cut-offs are acceptable — every extra 100 ms here is 100 ms added to every agent turn.
- Speech with deliberate mid-sentence pauses (reading out an account number, thinking aloud) needs a higher value than fast conversational speech.

Full reference: [Configurable Endpoint Silence Threshold](https://navana.gitbook.io/bodhi/quickstart/streaming-websocket/advanced-features#configurable-endpoint-silence-threshold)

# Audio Stream Requirements

To ensure optimal compatibility and performance with our audio processing system, please adhere to the following audio stream requirements:

- **Encoding/Bit Depth**: 16Bit PCM with a 2 Byte depth, providing high-quality audio representation.

- **Minimum Sample Rate**: The audio must have a sample rate of at least 8000Hz.

- **Fixed Streaming Rate**: Audio packets should be streamed at (chunk_duration_ms) a fixed size (50 - 500 ms), ensuring consistent data flow. We recommend using 100 ms as shown in the example script.

- **Channels**: Audio must be single-channel (Mono) to ensure compatibility with our processing pipeline.

- **Speakers**: Initially, support is provided for a single speaker per channel. However, support for multiple speakers on a single channel is under development and will be announced soon.

To test a different model, pass it on the command line (`-m` / `--model`) rather than editing the script.
