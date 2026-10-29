<div align="center">
  <img src=".github/icon.png" width="128" height="128" alt="Classic Zoom icon">

  # Classic Zoom

  **Hold V, zoom 3x, scroll for more. For Horizon.**

  [![Latest release](https://img.shields.io/github/v/release/SU4G3/classic-zoom?label=release&color=2e7d32)](https://github.com/SU4G3/classic-zoom/releases/latest)
  [![Build](https://img.shields.io/github/actions/workflow/status/SU4G3/classic-zoom/build.yml?branch=main&label=build)](https://github.com/SU4G3/classic-zoom/actions/workflows/build.yml)
  [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Minecraft](https://img.shields.io/badge/minecraft-26.3-5865F2)](#compatibility)
  [![Horizon mod API](https://img.shields.io/badge/horizon%20mod%20api-0.1-F0795A)](https://playhorizon.dev/docs/mods)
</div>

<br>

A zoom mod for [Horizon](https://github.com/horizon-rust/horizon), the Rust
rewrite of Minecraft: Java Edition 26.3. It brings the feel of
[WI Zoom](https://github.com/Wurst-Imperium/WI-Zoom) to Horizon: one key,
an instant zoom, the mouse wheel for more, and nothing to configure.

> **[Download the latest release →](https://github.com/SU4G3/classic-zoom/releases/latest)**

<details>
<summary><b>Table of contents</b></summary>

- [Controls](#controls)
- [How it differs from Horizon's own Zoom](#how-it-differs-from-horizons-own-zoom)
- [Differences from WI Zoom](#differences-from-wi-zoom)
- [Installing](#installing)
- [Permissions](#permissions)
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

- **10x maximum instead of 50x.** Horizon's `render.set-zoom` caps the zoom
  at 10x; a mod can't go past it.
- Classic Zoom is written from scratch for Horizon's sandboxed mod API. It
  shares no code with WI Zoom and is not affiliated with Wurst-Imperium.

## Installing

1. Download `classic_zoom-<version>.hmod` from
   [Releases](https://github.com/SU4G3/classic-zoom/releases/latest).
2. Put it in `horizon-mods/` next to `options.txt` in your Horizon game
   folder.
3. In game, open Options > Mods and turn **Classic Zoom** on. Mods start
   off.

## Permissions

Horizon mods run in a WebAssembly sandbox with no file, network or process
access. Classic Zoom asks only for:

- `render`: to set the camera zoom.
- `input`: to register the V key and to read the mouse wheel while V is
  held.

## Compatibility

- Horizon built for Minecraft: Java Edition 26.3, mod API 0.1.
- Client side only. Works in single player and on servers, but check a
  server's rules first: some forbid zoom mods.

## Building

Needs Rust stable with the `wasm32-unknown-unknown` target and
`cargo-horizon-mod`:

```sh
rustup target add wasm32-unknown-unknown
cargo install --locked --git https://github.com/horizon-rust/horizon \
  --rev 8f0c178957cce584b9b2027823e01651006dab6d cargo-horizon-mod
cargo horizon-mod build
cargo horizon-mod check target/horizon-mod/classic_zoom.hmod
```

The mod lands in `target/horizon-mod/classic_zoom.hmod`. For live editing,
`cargo horizon-mod run` starts the game with the mod and reloads it after
every build.

---

## License

MIT - see [LICENSE](LICENSE).
