# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import socket
import logging
import sys
import requests

from queue import Queue
from threading import Thread

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from . import ARI_URL, ARI_USERNAME, ARI_PASSWORD, APPLICATION
from .output import Output

logging.basicConfig(level=logging.DEBUG)

LISTEN_ADDRESS = '127.0.0.1'
LISTEN_PORT = 12222

GOOGLE_SPEECH_CREDS_FILENAME = '/root/google_speech_creds.json'
SPEECH_CLIENT = speech.SpeechClient.from_service_account_file(
    filename=GOOGLE_SPEECH_CREDS_FILENAME,
)
STREAMING_CONFIG = types.StreamingRecognitionConfig(
    config=types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,
        language_code='en-US',
    ),
)

output = None
DONE = object()


def serve(queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_ADDRESS, LISTEN_PORT))
    while True:
        data, _ = sock.recvfrom(4096)
        payload = data[12:]
        queue.put_nowait(payload)


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

    logging.debug('Starting %s', sys.argv[0])
    queue = Queue()
    output = Output()

    transcriber_thread = Thread(target=transcribe, args=(queue,))
    transcriber_thread.start()

    url = '/'.join([ARI_URL, 'ari', 'channels', 'externalMedia'])
    response = requests.post(
        url,
        auth=(ARI_USERNAME, ARI_PASSWORD),
        data={
            'app': APPLICATION,
            'external_host': '{}:{}'.format('127.0.0.1', LISTEN_PORT),
            'format': 'ulaw',
        }
    )

    try:
        serve(queue)
    except KeyboardInterrupt:
        pass
    finally:
        url = '/'.join([ARI_URL, 'ari', 'channels', response.json()['channel']['id']])
        requests.delete(url, auth=(ARI_USERNAME, ARI_PASSWORD))

        queue.put_nowait(DONE)
        transcriber_thread.join()
