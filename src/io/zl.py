import requests
from src.config.http import *
from src.config.zl import *
from src.utils import http_retry


class ZlProxy:
    class ZlIOException(RuntimeError):
        def __init__(self, resp):
            super().__init__(resp.text)
            self.resp = resp

    def __init__(self, cookies):
        self.cookies = cookies
        self.cookies_name_val_dict = {c['name']: c['value'] for c in cookies}
        self.client_id = None

    @http_retry(HTTP_RETRY_TIMES,HTTP_RETRY_GAP)
    def search_resume(self, page_no, page_size = 20, **kwargs):
        url = SEARCH_RESUME
        payload = {
            "filteringChatted": True,
            "filteringRead": False,
            "filteringDownloaded": False,
            "sort": {"type": "COMPLEX", "version": 17},
            "pageNo": page_no,
            "pageSize": page_size,
            "filteringOtherChattedType": "DONT_FILTER",
            "matchLatestWorkExperience": False,
            "searchExperimentalGroup": "EXPERIMENT",
            "frontExperiment": True,
            "firstPageCacheable": False,
            "freeMaskLimit": False,
            "experiment": ""
        }
        payload.update(kwargs)
        response = requests.post(url, cookies=self.cookies_name_val_dict, json=payload)
        return response

