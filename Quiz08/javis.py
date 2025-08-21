 # javis.py
# Microphone recorder + STT (Vosk) for recorded files.
# Recording:
#   - Saves to ./records/YYYYMMDD-HHMMSS.wav
#   - Dependencies: sounddevice, soundfile
# STT:
#   - Uses Vosk (offline) with a local model path
#   - Output CSV: same basename as audio, in ./records/, columns = "time_in_file_sec, text"
#   - Dependencies: vosk
#
# Install:
#   python -m pip install sounddevice soundfile vosk
# Download a Vosk model (example small EN):
#   https://alphacephei.com/vosk/models
#   Unzip and pass the folder path via --model or set env VOSK_MODEL_PATH
#
# Usage:
#   # List input devices
#   python javis.py --list-devices
#   # Record until Enter
#   python javis.py
#   # Record fixed duration
#   python javis.py --duration 5
#   # Run STT for all WAVs in ./records
#   python javis.py --stt --model "C:/path/to/vosk-model-small-en-us-0.15"
#   # Run STT for a single file
#   python javis.py --stt-file ./records/20250822-142355.wav --model "C:/path/to/model"
#
from __future__ import annotations
import argparse
import sys
import threading
import queue
from datetime import datetime
from pathlib import Path
import os
import json
import csv
from typing import Iterable, Optional

import sounddevice as sd
import soundfile as sf

RECORD_DIR = Path(__file__).resolve().parent / "records"
RECORD_DIR.mkdir(exist_ok=True)

def timestamp_name() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def list_input_devices() -> None:
    print("=== Input Devices ===")
    devices = sd.query_devices()
    default_in = sd.default.device[0]
    for idx, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            star = "*" if idx == default_in else " "
            print(f"{star} [{idx:>2}] {d['name']}  (in:{d['max_input_channels']}, out:{d['max_output_channels']})")

def list_recordings() -> list[Path]:
    files = sorted(RECORD_DIR.glob("*.wav"))
    print("=== Recordings ===")
    if not files:
        print("(no wav files in ./records)")
    for p in files:
        print(p.name)
    return files

def record_to_file(duration: Optional[float], device: Optional[int], samplerate: int, channels: int) -> Path:
    q: queue.Queue = queue.Queue()

    def cb(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    filename = f"{timestamp_name()}.wav"
    filepath = RECORD_DIR / filename

    with sf.SoundFile(str(filepath), mode="x", samplerate=samplerate, channels=channels, subtype="PCM_16") as wav:
        with sd.InputStream(samplerate=samplerate, device=device, channels=channels, callback=cb):
            print(f"Recording...  device={device if device is not None else 'default'}  rate={samplerate}Hz  ch={channels}")
            print(f"Press Enter to stop (or wait {duration}s if provided).")
            stop_event = threading.Event()

            def wait_for_enter():
                try:
                    _ = input()
                except EOFError:
                    pass
                stop_event.set()

            if duration is None:
                t = threading.Thread(target=wait_for_enter, daemon=True)
                t.start()

            start_time = datetime.now()
            try:
                if duration is None:
                    while not stop_event.is_set():
                        wav.write(q.get())
                else:
                    frames_to_write = int(duration * samplerate)
                    frames_written = 0
                    while frames_written < frames_to_write:
                        chunk = q.get()
                        wav.write(chunk)
                        frames_written += len(chunk)
            except KeyboardInterrupt:
                print("\nInterrupted by user.")
            finally:
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"Saved: {filepath}  (elapsed {elapsed:.1f}s)")

    return filepath

# ---------------- STT (Vosk) ----------------
def _load_vosk_model(model_path: Optional[str]):
    from vosk import Model
    mp = model_path or os.environ.get("VOSK_MODEL_PATH")
    if not mp:
        raise RuntimeError("Vosk model path is required. Use --model or set env VOSK_MODEL_PATH")
    mp = str(Path(mp).expanduser().resolve())
    if not Path(mp).exists():
        raise FileNotFoundError(f"Vosk model path not found: {mp}")
    return Model(mp)

