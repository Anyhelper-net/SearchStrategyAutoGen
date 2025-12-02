"""
@describe:
@fileName: http.py
@time    : 2025/9/19 14:12
@author  : duke
"""


class HTTPException(RuntimeError):
    def __init__(self, resp):
        super().__init__(f'code: {resp.status_code}, reason: {resp.reason}, text: {resp.text}')
        self.resp = resp


class HTTPRetryException(HTTPException):
    def __init__(self, resp):
        super().__init__(resp)


class AccessForbiddenException(HTTPException):
    def __init__(self, resp):
        super().__init__(resp)
