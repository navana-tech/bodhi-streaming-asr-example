
# Navana Streaming ASR Instructions

This repository contains examples and instructions for interacting with the Navana Streaming ASR API.

## Table of Contents

- [Non-SDK Examples](#non-sdk-examples)
- [SDK Examples](#sdk-examples)
- [Available ASR Models](#available-asr-models)
- [Tuning Streaming Behaviour](#tuning-streaming-behaviour)

## Non-SDK Examples

For direct API interaction without using the SDK, refer to the [Non-SDK Examples README](./direct-integration-example/README.md).

## SDK Examples

For examples demonstrating the use of the Bodhi Python SDK, refer to the [SDK Examples README](./python-sdk-examples/README.md).

## Available ASR Models

Every language has a **general** model and a **banking** model. Banking models are tuned for BFSI vocabulary (account numbers, EMI, policy and loan terms); use the general model otherwise.

All models are **bilingual (language + English)** and handle code-switched speech, except the dedicated English model and Gujarati and Odia, which are monolingual.

| Language                 | General               | Banking               | Bilingual with English |
| ------------------------ | --------------------- | --------------------- | ---------------------- |
| Bengali                  | `bn-general-v2-8khz`  | `bn-banking-v2-8khz`  | Yes                    |
| English (en-IN)          | `en-general-v2-8khz`  | `en-banking-v2-8khz`  | English-only           |
| Gujarati                 | `gu-general-v2-8khz`  | `gu-banking-v2-8khz`  | No                     |
| Hindi                    | `hi-general-v2-8khz`  | `hi-banking-v2-8khz`  | Yes                    |
| Hinglish (Hindi–English) | `hi-en-general-v2-8khz` | `hi-en-banking-v2-8khz` | Yes (legacy)         |
| Kannada                  | `kn-general-v2-8khz`  | `kn-banking-v2-8khz`  | Yes                    |
| Malayalam                | `ml-general-v2-8khz`  | `ml-banking-v2-8khz`  | Yes                    |
| Marathi                  | `mr-general-v2-8khz`  | `mr-banking-v2-8khz`  | Yes                    |
| Odia                     | `or-general-v3-8khz`  | _(coming soon)_       | No                     |
| Tamil                    | `ta-general-v2-8khz`  | `ta-banking-v2-8khz`  | Yes                    |
| Telugu                   | `te-general-v2-8khz`  | `te-banking-v2-8khz`  | Yes                    |

Notes:

- The **Hinglish** models are retained for backward compatibility. New integrations should use the Hindi models, which are bilingual by default.
- For pure English audio, prefer the dedicated **English** model over a bilingual one.
- Gujarati and Odia are monolingual today; bilingual upgrades are in progress.

The current list is also published at [Available languages & ASR Models](https://navana.gitbook.io/bodhi/bodhi-overview#available-languages-and-asr-models).

## Tuning Streaming Behaviour

Beyond the model, the streaming config accepts optional flags worth knowing about:

| Flag                        | What it does                                                                 |
| --------------------------- | ---------------------------------------------------------------------------- |
| `endpoint_silence_duration` | Trailing silence, in seconds, before an utterance is finalized (`0.44` - `1.2`, default `0.44`). Lower is faster, higher tolerates pauses. |
| `parse_number`              | Converts spoken numbers into numerals                                        |
| `exclude_partial`           | Emits only `complete` transcripts                                            |
| `hotwords`                  | Boosts domain-specific or rare phrases                                       |

`streaming.py` and `streaming-microphone.py` expose the endpointing threshold as a command-line flag — see [Endpoint Silence Threshold](./direct-integration-example/README.md#endpoint-silence-threshold) for how to tune it, and [Advanced Features](https://navana.gitbook.io/bodhi/quickstart/streaming-websocket/advanced-features) for the rest.
