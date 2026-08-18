# Bodhi Python SDK Examples

This folder contains example scripts demonstrating how to use the Bodhi Python SDK.

## Prerequisites

1. Set your credentials as environment variables:

   ```bash
   export BODHI_API_KEY='your_api_key'
   export BODHI_CUSTOMER_ID='your_customer_id'
   ```

2. Install required dependencies:
   ```bash
   pip install bodhi-sdk
   ```

## Example Scripts

- `local_transcription.py`: Demonstrates local file transcription
- `remote_transcription.py`: Demonstrates remote URL transcription
- `streaming_transcription.py`: Demonstrates streaming transcription

## Notes

- `TranscriptionConfig` in `bodhi-sdk` 1.2.0 supports `model`, `transaction_id`, `sample_rate`, `parse_number`, `hotwords`, `aux`, `exclude_partial`, `at_start_lid` and `transliterate`. Endpointing (`endpoint_silence_duration`) is not exposed by the SDK yet — use the [direct WebSocket examples](../direct-integration-example/README.md#endpoint-silence-threshold) if you need to tune it.

## Running Examples

```bash
python local_transcription.py
python remote_transcription.py
python streaming_transcription.py
```