"""
@describe:
@fileName: method.py
@time    : 2025/11/27 上午11:50
@author  : duke
"""
import random
import time
from src.config.http import GLOBAL_REQ_TIME_GAP_RANGE
import json
from io import BytesIO
import requests
from src.exceptions import InvalidRespJsonException
from src.config.http import GLOBAL_REQ_TIME_GAP_RANGE
from datetime import datetime


def random_sleep(_range=GLOBAL_REQ_TIME_GAP_RANGE):
    time.sleep(random.uniform(*_range))


def decode_resp_json(resp):
    data = resp.text
    try:
        return json.loads(data)
    except:
        raise InvalidRespJsonException(data)



class Logger:
    def __init__(self, on_active=None):
        self.msg = ''
        if not on_active:
            on_active = lambda x: print(x)

        self.on_active = on_active

    def write(self, msg, active=False):
        self.msg += f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] '
        self.msg += msg
        if active:
            self.active()

    def write_line(self, msg, active=False):
        self.write(msg + '\n', active=active)

    def active(self):
        self.on_active(self.msg)
        self.msg = ''


def stream_download(url):
    try:
        resp = requests.get(url, stream=True, headers={
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        })
        resp.raise_for_status()
        f = BytesIO()
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

        f.seek(0)
        return f

    except requests.exceptions.RequestException as e:
        return None
