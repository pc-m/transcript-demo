# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import websocket
import sys

from functools import partial


def on_message(out, ws, message):
    out.write(message)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def main():
    websocket.enableTrace(True)
    with open('out.wav', 'wb') as out:
        ws = websocket.WebSocketApp(
            "ws://localhost:5039/ws",
            on_message=partial(on_message, out),
            on_error=on_error,
            on_close=on_close,
            subprotocols=["stream-channel"],
            header=['Channel-ID: ' + sys.argv[1]],
        )
        ws.run_forever()
