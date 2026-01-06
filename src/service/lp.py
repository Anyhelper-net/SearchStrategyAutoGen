"""
@describe:
@fileName: lp.py
@time    : 2025/12/11 下午1:32
@author  : duke
"""

from src.io.lp import LpUserProxy
from src.utils.method import random_sleep
from src.utils.logger import logger

lp_service_logger = logger.getChild('lp_service')


class LpService:
    class LpServiceException(RuntimeError):
        def __init__(self, resp):
            super().__init__(resp.text)
            self.resp = resp

    class LpHumanRobotVerification(LpServiceException):
        pass

    def __init__(self, cookies):
        try:
            self.proxy = LpUserProxy(cookies)
        except LpUserProxy.LpIOException as e:
            raise LpService.LpServiceException(e.resp)

    def get_resume_count(self, inner_payload, retry=1) -> int:
        for _ in range(retry + 1):
            random_sleep()
            resp = self.proxy.search_resumes(inner_payload)
            data = resp.json()
            try:
                return data['data']['totalCnt']
            except KeyError:
                if resp.text == '{"flag":0}':
                    raise LpService.LpHumanRobotVerification(resp)
                else:
                    raise LpService.LpServiceException(resp)
