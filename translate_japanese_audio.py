#!/usr/bin/env python3
"""Japanese-themed GUI app to capture Japanese audio and translate it to English locally."""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk


APP_TITLE = "音声翻訳スタジオ | Japanese Audio Translator"

# Theme colors inspired by traditional Japanese palette.
SAKURA = "#F8D7DA"
WASHI = "#FFF9F0"
INK = "#2B2D42"
RED_ACCENT = "#C1121F"
GREEN_ACCENT = "#2A9D8F"

_MODEL_CACHE: dict[str, object] = {}


def ensure_ffmpeg_installed() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required but not found in PATH.")


def detect_linux_monitor_source() -> str | None:
    try:
        result = subprocess.run(
            ["pactl", "list", "sources", "short"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].endswith(".monitor"):
            return parts[1]
    return None


def build_ffmpeg_command(output_wav: Path, duration: int, device: str | None) -> list[str]:
    system_name = platform.system().lower()

    if "linux" in system_name:
        source = device or detect_linux_monitor_source()
        if source is None:
            raise RuntimeError(
                "Could not auto-detect a PulseAudio monitor source. Please set device manually."
            )
        return [
            "ffmpeg",
            "-y",
            "-f",
            "pulse",
            "-i",
            source,
            "-t",
            str(duration),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_wav),
        ]

    if "darwin" in system_name:
        source = device or ":0"
        return [
            "ffmpeg",
            "-y",
            "-f",
            "avfoundation",
            "-i",
            source,
            "-t",
            str(duration),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_wav),
        ]

    if "windows" in system_name:
        if not device:
            raise RuntimeError(
                "Windows needs a device like: audio=Stereo Mix (Realtek...)"
            )
        return [
            "ffmpeg",
            "-y",
            "-f",
            "dshow",
            "-i",
            device,
            "-t",
            str(duration),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_wav),
        ]

    raise RuntimeError(f"Unsupported platform: {platform.system()}")


def record_audio(output_path: Path, duration: int, device: str | None) -> None:
    ensure_ffmpeg_installed()
    command = build_ffmpeg_command(output_path, duration, device)
    subprocess.run(command, check=True)


def _load_local_model(model_size: str):
    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'openai-whisper'. Install with: pip install openai-whisper"
        ) from exc

    if model_size not in _MODEL_CACHE:
        _MODEL_CACHE[model_size] = whisper.load_model(model_size)
    return _MODEL_CACHE[model_size]


def translate_to_english(audio_path: Path, model_size: str) -> str:
    model = _load_local_model(model_size)
    result = model.transcribe(str(audio_path), task="translate", language="ja")
    text = result.get("text", "").strip()
    if not text:
        raise RuntimeError("No translated text was produced.")
    return text


class TranslatorGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("860x650")
        self.root.configure(bg=WASHI)

        self.input_file_var = tk.StringVar()
        self.device_var = tk.StringVar()
        self.duration_var = tk.StringVar(value="15")
        self.model_var = tk.StringVar(value="base")
        self.status_var = tk.StringVar(value="準備完了 / Ready")

        self._build_style()
        self._build_layout()

    def _build_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Title.TLabel", background=SAKURA, foreground=INK, font=("Meiryo", 18, "bold"))
        style.configure("Header.TLabel", background=WASHI, foreground=INK, font=("Meiryo", 11, "bold"))
        style.configure("Main.TButton", font=("Meiryo", 10, "bold"), padding=8)

    def _build_layout(self) -> None:
        top_banner = tk.Frame(self.root, bg=SAKURA, height=64)
        top_banner.pack(fill="x")
        ttk.Label(top_banner, text=APP_TITLE, style="Title.TLabel").pack(pady=14)

        container = tk.Frame(self.root, bg=WASHI)
        container.pack(fill="both", expand=True, padx=14, pady=12)

        settings = tk.LabelFrame(
            container,
            text="設定 / Settings",
            bg=WASHI,
            fg=INK,
            padx=12,
            pady=10,
            font=("Meiryo", 10, "bold"),
        )
        settings.pack(fill="x")

        ttk.Label(settings, text="録音秒数 (Duration)", style="Header.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(settings, textvariable=self.duration_var, width=12).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(settings, text="Whisperモデル", style="Header.TLabel").grid(row=0, column=2, sticky="e", padx=6, pady=6)
        model_menu = ttk.Combobox(settings, textvariable=self.model_var, values=["tiny", "base", "small", "medium", "large"], width=10, state="readonly")
        model_menu.grid(row=0, column=3, sticky="w", padx=6, pady=6)

        ttk.Label(settings, text="入力デバイス (optional)", style="Header.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(settings, textvariable=self.device_var, width=52).grid(row=1, column=1, sticky="we", padx=6, pady=6, columnspan=3)

        ttk.Label(settings, text="音声ファイル (optional)", style="Header.TLabel").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(settings, textvariable=self.input_file_var, width=52).grid(row=2, column=1, sticky="we", padx=6, pady=6, columnspan=2)
        ttk.Button(settings, text="参照 Browse", style="Main.TButton", command=self._choose_file).grid(row=2, column=3, padx=6, pady=6)

        settings.grid_columnconfigure(1, weight=1)

        button_row = tk.Frame(container, bg=WASHI)
        button_row.pack(fill="x", pady=(12, 8))

        tk.Button(
            button_row,
            text="録音して翻訳 / Record + Translate",
            bg=RED_ACCENT,
            fg="white",
            font=("Meiryo", 10, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self._run_record_and_translate,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            button_row,
            text="ファイルを翻訳 / Translate File",
            bg=GREEN_ACCENT,
            fg="white",
            font=("Meiryo", 10, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self._run_file_translate,
        ).pack(side="left")

        output_frame = tk.LabelFrame(
            container,
            text="英訳結果 / English Translation",
            bg=WASHI,
            fg=INK,
            padx=10,
            pady=8,
            font=("Meiryo", 10, "bold"),
        )
        output_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.output_box = scrolledtext.ScrolledText(
            output_frame,
            wrap="word",
            font=("Meiryo", 11),
            bg="#FFFEFA",
            fg=INK,
            height=18,
        )
        self.output_box.pack(fill="both", expand=True)

        tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            bg=INK,
            fg="white",
            padx=12,
            pady=6,
            font=("Meiryo", 9),
        ).pack(fill="x", side="bottom")

    def _choose_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="音声ファイルを選択 / Select audio file",
            filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All files", "*.*")],
        )
        if file_path:
            self.input_file_var.set(file_path)

    def _run_record_and_translate(self) -> None:
        self._run_async(self._record_and_translate_worker)

    def _run_file_translate(self) -> None:
        self._run_async(self._file_translate_worker)

    def _run_async(self, worker) -> None:
        threading.Thread(target=worker, daemon=True).start()

    def _record_and_translate_worker(self) -> None:
        try:
            duration = int(self.duration_var.get().strip())
            if duration <= 0:
                raise ValueError("Duration must be greater than 0.")
        except ValueError as exc:
            self._set_status(f"エラー / Error: {exc}")
            self._show_error("Invalid Duration", str(exc))
            return

        model_size = self.model_var.get().strip() or "base"
        device = self.device_var.get().strip() or None

        self._set_status("録音中... / Recording...")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                audio_path = Path(tmp) / "captured_audio.wav"
                record_audio(audio_path, duration, device)
                self._set_status("翻訳中... / Translating locally...")
                translation = translate_to_english(audio_path, model_size)
        except Exception as exc:
            self._set_status(f"失敗 / Failed: {exc}")
            self._show_error("Translation Error", str(exc))
            return

        self._show_translation(translation)
        self._set_status("完了 / Done")

    def _file_translate_worker(self) -> None:
        file_value = self.input_file_var.get().strip()
        if not file_value:
            self._show_warning("Missing File", "Please choose an audio file first.")
            return

        audio_path = Path(file_value)
        if not audio_path.exists():
            self._show_error("Missing File", f"File not found: {audio_path}")
            return

        model_size = self.model_var.get().strip() or "base"
        self._set_status("翻訳中... / Translating locally...")
        try:
            translation = translate_to_english(audio_path, model_size)
        except Exception as exc:
            self._set_status(f"失敗 / Failed: {exc}")
            self._show_error("Translation Error", str(exc))
            return

        self._show_translation(translation)
        self._set_status("完了 / Done")

    def _show_translation(self, text: str) -> None:
        self.root.after(0, self._render_translation, text)

    def _render_translation(self, text: str) -> None:
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)

    def _set_status(self, status: str) -> None:
        self.root.after(0, lambda: self.status_var.set(status))

    def _show_error(self, title: str, message: str) -> None:
        self.root.after(0, lambda: messagebox.showerror(title, message))

    def _show_warning(self, title: str, message: str) -> None:
        self.root.after(0, lambda: messagebox.showwarning(title, message))


def main() -> int:
    root = tk.Tk()
    TranslatorGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
