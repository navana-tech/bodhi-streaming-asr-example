# Navana Streaming ASR Instructions

## How to Stream

### Connection Instructions

- **Endpoint:** Websocket streaming speech API endpoint

  - `wss://bodhi.navana.ai`

- **Sample Script:**
  - `streaming.py` (for static audio files)
  - `streaming-microphone.py` (for real-time audio capture from the microphone)

### Access Token

Store the authentication headers in env to access the streaming speech API endpoints:

```bash
$ export API_KEY=YOUR_API_KEY
$ export CUSTOMER_ID=YOUR_CUSTOMER_ID
```

### Brief Description of Response Format

The received response format will be a JSON object.

```json
{
  "call_id": "CALL_ID",
  "segment_id": "SEGMENT_ID",
  "eos": false,
  "type": "partial",
  "text": "TRANSCRIPT"
}
```

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
$ pip install -r requirements.txt
```

## Usage

```bash
$ python streaming.py -f loan.wav
             OR
$ python streaming-microphone.py
```

Options:
-f: File name of the audio file to be streamed.

# Audio Stream Requirements

To ensure optimal compatibility and performance with our audio processing system, please adhere to the following audio stream requirements:

- **Encoding/Bit Depth**: 16Bit PCM with a 2 Byte depth, providing high-quality audio representation.

- **Minimum Sample Rate**: The audio must have a sample rate of at least 8000Hz.

- **Fixed Streaming Rate**: Audio packets should be streamed at (chunk_duration_ms) a fixed size (50 - 500 ms), ensuring consistent data flow. We recommend using 100 ms as shown in the example script.

- **Channels**: Audio must be single-channel (Mono) to ensure compatibility with our processing pipeline.

- **Speakers**: Initially, support is provided for a single speaker per channel. However, support for multiple speakers on a single channel is under development and will be announced soon.

# Available ASR Models for Testing

- **Hindi:** `hi-general-v2-8khz`
- **Kannada:** `kn-general-v2-8khz`

For testing the code, modify the `.py` file with the model name you want to use.
