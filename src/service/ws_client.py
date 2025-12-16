"""
@describe:
@fileName: ws_client.py
@time    : 2025/12/15 下午5:07
@author  : duke
"""
from threading import Event, Lock, Thread
from websocket import WebSocketApp
import json
import uuid
import time
import src.config
from src.config.ws_client import WS_SEVER_URL, HEARTBEAT_GAP
from src.utils.logger import logger
from src.service.ss_generator import Generator
import traceback
from src.config.path import WS_CFG_PATH


class Client:
    def __init__(self):
        with open(WS_CFG_PATH, 'r') as f:
            data = json.load(f)
            self.id = data['id']
            self.name = data['name']

        self.logger = logger.getChild('ws')
        self.lck = Lock()
        self.hb_thread: Thread = Thread(target=self.heartbeat_loop)
        self.stop_evt: Event = Event()
        self.ws = WebSocketApp(
            WS_SEVER_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

    def _on_open(self, ws):
        ws.send(json.dumps({
            "id": str(uuid.uuid4()),
            "type": "REGISTER",
            "payload": {
                "machine_id": self.id,
                "name": self.name,
                "agent_version": None,
            }
        }, ensure_ascii=False))

        self.start_heartbeat()

    def _on_message(self, ws, msg):
        self.logger.info(msg)
        data = json.loads(msg)

        if data['type'] == 'RUN_GENERATE_EXCEL':
            with self.lck:
                pid = int(data['payload']['positionID'])
                lp_cookies = data['payload']['cookies']['liepin']['value']
                mm_cookies = data['payload']['cookies']['maimai']['value']

                try:
                    generator = Generator(lp_cookies, pid)
                    generator.run()
                    self.report_task(data['payload']['task_id'], True, '')
                except Exception as e:
                    self.report_task(data['payload']['task_id'], False, str(e))
                    self.logger.error(e)
                    if src.config.IS_DEV:
                        raise
                    else:
                        traceback.print_exc()

                # add helpers here
                
        else:
            self.logger.info(msg)

    def _on_error(self, ws, error):
        self.logger.error(error)

    def _on_close(self, ws, close_status_code, close_msg):
        self.logger.info('ws closed')

    def send_heartbeat(self):
        self.ws.send(json.dumps({
            "id": str(uuid.uuid4()),
            "type": "HEARTBEA",
            "payload": {"run_state": "idle"}
        }, ensure_ascii=False))

    def heartbeat_loop(self, gap=HEARTBEAT_GAP):
        while not self.stop_evt.is_set():
            time.sleep(gap)
            if self.stop_evt.is_set():
                self.ws.close()
            else:
                self.send_heartbeat()

    def start_heartbeat(self):
        if self.hb_thread.is_alive():
            return
        self.hb_thread.start()

    def report_task(self, task_id, is_ok, fail_log):
        self.ws.send(json.dumps({
            "task_id": task_id,
            "ok": is_ok,
            "file_path": '',
            "fail_log": fail_log,
        }, ensure_ascii=False))

    def __del__(self):
        self.ws.close()
        self.stop_evt.set()
