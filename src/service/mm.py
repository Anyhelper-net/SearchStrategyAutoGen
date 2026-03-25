"""
@describe:
@fileName: user.py
@time    : 2025/9/24 20:19
@author  : duke
"""
import json
from src.io.mm import MMProxy
from src.model.mm_user import MMUser
from src.model.mm_job import MMJob
from src.model.mm_strategy import MMStrategy
from src.exceptions.maimai import *
from src.utils import decode_resp_json
from src.config.maimai import PATTERN_MM_CSRF, PATTERN_MM_CSRF_TOKEN, PATTERN_MM_MOBILE
import re


class MMService:
    def __init__(self, cookies):
        self.proxy = MMProxy(cookies)
        self.user = MMUser(self._pull_all_jod(), **self._pull_user_info())
        self.chat_init()

    def export_cookies(self):
        return self.proxy.export_cookies()

    def refresh(self):
        self.user = MMUser(self._pull_all_jod(), **self._pull_user_info())

    def _get_job_by_pid(self, pid: str):
        try:
            job = self.user.job_dict[pid]
        except KeyError:
            raise DisMatchedJobException(pid, self.user.name)
        return job

    def get_jid_by_pid(self, pid: str):
        return self._get_job_by_pid(pid).jid

    def get_ejid_by_pid(self, pid: str):
        return self._get_job_by_pid(pid).ejid

    def get_jname_by_pid(self, pid: str):
        return self._get_job_by_pid(pid).position

    def _pull_all_jod(self):
        resp = self.proxy.get_job_list()
        data = decode_resp_json(resp)
        jobs = data['jobs']
        result = {}
        for job in jobs:
            pid_group = re.search(r"\d+", job['position'])
            if not pid_group:
                continue
            pid = pid_group.group()
            result[pid] = MMJob(**job)
        return result

    def _pull_user_info(self):
        resp = self.proxy.get_user_info()
        data = decode_resp_json(resp)
        return data['data']['ucard']

    def search_candidate(self, search_condition: MMStrategy, page, size):
        payload = search_condition.get_mm_payload(page, size)
        resp = self.proxy.search_candidate(payload)
        data = decode_resp_json(resp)
        return data['data']

    # def send_job(self, uid, jid, greet_text):
    #     resp = self.proxy.send(uid, greet_text, jid=jid, greet_name='您好，')
    #     data = decode_resp_json(resp)
    #     return data['result'] == 'ok'

    def batch_send_job(self, uids, pid, greet_text):
        jid = self.get_jid_by_pid(pid)
        resp = self.proxy.batch_send(uids, greet_text, jid=jid, greet_name_type='姓+先生/女士')
        data = decode_resp_json(resp)
        return data

    def chat_init(self):
        resp = self.proxy.chat()
        text = resp.text
        match = re.search(PATTERN_MM_CSRF, text)
        try:
            _csrf = match.group(1)
        except Exception as e:
            raise NoCSRFException(str(e))

        match = re.search(PATTERN_MM_CSRF_TOKEN, text)
        try:
            _csrf_token = match.group(1)
        except Exception as e:
            raise NoCSRFException(str(e))

        _csrf = _csrf.encode('utf-8').decode('unicode_escape')
        _csrf_token = _csrf_token.encode('utf-8').decode('unicode_escape')

        self.proxy._csrf = _csrf
        self.proxy.headers['X-Csrf-Token'] = _csrf_token
        self.proxy.cookies_dict['csrftoken'] = _csrf_token
        pass

    def get_msgs(self, count=100, only_unread=False):
        resp = self.proxy.get_msg_by_ldtime(count, only_unread=only_unread)
        data = decode_resp_json(resp)
        msgs = data['messages']
        return msgs

    def _get_trackable_token(self, uid):
        resp = self.proxy.get_contact(uid)
        return json.loads(resp.text)['data']['card']['trackable_token']

    def get_resume(self, uid):
        trackable_token = self._get_trackable_token(uid)
        resp = self.proxy.get_resume(uid, trackable_token)
        return decode_resp_json(resp)

    def req_mobile_vx(self, uid, mid, pid):
        ejid = self.get_ejid_by_pid(pid)
        resp1 = self.proxy.mobile_req(uid, mid, ejid)
        resp2 = self.proxy.vx_req(uid, mid, ejid)
        return decode_resp_json(resp1), decode_resp_json(resp2)

    def get_dialog(self, mid, count=100):
        r = []
        resp = self.proxy.get_dialog(mid)
        dialogs = decode_resp_json(resp)['dialogues']
        r += dialogs
        while len(dialogs) == 20 and len(r) < count:
            resp = self.proxy.get_dialog(mid, before_did=dialogs[0]['last_did'])
            dialogs = decode_resp_json(resp)['dialogues']
            r += dialogs
        r.sort(key=lambda x:x['crtimestamp'])
        return r

    def add_dialog(self, mid, msg):
        resp = self.proxy.add_dialog(mid, msg)
        return decode_resp_json(resp)['dialogue']['last_did']

    def get_mobile(self, mid):
        resp = self.proxy.enter_msg(mid)
        text = resp.text
        match = re.search(PATTERN_MM_MOBILE, text)
        if match:
            return match.group(1)
        return None

    def read_msg(self, mid, last_did):
        resp = self.proxy.clear_badge(mid, last_did)
        return resp.ok
