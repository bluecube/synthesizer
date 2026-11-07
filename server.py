#!/bin/env python
"""Web interface for the synthesizer.

Serves the page, receives key presses and mixing levels over a WebSocket
and plays the sound locally."""

import pathlib

import aiohttp
import aiohttp.web
import sounddevice

import simulator

STATIC_DIR = pathlib.Path(__file__).parent / "static"
SYNTH = aiohttp.web.AppKey("synth", simulator.Synthesizer)


async def index(request):
    return aiohttp.web.FileResponse(STATIC_DIR / "index.html")


async def websocket(request):
    synth = request.app[SYNTH]
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    await ws.send_json(
        {
            "type": "config",
            "keys": synth.key_names,
            "busbars": synth.busbar_names,
            "mixing": synth.mixing.tolist(),
        }
    )

    try:
        async for message in ws:
            if message.type != aiohttp.WSMsgType.TEXT:
                continue
            data = message.json()
            if data["type"] == "key":
                if data["down"]:
                    synth.press(data["key"])
                else:
                    synth.release(data["key"])
            elif data["type"] == "release_all":
                synth.release_all()
            elif data["type"] == "mixing":
                synth.mixing = data["values"]
    finally:
        # A closed page can't release its keys anymore
        synth.release_all()

    return ws


def main(host="127.0.0.1", port=8080):
    synth = simulator.Synthesizer(batch_size=256)
    blocks = synth.run()

    def callback(outdata, frames, time, status):
        if status:
            print(status)
        outdata[:, 0] = next(blocks)

    app = aiohttp.web.Application()
    app[SYNTH] = synth
    app.router.add_get("/", index)
    app.router.add_get("/ws", websocket)

    with sounddevice.OutputStream(
        samplerate=synth.sample_rate,
        blocksize=synth.batch_size,
        channels=1,
        dtype="float32",
        latency="low",
        callback=callback,
    ):
        aiohttp.web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
