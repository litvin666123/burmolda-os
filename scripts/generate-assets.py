#!/usr/bin/env python3
"""Generate original Burmolda wallpapers and UI sounds using Python's standard library."""
from __future__ import annotations
import argparse
import math
import random
import struct
import wave
import zlib
from pathlib import Path

W, H = 1600, 900


def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)


def make_wallpaper(path: Path, mode: int) -> None:
    rng = random.Random(900 + mode)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        fy = y / (H - 1)
        for x in range(W):
            fx = x / (W - 1)
            glow = max(0.0, 1.0 - math.sqrt(((fx - (0.72 if mode % 2 == 0 else 0.28)) * 1.2) ** 2 + ((fy - 0.48) * 1.7) ** 2))
            base = (int(10 + 22 * fy), int(7 + 7 * fx), int(18 + 35 * fy))
            accent = (255, 48, 205) if mode in (0, 2) else (126, 70, 255)
            p = [int(base[i] * (1 - glow * 0.38) + accent[i] * glow * 0.38) for i in range(3)]
            if mode == 0:
                radius = math.sqrt((fx - 0.72) ** 2 + (fy - 0.48) ** 2)
                ring = max(0.0, 1.0 - abs(radius - 0.26) / 0.012)
                ring = max(ring, max(0.0, 1.0 - abs(radius - 0.34) / 0.009))
                p = [int(p[i] * (1-ring) + (255, 100, 230)[i] * ring) for i in range(3)]
            elif mode == 1 and (int(fx * 18) + int(fy * 10)) % 4 == 0:
                p = [int(p[i] * 0.7 + (120, 45, 150)[i] * 0.3) for i in range(3)]
            elif mode == 2 and (y // 5) % 31 in (0, 1, 2) and (x // 73) % 4 == 0:
                p = [int(p[i] * 0.4 + (255, 40, 180)[i] * 0.6) for i in range(3)]
            elif mode == 3 and rng.random() < 0.0007:
                p = [230, 205, 255]
            raw.extend(p)
    compressed = zlib.compress(bytes(raw), 7)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    data += chunk(b"IDAT", compressed) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def make_sound(path: Path, tones: list[tuple[float, float]], duration: float, descending: bool = False) -> None:
    rate = 22050
    samples = bytearray()
    for i in range(int(rate * duration)):
        t = i / rate
        freq = tones[0][0]
        for f, start in tones:
            if t >= start:
                freq = f
        if descending:
            freq *= max(0.25, 1 - t / duration * 0.7)
        envelope = min(1.0, t / 0.02) * min(1.0, max(0.0, (duration - t) / 0.07))
        value = math.sin(2 * math.pi * freq * t) * envelope * 0.4
        samples.extend(struct.pack("<h", int(max(-1, min(1, value)) * 32767)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(samples)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", required=True, type=Path)
    root = parser.parse_args().overlay
    wall = root / "usr/share/backgrounds/burmolda"
    snd = root / "usr/share/burmolda/sounds"
    for name, mode in [("01-burmolda-neon.png", 0), ("02-brainrot-grid.png", 1), ("03-chaos-mode.png", 2), ("04-purple-static.png", 3)]:
        make_wallpaper(wall / name, mode)
    make_sound(snd / "intro.wav", [(523.25, 0), (659.25, .16), (783.99, .32), (1046.5, .50)], .9)
    make_sound(snd / "notification.wav", [(880, 0), (1174.66, .16)], .48)
    make_sound(snd / "error.wav", [(440, 0), (330, .16), (220, .34)], .62)
    make_sound(snd / "boing.wav", [(620, 0)], .75, descending=True)
    print("Generated four 1600x900 wallpapers and four synthesized WAV files.")


if __name__ == "__main__":
    main()
