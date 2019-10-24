# Asterisk Live transcript demo

This is a simple demo showing how to use the Asterisk ARI externalMedia resource and Google Speech API to get
a transcript of a call.

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

```sh
cd /tmp/translation && python -m SimpleHTTPServer
```

Then visit the dispayed address in your browser


## How it works

1. When a call enters the stasis application it will be added to the bridge
2. When the server starts listening on the configured port and create the external media channel
3. When RTP is received the payload is sent to Google Speech to text API and an HTML file is generated


## Usage Wazo module demo

1. A calls B
2. exucute `call-transcript-wazo <channel uniqueid>`
