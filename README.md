# Asterisk Live transcript demo

This repo contains two simple demos showing how to use the Asterisk ARI
externalMedia resource and another one using res_ari_stream to get a live
transcription of a call.

The ARI demo creates an application that starts a bridge, the voice in that
bridge will be translated.

The res_ari_stream demo can listen to an arbitrary channel

## Installing

1. clone this repository
2. python setup.py install
3. configure Asterisk such that calls enter the `stt` stasis application `same = n,Stasis(stt)`
4. create credentials for the Google Speech to Text API
5. create a ARI user with username/password `demo/2b34c141-0ca9-44a7-95ca-570302f069c0`

### res_ari_stream

See the git repo README for installation instructions https://github.com/sboily/wazo-hackathon-asterisk-stream-module


## Usage ARI demo

This demo is made of 3 processes

1. The stasis application which receives the incoming call and puts everyone in a bridge.
2. The server which create the external media channel, receives the RTP from Asterisk sends it to Google Speech API and write the result to an html file.
3. An HTTP server to serve the generated transcript

### Starting the stasis application

```sh
call-transcript-ari-stasis
```

### Starting the server

```sh
call-transcript-ari-server
```

### Displaying the result

```sh
cd /tmp/translation && python -m SimpleHTTPServer
```

Then visit the dispayed address in your browser


## How it works

1. When a call enters the stasis application it will be added to the bridge
2. When the server starts listening on the configured port and create the external media channel
3. When RTP is received the payload is sent to Google Speech to text API and an HTML file is generated


## Usage Wazo module demo

1. exucute `call-transcript-wazo <channel uniqueid>`
2. An HTTP server to serve the generated transcript

### Start the script with an active call

replace PJSIP/twilio with the peer you wish to listen to

```sh
call-transcript-wazo $(asterisk -rx 'core show channels concise' | grep 'PJSIP/twilio' | awk -F'!' '{ print $NF}')
```
