# NicholasAndrewGanich

## Japanese-Themed Audio Translator GUI

This project now includes a **Japanese-themed desktop GUI** app:

- File: `translate_japanese_audio.py`
- Purpose: Capture Japanese audio from your computer and translate it into English.

## Requirements

- Python 3.9+
- `ffmpeg` installed and available in `PATH`
- OpenAI Python package:
  - `pip install openai`
- `OPENAI_API_KEY` environment variable set

## Run

```bash
python3 translate_japanese_audio.py
```

## How to use in the app

1. **録音して翻訳 / Record + Translate**
   - Set duration (seconds).
   - (Optional) set your device name.
   - Click the red button to record system audio and translate.

2. **ファイルを翻訳 / Translate File**
   - Pick an audio file with Browse.
   - Click the green button to translate the selected file.

## Notes

- Linux can auto-detect PulseAudio monitor sources.
- macOS and Windows may need a manual audio device value.
- The OpenAI API key is required for translation.
