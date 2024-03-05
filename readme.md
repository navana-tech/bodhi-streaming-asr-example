# Navana Streaming ASR Instructions

## How to Stream

### Connection Instructions

- **Endpoint:** Websocket streaming speech API endpoint

  - `wss://streaming.navana.ai`

- **Sample Script:**
  - `streaming.py` (for static audio files)

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
  - _Usually, a speech segment is 4-10 seconds long_

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
$ python streaming.py -f loan.wav -r 16000
```

Options:
-f: File name of the audio file to be streamed.
-r: Sample rate of the audio file (in this example, set to 16000).

# Available ASR Models for Testing

- **Bengali:** `bn-general-jan24-v1-8khz`
- **Hindi:** `hi-general-feb24-v1-8khz`
- **Kannada:** `kn-general-jan24-v1-8khz`
- **Marathi:** `mr-general-jan24-v1-8khz`
- **Tamil:** `ta-general-jan24-v1-8khz`
- **Telugu:** `te-general-jan24-v1-8khz`

For testing the code, modify the `.py` file with the model name you want to use.
