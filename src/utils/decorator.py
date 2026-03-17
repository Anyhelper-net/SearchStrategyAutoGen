"""
@describe:
@fileName: decorator.py
@time    : 2025/9/19 14:08
@author  : duke
"""
import random
from src.exceptions import HTTPRetryException, AccessForbiddenException
import time

def http_retry(times, gap):
    def decorator(func):
        def wrapper(*args, **kwargs):
            resp = None
            delay = gap
            for i in range(times):
                try:
                    resp = func(*args, **kwargs)
                except:
                    if i + 1 < times:
                        sleep_time = delay + random.uniform(0, delay)
                        time.sleep(sleep_time)
                        delay *= 2
                        continue
                    raise
                if resp.ok or resp.status_code == 200:
                    return resp
                if resp.status_code == 403:
                    raise AccessForbiddenException(resp)
                time.sleep(gap)
            raise HTTPRetryException(resp)

        return wrapper

    return decorator
