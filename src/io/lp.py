"""
@describe:
@fileName: lp.py
@time    : 2025/11/28 下午12:54
@author  : duke
"""
import json
import time

import requests
import re
import uuid

from selenium.webdriver.chrome.options import Options

from src.config.lp import TEMP_LP_HEADERS, TEMP_LP_HEADERS_HOME, PATTERN_LP_HOME_JS, PATTERN_LP_CLIENT_ID, \
    API_LP_SEARCH_RESUMES, API_LP_HOME
from copy import deepcopy
from src.utils.decorator import http_retry
from src.config.http import HTTP_TIME_OUT_LP, HTTP_RETRY_GAP, HTTP_RETRY_TIMES
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import InvalidSessionIdException

from src.config.path import CHROME_DRIVER_PATH


class LpUserProxy:
    class LpIOException(RuntimeError):
        def __init__(self, resp):
            super().__init__(resp.text)
            self.resp = resp

    def __init__(self, cookies):
        self.cookies = cookies
        self.cookies_name_val_dict = {c['name']: c['value'] for c in cookies}
        self.client_id = None
        self._get_client_id()

    def _get_headers(self):
        headers = deepcopy(TEMP_LP_HEADERS)
        headers['X-XSRF-TOKEN'] = self.cookies_name_val_dict['XSRF-TOKEN']
        headers['X-Fscp-Trace-Id'] = str(uuid.uuid4())
        headers['X-Fscp-Std-Info'] = f'{{"client_id": "{self.client_id}"}}'
        return headers

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def _get_client_id(self):
        resp = self._get_homepage()
        match = re.search(PATTERN_LP_HOME_JS, resp.text)
        if not match:
            raise LpUserProxy.LpIOException(resp)
        url = 'https:' + match.group()
        resp = requests.get(url, timeout=HTTP_TIME_OUT_LP)
        match = re.search(PATTERN_LP_CLIENT_ID, resp.text)
        self.client_id = match.group(1)
        return resp

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def _get_homepage(self):
        return requests.get(API_LP_HOME, headers=TEMP_LP_HEADERS_HOME, cookies=self.cookies_name_val_dict,
                            timeout=HTTP_TIME_OUT_LP)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def search_resumes(self, searchParamsInputVo, curPage=0):
        searchParamsInputVo['curPage'] = curPage
        payload = {
            'searchParamsInputVo': searchParamsInputVo,
            'logForm': {"ckId": str(uuid.uuid4()), "skId": '', "fkId": '', "searchScene": "refresh"},
            'version': 'V5',
        }
        payload = [f'{key}={json.dumps(val, ensure_ascii=False, separators=(',', ':'))}' for key, val in
                   payload.items()]
        payload = '&'.join(payload)

        return requests.post(API_LP_SEARCH_RESUMES, headers=self._get_headers(), cookies=self.cookies_name_val_dict,
                             data=payload, timeout=HTTP_TIME_OUT_LP)

    def human_robot_verification(self):
        chrome_options = Options()
        # chrome_options.add_argument('--disable-web-security')
        # chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_service = Service(executable_path=CHROME_DRIVER_PATH)
        wd = webdriver.Chrome(service=chrome_service, options=chrome_options)
        try:
            wd.get('https://h.liepin.com/')
            for cookie in self.cookies:
                wd.add_cookie(cookie)
            # wd.refresh()
            wd.get('https://h.liepin.com/')
            try:
                while wd.current_window_handle:
                    time.sleep(1)
            except InvalidSessionIdException:
                return
        finally:
            wd.quit()
