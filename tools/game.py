"""A modded game driven with horizon-ctl, on fresh data: a temporary game folder (the game keeps its
options, worlds and mods' settings in its working folder) and temporary launcher and XDG folders, with
no audio and no self-update. Nothing touches the player's own data."""
import json
import os
import struct
import subprocess
import tempfile
import time
import zlib
from pathlib import Path


class Game:
    def __init__(self, ctl, resources, out, files=None):
        self.ctl, self.resources, self.out = Path(ctl), Path(resources), Path(out)
        self.files = files or {}

    def __enter__(self):
        self.out.mkdir(parents=True, exist_ok=True)
        self.dirs = [tempfile.mkdtemp(prefix=f"native-proof-{n}-") for n in ("home", "launcher", "data", "config")]
        self.home = Path(self.dirs[0])
        for name, text in self.files.items():
            (self.home / name).parent.mkdir(parents=True, exist_ok=True)
            (self.home / name).write_text(text)
        self.socket = str(Path(tempfile.mkdtemp(prefix="native-ctl-")) / "ctl.sock")
        self.env = dict(os.environ, HORIZON_HOME=self.dirs[0], HORIZON_LAUNCHER_HOME=self.dirs[1],
                        XDG_DATA_HOME=self.dirs[2], XDG_CONFIG_HOME=self.dirs[3],
                        HORIZON_LAUNCHER_NO_SELF_UPDATE="1", HORIZON_NO_AUDIO="1")
        self.run("launch", "--world", "Proof", "--creative", "--offscreen", "--wait",
                 "--resources", str(self.resources))
        time.sleep(3)
        return self

    def __exit__(self, *_):
        subprocess.run([str(self.ctl), "--socket", self.socket, "quit"], env=self.env, cwd=self.home,
                       capture_output=True)

    def run(self, *args):
        done = subprocess.run([str(self.ctl), "--socket", self.socket, *args], env=self.env, cwd=self.home,
                              capture_output=True, text=True, check=True)
        try:
            return json.loads(done.stdout)
        except json.JSONDecodeError:
            return done.stdout

    def play(self):
        """Back to the world from any screen."""
        for _ in range(6):
            if self.run("status").get("screen") == "playing":
                return
            self.run("key", "esc", "tap")
            time.sleep(0.5)
        if self.run("status").get("screen") == "playing":
            return
        raise AssertionError(f"not back in the world: {self.run('status').get('screen')}")

    def labels(self):
        return [w.get("label") for w in self.run("ui").get("widgets", [])]

    def ids(self):
        return {w.get("label"): w.get("id") for w in self.run("ui").get("widgets", [])}

    def shot(self, name):
        path = self.out / f"{name}.png"
        self.run("screenshot", str(path))
        return path


def pixels(path):
    """An 8-bit RGB or RGBA, non-interlaced PNG's (width, height, channels, rows)."""
    data = Path(path).read_bytes()
    pos, chunks, width = 8, b"", 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", body[:10])
            channels = {2: 3, 6: 4}[color]
            assert depth == 8
        elif kind == b"IDAT":
            chunks += body
        pos += 12 + length
    raw, stride, rows, prev = zlib.decompress(chunks), width * channels, [], bytearray(width * channels)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b, c = prev[i], prev[i - channels] if i >= channels else 0
            if kind == 1:
                line[i] = (line[i] + a) & 255
            elif kind == 2:
                line[i] = (line[i] + b) & 255
            elif kind == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return width, height, channels, rows


def difference(a, b, box=(0.0, 0.0, 1.0, 1.0)):
    """The mean difference of two screenshots' colours, 0..255, on a grid of samples, within `box`
    (left, top, right, bottom, as fractions of the screen)."""
    wa, ha, ca, ra = pixels(a)
    _, _, cb, rb = pixels(b)
    total = count = 0
    x0, y0, x1, y1 = int(box[0] * wa), int(box[1] * ha), int(box[2] * wa), int(box[3] * ha)
    for y in range(y0, y1, 4):
        for x in range(x0, x1, 4):
            total += sum(abs(ra[y][x * ca + k] - rb[y][x * cb + k]) for k in range(3))
            count += 3
    return total / count
