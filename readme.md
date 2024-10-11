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

$  pip  install  -r  requirements.txt

```

## Usage

```bash

$  python  streaming.py  -f  loan.wav

OR

$  python  streaming-microphone.py

OR

$  python3  non-streaming-api.py  -f  loan.wav

```

Options:

-f: File name of the audio file to be streamed.


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
                        }
                    }
                )
            )
```

# Audio Stream Requirements

To ensure optimal compatibility and performance with our audio processing system, please adhere to the following audio stream requirements:

- **Encoding/Bit Depth**: 16Bit PCM with a 2 Byte depth, providing high-quality audio representation.

- **Minimum Sample Rate**: The audio must have a sample rate of at least 8000Hz.

- **Fixed Streaming Rate**: Audio packets should be streamed at (chunk_duration_ms) a fixed size (50 - 500 ms), ensuring consistent data flow. We recommend using 100 ms as shown in the example script.

- **Channels**: Audio must be single-channel (Mono) to ensure compatibility with our processing pipeline.

- **Speakers**: Initially, support is provided for a single speaker per channel. However, support for multiple speakers on a single channel is under development and will be announced soon.

# Available ASR Models for Testing

- **Hindi:** `hi-general-v2-8khz`

- **Hindi-Banking:** `hi-banking-v2-8khz`

- **Kannada:** `kn-general-v2-8khz`

- **Kannada-Banking:** `kn-banking-v2-8khz`

- **Marathi:** `mr-general-v2-8khz`

- **Marathi Banking:** `mr-banking-v2-8khz`

- **Tamil:** `ta-general-v2-8khz`

- **Tamil Banking:** `ta-banking-v2-8khz`

- **Bengali** `bn-general-v2-8khz`

- **Bengali Banking** `bn-banking-v2-8khz`

- **English** `en-general-v2-8khz`

- **English Banking** `en-banking-v2-8khz`

- **Gujarati** `gu-general-v2-8khz`

- **Gujarati Banking** `gu-banking-v2-8khz`

- **Telugu** `te-general-v2-8khz`

- **Telugu Banking** `te-banking-v2-8khz`

- **Malayalam** `ml-general-v2-8khz`

- **Malayalam Banking** `ml-banking-v2-8khz`

For testing the code, modify the `.py` file with the model name you want to use.