def _iter_wav_frames(path: Path, block_size: int = 8000) -> Iterable[bytes]:
    # Read audio and yield int16 bytes blocks (mono)
    with sf.SoundFile(str(path), mode="r") as f:
        samplerate = f.samplerate
        channels = f.channels
        while True:
            data = f.read(block_size, dtype="int16", always_2d=True)
            if len(data) == 0:
                break
            # downmix to mono if needed
            if channels > 1:
                mono = data.mean(axis=1).astype("int16")
                yield mono.tobytes()
            else:
                yield data.tobytes()

def stt_file_to_csv(audio_path: Path, model_path: Optional[str] = None) -> Path:
    """
    Transcribe a single WAV file to CSV with columns: time_in_file_sec, text
    """
    from vosk import KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)  # silence Vosk logs

    audio_path = audio_path.resolve()
    out_csv = audio_path.with_suffix(".csv")

    # Open to get samplerate
    with sf.SoundFile(str(audio_path), "r") as f:
        samplerate = f.samplerate

    model = _load_vosk_model(model_path)
    rec = KaldiRecognizer(model, samplerate)
    rec.SetWords(True)

    segments = []  # (time_sec, text)

    for chunk in _iter_wav_frames(audio_path):
        if rec.AcceptWaveform(chunk):
            res = json.loads(rec.Result())
            text = res.get("text", "").strip()
            words = res.get("result", [])
            if text:
                t0 = words[0]["start"] if words else None
                segments.append((t0 if t0 is not None else None, text))

    # final partial
    final = json.loads(rec.FinalResult())
    text = final.get("text", "").strip()
    words = final.get("result", [])
    if text:
        t0 = words[0]["start"] if words else None
        segments.append((t0 if t0 is not None else None, text))

    # write CSV
    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["time_in_file_sec", "text"])
        for t, tx in segments:
            # Format time as seconds with 2 decimals; None -> 0.00
            ts = f"{(t if t is not None else 0.0):.2f}"
            w.writerow([ts, tx])

    print(f"STT saved: {out_csv}")
    return out_csv

def stt_all_records(model_path: Optional[str] = None) -> list[Path]:
    files = list(RECORD_DIR.glob("*.wav"))
    if not files:
        print("No WAV files found in ./records")
        return []
    result_csvs = []
    for p in files:
        try:
            out = stt_file_to_csv(p, model_path=model_path)
            result_csvs.append(out)
        except Exception as e:
            print(f"STT failed for {p.name}: {e}", file=sys.stderr)
    return result_csvs

# ---------------- CLI ----------------
def main():
    parser = argparse.ArgumentParser(description="Record microphone (./records) and run offline STT (Vosk).")
    parser.add_argument("--list-devices", action="store_true", help="list input devices")
    parser.add_argument("--list-recordings", action="store_true", help="list WAV files in ./records")
    parser.add_argument("--device", type=int, default=None, help="input device index")
    parser.add_argument("--rate", type=int, default=44100, help="sample rate")
    parser.add_argument("--channels", type=int, default=1, help="number of input channels (1=mono, 2=stereo)")
    parser.add_argument("--duration", type=float, default=None, help="seconds to record (omit = Enter to stop)")

    parser.add_argument("--stt", action="store_true", help="run STT on all WAVs in ./records")
    parser.add_argument("--stt-file", type=str, default=None, help="run STT on a single WAV file")
    parser.add_argument("--model", type=str, default=None, help="vosk model path (or set VOSK_MODEL_PATH)")

    args = parser.parse_args()

    if args.list_devices:
        list_input_devices()
        return
    if args.list_recordings:
        list_recordings()
        return

    # If STT requested, do not record; just transcribe
    if args.stt or args.stt_file:
        if args.stt_file:
            audio = Path(args.stt_file)
            stt_file_to_csv(audio, model_path=args.model)
        else:
            stt_all_records(model_path=args.model)
        return

    # Default: record
    try:
        path = record_to_file(duration=args.duration, device=args.device, samplerate=args.rate, channels=args.channels)
        print(path)
    except Exception as e:
        print(f"Recording failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
