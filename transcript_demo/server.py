# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import tempfile
import asyncio
import aiohttp
import logging
import uuid
import sys
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from aiohttp_requests import requests

logging.basicConfig(level=logging.DEBUG)

from . import ARI_URL, ARI_USERNAME, ARI_PASSWORD, APPLICATION

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12222
EXTERNAL_MEDIA_URL = '/'.join([ARI_URL, 'ari', 'channels', 'externalMedia'])
CHANNEL_ID = str(uuid.uuid4())
GOOGLE_SPEECH_CREDS_FILENAME = '/root/google_speech_creds.json'


class ExternalMediaServer:
    _speech_client = speech.SpeechClient.from_service_account_file(
        filename=GOOGLE_SPEECH_CREDS_FILENAME,
    )
    _streaming_config = types.StreamingRecognitionConfig(
        config=types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.MULAW,
            sample_rate_hertz=8000,
            language_code='en-US',
        ),
    )

    def connection_made(self, transport):
        self.loop = asyncio.get_running_loop()
        self.transport = transport
        self._buffer = b''
        self._file = tempfile.NamedTemporaryFile()
        logging.debug('%s', self._file.name)

    def connection_lost(self, exc):
        self._file.close()

    def datagram_received(self, data, addr):
        self._buffer += data[12:]
        if len(self._buffer) > 16 * 1024:
            self._write()
            self._flush()

    def _write(self):
        self._file.write(self._buffer)
        self._buffer = b''

    def _flush(self):
        self._file.seek(0)
        chunk = self._file.read()

        logging.debug(
            "_send_buffer: chunk len: %s",
            len(chunk) if chunk is not None else None,
        )
        if not chunk:
            return

        request = types.StreamingRecognizeRequest(audio_content=chunk)

        responses = list(
            self._speech_client.streaming_recognize(self._streaming_config, [request]),
        )
        logging.debug('%s', responses)

        output = '\n'
        for response in responses:
            results = list(response.results)
            logging.debug("results: %d" % len(results))
            for result in results:
                if not result.is_final:
                    continue
                output += '{}\n'.format(result.alternatives[0].transcript)

        logging.info('%s', output)


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

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ExternalMediaServer(),
        local_addr=(host, port),
    )

    logging.debug('launching task')
    asyncio.create_task(create_external_media())

    await asyncio.sleep(3600)


def main():
    logging.debug('Starting %s', sys.argv[0])
    asyncio.run(start(SERVER_HOST, SERVER_PORT))
    logging.debug('bye')
