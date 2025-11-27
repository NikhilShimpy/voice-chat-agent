# Voice Chat Agent

A low-latency voice chat application with real-time speech recognition and text-to-speech capabilities.

## Features

- Real-time voice capture and streaming (PCM16)
- Dual ASR provider support (AssemblyAI & Deepgram)
- Streaming TTS with Murf AI
- OpenAI integration for intelligent responses
- WebSocket-based real-time communication
- Production-ready with Docker deployment

## Environment Setup

1. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env