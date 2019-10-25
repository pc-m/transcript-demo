# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import socket
import logging
import requests

from . import ARI_URL, ARI_USERNAME, ARI_PASSWORD, APPLICATION
from .transcription import Transcriber, MULAW

logging.basicConfig(level=logging.DEBUG)

LISTEN_ADDRESS = '127.0.0.1'
LISTEN_PORT = 12222


def serve(transcriber):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_ADDRESS, LISTEN_PORT))
    while True:
        data, _ = sock.recvfrom(4096)
        payload = data[12:]
        transcriber.push(payload)


def create_external_media_channel():
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
    return response.json()['channel']['id']


def destroy_external_media_channel(channel_id):
    url = '/'.join([ARI_URL, 'ari', 'channels', channel_id])
    requests.delete(url, auth=(ARI_USERNAME, ARI_PASSWORD))


def main():
    transcriber = Transcriber(language='en-US', codec=MULAW, sample_rate=8000)
    transcriber.start()

    external_media_channel_id = create_external_media_channel()

    try:
        serve(transcriber)
    except KeyboardInterrupt:
        pass
    finally:
        destroy_external_media_channel(external_media_channel_id)
        transcriber.stop()
