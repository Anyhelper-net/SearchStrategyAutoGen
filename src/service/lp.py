"""
@describe:
@fileName: lp.py
@time    : 2025/12/11 下午1:32
@author  : duke
"""

from src.io.lp import LpUserProxy


class LpService:
    def __init__(self, cookies):
        self.proxy = LpUserProxy(cookies)

    def get_resume_count(self, inner_payload) -> int:
        resp = self.proxy.search_resumes(inner_payload)
        data = resp.json()
        return data['data']['totalCnt']
