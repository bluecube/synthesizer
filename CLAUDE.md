# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A simulator of a planned hardware synthesizer (two octaves, four Hammond-style busbars). The simulation models the intended circuit: a top octave generator (MCU) + 4-bit counter dividers producing square waves → one unity-gain Sallen-Key low pass per tone → busbars (summing amplifiers fed by key contacts) → mixing levels → output. Code should keep mirroring that hardware structure; names and comments refer to circuit parts (DC blocking capacitor, E-series resistors, etc.).

## Running

```sh
python -m venv venv && . venv/bin/activate   # a venv/ already exists in the checkout
pip install -r requirements.txt
python server.py                             # http://127.0.0.1:8080, plays audio locally via sounddevice
```

There are no tests, linter config, or build step.

## Architecture

- `simulator.py` — `Synthesizer`. Audio is produced by a chain of generators, each consuming the previous one block by block (`batch_size` samples): `_square_waves` → `_filtered_tones` → `_busbars` → `run`. Each stage yields numpy arrays shaped `(n_tones, batch_size)` until the busbar stage, which reduces to `(n_busbars, batch_size)`; `run` yields mono `(batch_size,)` samples. Filter state (`lfilter` `zi`) and oscillator phase are carried across blocks, so blocks must be continuous.
- Tone indexing: `_frequencies` holds 48 semitones C2..B5; keys are indices into `_key_indices` (12..35, i.e. C3..B4); each busbar adds an offset (`_busbar_offsets`, in semitones) to the key's tone index. The asserts in `__init__` require the frequency table to exactly cover keys × offsets — changing keys or offsets means adjusting the `range(-33, +15)` too.
- Threading: `server.py` pulls `next(blocks)` from `synth.run()` inside the sounddevice audio callback thread, while the aiohttp event loop mutates `_pressed_keys` (via `press`/`release`/`release_all`) and `mixing`. Shared state is only read once at the start of each block (pressed keys copied, mixing ramped across the block to avoid zipper noise). Keep the per-block work fast enough for real time at `batch_size=256`.
- `server.py` — aiohttp app serving `static/index.html` and a WebSocket at `/ws`. On connect the server sends `{"type": "config", keys, busbars, mixing}`; the client sends `key` (`key` index, `down` bool), `release_all`, and `mixing` (`values` list). All keys are released when a socket closes.
- `static/index.html` — single-file vanilla JS UI, built dynamically from the `config` message (key count, busbar names, initial mixing). Computer-keyboard mapping is by physical `KeyboardEvent.code` in `KEY_CODES`, starting from a C; keys beyond that list are mouse-only.
