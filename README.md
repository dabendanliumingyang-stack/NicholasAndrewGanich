# NicholasAndrewGanich

## Japanese-Themed Audio Translator GUI (No API Key)

This project includes a **Japanese-themed desktop GUI** app:

- File: `translate_japanese_audio.py`
- Purpose: Capture Japanese audio from your computer and translate it into English
- Translation mode: **Local Whisper model** (no OpenAI API key required)

## Requirements

- Python 3.9+
- `ffmpeg` installed and available in `PATH`
- Local Whisper package:
  - `pip install openai-whisper`

## Run

```bash
python3 translate_japanese_audio.py
```

## How to use in the app

1. Pick a Whisper model (`tiny`, `base`, `small`, `medium`, `large`).
2. Use **録音して翻訳 / Record + Translate** for live capture.
3. Or use **ファイルを翻訳 / Translate File** for an existing audio file.

## Notes

- Linux can auto-detect PulseAudio monitor sources.
- macOS and Windows may need a manual audio device value.
- First-time model load may take longer while model weights download/cache.
