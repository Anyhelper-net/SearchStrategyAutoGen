from src.config.lp import LP_RANDOM_SLEEP_RANGE
from src.io.zl import ZlProxy
from src.model.zl_strategy import zhilian_search_conditon
from src.utils.method import random_sleep
from src.utils.logger import logger

zl_service_logger = logger.getChild('zl_service')

class ZlService:
    class ZlServiceException(RuntimeError):
        def __init__(self, resp):
            super().__init__(resp.text)
            self.resp = resp
    def __init__(self, cookies):
        try:
            self.proxy = ZlProxy(cookies)
        except ZlProxy.ZlIOException as e:
            raise ZlProxy.ZlIOException(e.resp)
    def get_resumes(self,zl_strategy:zhilian_search_conditon,cur_page = 0,retry=1):
        for _ in range(retry + 1):
            random_sleep(LP_RANDOM_SLEEP_RANGE)
            resp = self.proxy.search_resume(page_no=cur_page,**zl_strategy.to_dict())
            data = resp.json()
            try:
                return data
            except Exception:
                raise ZlService.ZlServiceException(resp)


