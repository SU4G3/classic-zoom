<div align="center">
  <img src=".github/icon.png" width="128" height="128" alt="Classic Zoom icon">

  # Classic Zoom

  **Hold V, zoom 3x, scroll for more. For Horizon.**

  [![Latest release](https://img.shields.io/github/v/release/SU4G3/classic-zoom?label=release&color=2e7d32)](https://github.com/SU4G3/classic-zoom/releases/latest)
  [![Build](https://img.shields.io/github/actions/workflow/status/SU4G3/classic-zoom/build.yml?branch=main&label=build)](https://github.com/SU4G3/classic-zoom/actions/workflows/build.yml)
  [![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)
  [![Minecraft](https://img.shields.io/badge/minecraft-26.3-5865F2)](#compatibility)
  [![Horizon native mod](https://img.shields.io/badge/horizon-native%20mod-F0795A)](https://github.com/horizon-rust/horizon/blob/main/docs/native-mods.md)
</div>

<br>

A zoom mod for [Horizon](https://github.com/horizon-rust/horizon), the Rust
rewrite of Minecraft: Java Edition 26.3. It brings the feel of
[WI Zoom](https://github.com/Wurst-Imperium/WI-Zoom) to Horizon: one key,
an instant zoom, the mouse wheel for more, and nothing to configure.

Since 2.0.0 it is a **native mod**: Horizon is removing WebAssembly code
mods, so the launcher now builds Classic Zoom into the game. The
WebAssembly 1.0.0 stays in [Releases](https://github.com/SU4G3/classic-zoom/releases/tag/v1.0.0)
for Horizon versions that still run it.

> **[Download the latest release →](https://github.com/SU4G3/classic-zoom/releases/latest)**

<details>
<summary><b>Table of contents</b></summary>

- [Controls](#controls)
- [How it differs from Horizon's own Zoom](#how-it-differs-from-horizons-own-zoom)
- [Differences from WI Zoom](#differences-from-wi-zoom)
- [Installing](#installing)
- [Verifying a download](#verifying-a-download)
- [What a native mod can do](#what-a-native-mod-can-do)
- [Compatibility](#compatibility)
- [Building](#building)
- [License](#license)

</details>

---

## Controls

| Action | Result |
|---|---|
| Hold **V** | Zoom in 3x |
| Scroll up / down while holding V | Zoom in / out, ×1.1 per wheel step, from 1x to 10x |
| Release V | Back to normal view at once |

While V is held, the mouse wheel zooms instead of switching hotbar slots,
and turning slows down in step with the zoom so aiming stays steady. The
key can be rebound on the mod's page in Options > Mods.

## How it differs from Horizon's own Zoom

Horizon ships an official Zoom mod. Classic Zoom is for players who want
the WI Zoom feel instead:

| | Horizon Zoom | Classic Zoom |
|---|---|---|
| Default key | Z | V |
| Starting zoom | 4x (configurable) | 3x |
| Range | 1.25x to 10x | 1x to 10x |
| Wheel step | ×1.25 | ×1.1, finer |
| Transition | Smooth by default | Instant |
| Settings page | Yes | None |

Both can be installed at once: they use different keys.

## Differences from WI Zoom

- **10x maximum instead of 50x** is Horizon's cap on a mod's zoom.
- Classic Zoom shares no code with WI Zoom and is not affiliated with
  Wurst-Imperium.

## Installing

1. In the Horizon launcher: **Mods**, find **Classic Zoom**, **Install**.
2. **Settings → Game → Native mods (experimental) → Build.** The launcher
   downloads its own Rust and builds the game with your native mods.
3. Play. Classic Zoom shows in Options > Mods, where its key can be
   rebound. A key you set in 1.0.0 (`key.classic_zoom.zoom` in
   `horizon-mods.txt`) carries over.

## Verifying a download

Every release file is signed with [minisign](https://jedisct1.github.io/minisign/).
The public key is in [`minisign.pub`](minisign.pub):

```
RWTOxMcIG6MtC0QQnhWEMC+nLKJ6+u4trV/rF+4juSRuow8W4b5P+CPS
```

Download the `.hnmod` and its `.minisig` from the release, then:

```sh
minisign -Vm classic_zoom-2.0.0.hnmod -P RWTOxMcIG6MtC0QQnhWEMC+nLKJ6+u4trV/rF+4juSRuow8W4b5P+CPS
```

## What a native mod can do

Native mods are not sandboxed: they are compiled into the game and run with
your account's permissions, so read the source before you build it. Classic
Zoom is small on purpose. It is one [horizon-mixins](https://github.com/horizon-rust/horizon-mixins)
bundle in [`mixins/classic_zoom/`](mixins/classic_zoom) that only uses
Horizon's native hook points:

| Hook | What Classic Zoom does there |
|---|---|
| `native_key` | Notes when the zoom key goes down or up |
| `native_wheel` | Takes the wheel while the key is held |
| `native_zoom` | Sets the zoom factor and slower turning |
| `native_mods` | Lists itself and its key in Options > Mods |

No files, network or other game state are touched.

## Compatibility

- Horizon for Minecraft: Java Edition 26.3 with native hook points v1 or
  later. [`compatibility.json`](compatibility.json) names the Horizon and
  horizon-mixins commits it was tested on.
- Client side only. Works in single player and on servers, but check a
  server's rules first: some forbid zoom mods.

## Building

The zoom logic and its tests are a plain Cargo library:

```sh
cargo test
python3 tools/native.py package .    # target/classic_zoom-<version>.hnmod
python3 tools/native.py check .      # apply on the tested Horizon and cargo check the game
python3 tools/native.py proof . --resources /path/to/.local/horizon-client/26.3
```

`tools/native.py` is Horizon's own native-mod tool, vendored from
[horizon-mods](https://github.com/horizon-rust/horizon-mods/tree/main/native/tools).
`check` and `proof` download Horizon's source at the pinned commit and build
it; `proof` then drives the game with `horizon-ctl` on temporary data
(resources prepared from your own Minecraft 26.3 with `horizon-prepare`).

---

## License

GPL-3.0-or-later - see [LICENSE](LICENSE).

The mixin bundle and proof follow Horizon's official native Zoom, and
`tools/` is vendored from horizon-mods, both under the MIT License - see
[NOTICE](NOTICE).
