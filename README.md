Simulator for a simple synthesizer that I'd like to build one day, or maybe not.

Sort of inspired by Hammond organ, but actually closer to something
much newer and much cheaper.

Two octaves, four mixing busbars.
Based on a top octave generator (implemented on an MCU, because it would be easier),
4bit counters (with one bit unused) and Sallen-Key filters.

The simulator runs in python and has a web interface, can be played
using a keyboard.

Start by installing stuff from `requirements.txt`, then running `server.py`

85% Clauded, I don't understand the filter implementation at all, I didn't even look at index.html.
