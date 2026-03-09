"""
@describe:
@fileName: maimai_io.py
@time    : 2025/9/19 13:59
@author  : duke
"""
import time
from typing import Iterable
import requests
from src.config.maimai import *
from copy import deepcopy
from src.utils.decorator import http_retry
from src.config.http import *


class MMProxy:
    def __init__(self, cookies):
        self.cookies = cookies
        cookies_dict = MMProxy.cookies2dict(cookies)
        self.cookies_dict = cookies_dict

        # self.headers: talents
        # self.headers2: im (cors, referer edited)
        self.headers = deepcopy(TEMPLATE_MM_HEADERS)
        self.headers['X-Csrf-Token'] = cookies_dict['csrftoken']
        self.headers2 = deepcopy(self.headers)
        self.headers['Sec-Fetch-Mode'] = 'cors'
        self.headers['Referer'] = 'https://maimai.cn/chat?fr=ent&in_iframe=1&scene=talent_bank'

        self.uid = cookies_dict['u']
        self._csrf = None

    @staticmethod
    def get_valid_cookies(cookies: list[dict], domain: str, is_time_strict=False) -> filter:
        cookies = filter(lambda x: x['domain'].endswith(domain), cookies)
        if is_time_strict:
            timestamp = time.time()
            cookies = list(cookies)
            cookies = filter(lambda x: float(x['expirationDate']) > timestamp, cookies)
        return cookies

    @staticmethod
    def cookies2dict(cookies: Iterable[dict]) -> dict:
        """
        :param cookies: iterable obj of cookies containing key, value, and other information, e.g. expirationDate, Domain.
        :return: key-value dict of cookies.
        """
        cookies_dict = {}
        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']
        return cookies_dict

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def search_candidate(self, payload: str):
        """
        :param payload: stringfied search condition dict
        :return: response of requests
        """
        headers = deepcopy(self.headers)
        headers['Content-Type'] = 'text/plain;charset=UTF-8'
        return requests.post(API_MM_SEARCH_BASIC, headers=headers, cookies=self.cookies_dict, data=payload,
                             timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def send(self, uid, greet_text, jid=0, greet_name=''):
        """
        greet and send job
        """
        params = deepcopy(TEMPLATE_PARAMS_MM_SEND)
        params['u'] = self.uid
        params['u2'] = uid
        params['greet_name'] = greet_name
        params['greet_text'] = greet_text
        params['jid'] = jid

        return requests.get(API_MM_SEND, headers=self.headers, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def batch_send(self, uids, greet_text, jid=0, greet_name_type=''):
        params = deepcopy(TEMPLATE_PARAMS_MM_SEND)
        params['u'] = self.uid
        params['to_uids'] = ','.join(map(str, uids))
        params['greet_name_type'] = greet_name_type
        params['greet_text'] = greet_text
        params['jid'] = jid

        return requests.get(API_MM_BATCH_SEND, headers=self.headers, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def get_job_list(self):
        params = deepcopy(TEMPLATE_PARAMS_MM_JOB_LIST)
        params['uid'] = self.uid

        return requests.get(API_MM_JOB_LIST, headers=self.headers, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def get_user_info(self):
        params = deepcopy(TEMPLATE_PARAMS_MM_CURRENT)
        ts = round(time.time(), 3)
        ts = str(ts).replace('.', '')
        params['t'] = f't_{ts}'
        return requests.get(API_MM_CURRENT, headers=self.headers, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def chat(self):
        return requests.get(API_MM_CHAT, headers=self.headers, cookies=self.cookies_dict, timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def get_msg_by_ldtime(self, count, only_unread=False):
        params = deepcopy(TEMPLATE_PARAMS_MM_GET_MSG_LDTIME)
        params['u'] = self.uid
        params['_csrf'] = self._csrf
        params['_csrf_token'] = self.cookies_dict['csrftoken']
        params['only_unread'] = 1 if only_unread else 0
        params['count'] = count

        return requests.get(API_MM_GET_MSG_LDTIME, headers=self.headers2, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def get_resume(self, uid, trackable_token):
        params = deepcopy(TEMPLATE_PARAMS_MM_GET_RESUME)
        params['to_uid'] = uid
        params['trackable_token'] = trackable_token

        return requests.get(API_MM_GET_RESUME, headers=self.headers, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def get_contact(self, uid):
        return requests.get(API_MM_CONTACT.format(uid), headers=self.headers, cookies=self.cookies_dict,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def mobile_req(self, uid, message_id, ejid):
        params = deepcopy(TEMPLATE_PARAMS_MM_MOBILE_REQ)
        params['u'] = self.uid
        params['_csrf'] = self._csrf
        params['_csrf_token'] = self.cookies_dict['csrftoken']
        params['u2'] = uid
        params['mid'] = message_id
        params['ejid'] = ejid

        return requests.get(API_MM_MOBILE_REQ, headers=self.headers2, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def vx_req(self, uid, message_id, ejid):
        params = deepcopy(TEMPLATE_PARAMS_MM_MOBILE_REQ)
        params['u'] = self.uid
        params['_csrf'] = self._csrf
        params['_csrf_token'] = self.cookies_dict['csrftoken']
        params['u2'] = uid
        params['mid'] = message_id
        params['ejid'] = ejid

        return requests.get(API_MM_VX_REQ, headers=self.headers2, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def get_dialog(self, mid, count=20, before_did=0):
        params = deepcopy(TEMPLATE_PARAMS_MM_GET_DIALOG)
        params['u'] = self.uid
        params['_csrf'] = self._csrf
        params['_csrf_token'] = self.cookies_dict['csrftoken']
        params['mid'] = mid
        params['count'] = count
        params['before_did'] = before_did

        return requests.get(API_MM_GET_DIALOG, headers=self.headers2, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def add_dialog(self, mid, msg):
        params = deepcopy(TEMPLATE_PARAMS_MM_ADD_DIALOG)
        params['u'] = self.uid
        params['_csrf'] = self._csrf
        params['_csrf_token'] = self.cookies_dict['csrftoken']

        payload = {
            'mid': mid,
            'msghash': f'im{self.uid}{round(time.time(), 3)}',
            'text': msg,
        }

        return requests.post(API_MM_ADD_DIALOG, headers=self.headers2, cookies=self.cookies_dict, params=params,
                             data=payload, timeout=HTTP_TIME_OUT_MM)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def enter_msg(self, mid):
        params = deepcopy(TEMPLATE_PARAMS_MM_ENTER_MSG)
        params['u'] = self.uid
        params['_csrf'] = self._csrf
        params['_csrf_token'] = self.cookies_dict['csrftoken']
        params['mid'] = mid

        return requests.get(API_MM_ENTER_MSG, headers=self.headers2, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    # @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    # def pull_msg(self, mid):
    #     params = deepcopy(TEMPLATE_PARAMS_MM_PULL_MSG)
    #     params['u'] = self.uid
    #     params['_csrf'] = self._csrf
    #     params['_csrf_token'] = self.cookies_dict['csrftoken']
    #     params['mid'] = mid
    #     params['mtime'] = int(time.time())
    #
    #     return requests.get(API_MM_PULL_MSG, headers=self.headers2, cookies=self.cookies_dict, params=params)

    @http_retry(HTTP_RETRY_TIMES, HTTP_RETRY_GAP)
    def clear_badge(self, mid, last_did):
        params = deepcopy(TEMPLATE_PARAMS_MM_CLEAR_BADGE)
        params['u'] = self.uid
        params['_csrf'] = self._csrf
        params['_csrf_token'] = self.cookies_dict['csrftoken']
        params['mid'] = mid
        params['last_did'] = last_did

        return requests.get(API_MM_CLEAR_BADGE, headers=self.headers2, cookies=self.cookies_dict, params=params,
                            timeout=HTTP_TIME_OUT_MM)

    def export_cookies(self):
        for cookie in self.cookies:
            name = cookie['name']
            if name in self.cookies_dict:
                cookie['value'] = self.cookies_dict[name]
            try:
                del self.cookies['expirationDate']
            except:
                pass
        return self.cookies
