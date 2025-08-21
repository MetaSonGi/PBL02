# javis.py
# System microphone recorder (saves to ./records/YYYYMMDD-HHMMSS.wav)
# Dependencies: sounddevice, soundfile
#   pip install sounddevice soundfile
#
# Usage examples:
#   python javis.py --list                 # list input devices
#   python javis.py                        # record from default mic, press Enter to stop
#   python javis.py --duration 10          # record 10 seconds then save
#   python javis.py --device 1 --rate 48000 --channels 2

from __future__ import annotations
import argparse
import sys
import threading
import queue
from datetime import datetime
from pathlib import Path

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

def record_to_file(duration: float | None, device: int | None, samplerate: int, channels: int) -> Path:
    """
    Record audio from the system microphone.
    If duration is None: record until user presses Enter.
    Otherwise: record for 'duration' seconds.
    """
    q: queue.Queue = queue.Queue()

    def cb(indata, frames, time, status):
        if status:
            # Non-fatal warnings (underflow/overflow) printed to stderr
            print(status, file=sys.stderr)
        q.put(indata.copy())

    # Prepare filename/path
    filename = f"{timestamp_name()}.wav"
    filepath = RECORD_DIR / filename

    # Open audio stream
    with sf.SoundFile(str(filepath), mode="x", samplerate=samplerate, channels=channels, subtype="PCM_16") as wav:
        with sd.InputStream(samplerate=samplerate, device=device, channels=channels, callback=cb):
            print(f"Recording...  device={device if device is not None else 'default'}  "
                  f"rate={samplerate}Hz  ch={channels}")
            print(f"Press Enter to stop (or wait {duration}s if provided).")
            stop_event = threading.Event()

            # Stopper thread (Enter key)
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
                    # Run until Enter
                    while not stop_event.is_set():
                        wav.write(q.get())
                else:
                    # Run for fixed duration
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

def main():
    parser = argparse.ArgumentParser(description="Record microphone audio to ./records/YYYYMMDD-HHMMSS.wav")
    parser.add_argument("--list", action="store_true", help="list input devices")
    parser.add_argument("--device", type=int, default=None, help="input device index")
    parser.add_argument("--rate", type=int, default=44100, help="sample rate")
    parser.add_argument("--channels", type=int, default=1, help="number of input channels (1=mono, 2=stereo)")
    parser.add_argument("--duration", type=float, default=None, help="seconds to record (omit to press Enter to stop)")
    args = parser.parse_args()

    if args.list:
        list_input_devices()
        return

    try:
        path = record_to_file(duration=args.duration, device=args.device, samplerate=args.rate, channels=args.channels)
        print(path)
    except Exception as e:
        print(f"Recording failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
