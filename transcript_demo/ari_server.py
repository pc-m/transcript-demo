# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import aiohttp
import logging
import uuid
import sys
import os
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from aiohttp_requests import requests
from . import ARI_URL, ARI_USERNAME, ARI_PASSWORD, APPLICATION

logging.basicConfig(level=logging.DEBUG)

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12222
EXTERNAL_MEDIA_URL = '/'.join([ARI_URL, 'ari', 'channels', 'externalMedia'])
CHANNEL_ID = str(uuid.uuid4())
GOOGLE_SPEECH_CREDS_FILENAME = '/root/google_speech_creds.json'
TPL = '''\
<head>
    <meta http-equiv="refresh" content="1">
</head>
<body>
{}
</body>
'''
OUTPUT_DIRNAME = '/tmp/translation'
OUTPUT_FILENAME = os.path.join(OUTPUT_DIRNAME, 'index.html')
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


class ExternalMediaServer:
    def __init__(self, queue):
        self._queue = queue

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self._queue.put_nowait(data[12:])


async def fetch_transcription(buf):
    request = types.StreamingRecognizeRequest(audio_content=buf)
    responses = list(SPEECH_CLIENT.streaming_recognize(STREAMING_CONFIG, [request]))
    logging.debug('%s', responses)

    output = '\n'
    for response in responses:
        results = list(response.results)
        logging.debug("results: %d" % len(results))
        for result in results:
            if not result.is_final:
                continue
            output += '{}\n'.format(result.alternatives[0].transcript)

    logging.debug('%s', output)
    return output


async def write_transcription(transcribed):
    logging.debug('transcribed: %r', transcribed)
    with open(OUTPUT_FILENAME, 'w') as f:
        f.write(TPL.format(transcribed.replace('\n', '</p>')))


async def transcribe(queue):
    buf = b''
    step = 64 * 1024
    threshold = step
    while True:
        data = await queue.get()
        buf += data
        if len(buf) >= threshold:
            logging.debug('transcribing...')
            transcribed = await fetch_transcription(buf)
            threshold += step
            await write_transcription(transcribed)


async def create_external_media():
    await asyncio.sleep(1)

    logging.debug('POSTing %s', EXTERNAL_MEDIA_URL)
    response = await requests.post(
        EXTERNAL_MEDIA_URL,
        auth=aiohttp.BasicAuth(ARI_USERNAME, ARI_PASSWORD),
        params={
            'channelId': CHANNEL_ID,
            'app': APPLICATION,
            'external_host': '{}%3A{}'.format(SERVER_HOST, SERVER_PORT),
            'format': 'ulaw',
        },
    )
    result = await response.text()
    logging.debug('result: %s', result)


async def destroy_external_media():
    await asyncio.sleep(1)

    logging.debug('Destroying %s', EXTERNAL_MEDIA_URL)
    response = await requests.post(
        EXTERNAL_MEDIA_URL + '/destroy',
        auth=aiohttp.BasicAuth(ARI_USERNAME, ARI_PASSWORD),
        params={
            'channelId': CHANNEL_ID,
        },
    )
    result = await response.text()
    logging.debug('result: %s', result)


async def start(host, port):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ExternalMediaServer(queue),
        local_addr=(host, port),
    )

    logging.debug('launching task')
    tasks = [
        asyncio.create_task(create_external_media()),
        asyncio.create_task(transcribe(queue)),
    ]

    asyncio.gather(*tasks)

    await asyncio.sleep(3600)


def main():
    logging.debug('Starting %s', sys.argv[0])
    try:
        os.mkdir(OUTPUT_DIRNAME)
    except FileExistsError:
        pass

    with open(OUTPUT_FILENAME, 'w') as f:
        f.write(TPL.format('Waiting for the transcription to start...'))
    asyncio.run(start(SERVER_HOST, SERVER_PORT))
    logging.debug('bye')
