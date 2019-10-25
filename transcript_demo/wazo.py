# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import websocket
import sys

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from queue import Queue
from threading import Thread
from functools import partial
from .output import Output

GOOGLE_SPEECH_CREDS_FILENAME = '/root/google_speech_creds.json'
SPEECH_CLIENT = speech.SpeechClient.from_service_account_file(
    filename=GOOGLE_SPEECH_CREDS_FILENAME,
)
STREAMING_CONFIG = types.StreamingRecognitionConfig(
    config=types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='en-US',
    ),
)

logging.basicConfig(level=logging.DEBUG)

DONE = object()

output = None


def on_message(queue, ws, message):
    queue.put_nowait(message)


def on_error(ws, error):
    logging.debug(error)


def on_close(ws):
    logging.debug('closing')


def transcribe(queue):
    step = 64 * 1024
    transcribe_threshold = step
    buffer = b''
    while True:
        data = queue.get()
        try:
            if data == DONE:
                return
            buffer += data
            written = len(buffer)
            if written >= transcribe_threshold:
                transcribed = do_transcription(buffer)
                transcribe_threshold = written + step
                output.write(transcribed)
        finally:
            queue.task_done()


def do_transcription(data):
    logging.debug('Sending %s to the speech API', len(data))
    request = types.StreamingRecognizeRequest(audio_content=data)
    responses = list(SPEECH_CLIENT.streaming_recognize(STREAMING_CONFIG, [request]))
    logging.debug('responses: %s', responses)

    output = '\n'
    for response in responses:
        results = list(response.results)
        logging.debug("results: %d" % len(results))
        for result in results:
            if not result.is_final:
                continue
            output += '{}\n'.format(result.alternatives[0].transcript)

    logging.debug('final output: %s', output)
    return output


def main():
    global output

    output = Output()
    queue = Queue()
    transcriber_thread = Thread(target=transcribe, args=(queue,))
    transcriber_thread.start()

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "ws://localhost:5039/ws",
        on_message=partial(on_message, queue),
        on_error=on_error,
        on_close=on_close,
        subprotocols=["stream-channel"],
        header=['Channel-ID: ' + sys.argv[1]],
    )

    try:
        ws.run_forever()
    finally:
        queue.put_nowait(DONE)
        queue.join()
        logging.debug('joining transcriber_thread')
        transcriber_thread.join()
