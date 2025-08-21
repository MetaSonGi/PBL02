# cctv.py
# CCTV.zip -> extract to ./CCTV, then view images with left/right arrow navigation.
# Requires: Pillow (PIL). Install:  python -m pip install pillow
#
# Usage:
#   python cctv.py                      # looks for CCTV.zip next to this script, extracts to ./CCTV
#   python cctv.py --dir "C:/path/CCTV" # use an existing folder of images
#
from __future__ import annotations
import argparse
import zipfile
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ZIP = SCRIPT_DIR / "CCTV.zip"
DEFAULT_OUT = SCRIPT_DIR / "CCTV"

def extract_zip_to_folder(zip_path: Path, out_dir: Path) -> None:
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)

def collect_images(folder: Path) -> list[Path]:
    imgs = []
    for ext in SUPPORTED_EXTS:
        imgs.extend(folder.rglob(f"*{ext}"))
        imgs.extend(folder.rglob(f"*{ext.upper()}"))
    # Unique & sorted by name
    imgs = sorted(set(imgs), key=lambda p: p.as_posix().lower())
    return imgs

class CCTVViewer(tk.Tk):
    def __init__(self, images: list[Path]):
        super().__init__()
        self.title("CCTV Viewer")
        self.geometry("1000x700")
        self.configure(bg="#111111")
        self.images = images
        self.idx = 0
        self.label = tk.Label(self, bg="#111111")
        self.label.pack(fill=tk.BOTH, expand=True)
        self.bind("<Right>", self.next_image)
        self.bind("<Left>", self.prev_image)
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Configure>", self._on_resize)  # redraw on window resize
        self.current_tk_img = None
        self.show_image()

    def _fit_image(self, img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        if max_w <= 1 or max_h <= 1:
            return img
        w, h = img.size
        scale = min(max_w / w, max_h / h)
        if scale <= 0:
            return img
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        return img.resize(new_size, Image.LANCZOS)

    def show_image(self):
        if not self.images:
            self.label.config(text="No images found", fg="white")
            return
        path = self.images[self.idx]
        try:
            img = Image.open(path).convert("RGB")
            # Fit to current window
            max_w = self.label.winfo_width() or self.winfo_width()
            max_h = self.label.winfo_height() or self.winfo_height()
            img = self._fit_image(img, max_w-20, max_h-20)
            self.current_tk_img = ImageTk.PhotoImage(img)
            self.label.config(image=self.current_tk_img)
            self.title(f"CCTV Viewer — {path.name}  ({self.idx+1}/{len(self.images)})")
        except Exception as e:
            messagebox.showerror("Open Error", f"Failed to open {path}\n{e}")

    def next_image(self, event=None):
        if not self.images: return
        self.idx = (self.idx + 1) % len(self.images)
        self.show_image()

    def prev_image(self, event=None):
        if not self.images: return
        self.idx = (self.idx - 1) % len(self.images)
        self.show_image()

    def _on_resize(self, event):
        # Redraw current image on resize to keep it fitted
        self.after(50, self.show_image)

def main():
    parser = argparse.ArgumentParser(description="Extract CCTV.zip and browse images with arrow keys.")
    parser.add_argument("--zip", type=str, default=str(DEFAULT_ZIP), help="Path to CCTV.zip (default: alongside script)")
    parser.add_argument("--dir", type=str, default=None, help="Use existing CCTV directory instead of extracting")
    args = parser.parse_args()

    if args.dir:
        cctv_dir = Path(args.dir).expanduser().resolve()
        if not cctv_dir.exists():
            print(f"Directory does not exist: {cctv_dir}")
            sys.exit(1)
    else:
        # Extract CCTV.zip -> ./CCTV
        cctv_dir = DEFAULT_OUT
        if not cctv_dir.exists():
            try:
                extract_zip_to_folder(Path(args.zip).expanduser().resolve(), cctv_dir)
                print(f"Extracted to: {cctv_dir}")
            except Exception as e:
                print(f"Extraction failed: {e}")
                sys.exit(1)

    images = collect_images(cctv_dir)
    if not images:
        print(f"No images found in {cctv_dir}")
        sys.exit(1)

    app = CCTVViewer(images)
    app.mainloop()

if __name__ == "__main__":
    main()
