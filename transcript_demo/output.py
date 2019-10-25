# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os

_TPL = '''\
<head>
    <meta http-equiv="refresh" content="1">
</head>
<body>
{}
</body>
'''
_OUTPUT_DIRNAME = '/tmp/translation'
_OUTPUT_FILENAME = os.path.join(_OUTPUT_DIRNAME, 'index.html')


class Output:

    def __init__(self):
        try:
            os.mkdir(_OUTPUT_DIRNAME)
        except FileExistsError:
            pass

        self.write('Waiting for the transcription to start...')

    def write(self, content):
        generated_html = _TPL.format(content.replace('\n', '</p>'))
        with open(_OUTPUT_FILENAME, 'w') as f:
            f.write(generated_html)
