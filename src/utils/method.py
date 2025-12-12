"""
@describe:
@fileName: method.py
@time    : 2025/11/27 上午11:50
@author  : duke
"""
import random
import time

from src.config.http import GLOBAL_REQ_TIME_GAP_RANGE


def random_sleep(_range=GLOBAL_REQ_TIME_GAP_RANGE):
    time.sleep(random.uniform(*_range))
