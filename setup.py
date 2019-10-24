# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import find_packages
from setuptools import setup

setup(
    name='transcript_demo',
    version='1.0',
    description='Get a transcript of a call in Asterisk',
    author='Wazo Authors',
    author_email='dev@wazo.community',
    url='http://wazo.community',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'call-transcript-ari-stasis = transcript_demo.ari_stasis:main',
            'call-transcript-ari-server = transcript_demo.ari_server:main',
            'call-transcript-wazo = transcript_demo.wazo:main',
        ],
    },
)
