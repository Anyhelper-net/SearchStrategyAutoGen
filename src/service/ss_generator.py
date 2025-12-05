"""
@describe:
@fileName: ss_generator.py
@time    : 2025/12/4 上午10:44
@author  : duke
"""
import json
from src.io.lp import UserProxy
import src.io.bot as bot_io
import src.io.anyhelper as ah_io
from src.config.bot import ENUM_MODEL_ID
from typing import List
from src.model.strategy import KeywordsGroup, Priority, PositionType


class Generator:
    def __init__(self, cookies, pid):
        self.lp_io = UserProxy(cookies)
        self.pid = pid
        data1, data2 = self._get_position_info()

        self.keywords_groups = None
        self.position_type = None
        self._parse_search_keywords_groups(data1)

    def _get_position_info(self):
        resp1 = ah_io.get_position_info(self.pid)
        data1 = resp1.json()
        resp2 = ah_io.get_position_info_2(self.pid)
        data2 = resp2.json()
        return data1, data2

    def _parse_search_keywords_groups(self, data):
        msg = {
            'job_description': data['results'][0]['description'],
            'summary': data['results'][0]['summary'],
            # 'summary2': data['results'][0]['name_summary'],
            'comments': data['comments']
        }
        msg = json.dumps(msg)
        resp = bot_io.send(msg, ENUM_MODEL_ID.REQUIREMENT_PARSER)
        data = bot_io.parse(resp)

        lines = data.split('\n')
        position_tp = PositionType(lines.pop()[5:])

        groups: List[KeywordsGroup] = []
        for line in lines:
            vals = line.split('|')
            keywords = vals[3].split()
            keywords_mapping = vals[5].split()
            tp = vals[1]
            priority = Priority(vals[4], int(vals[0].replace(vals[4], '')))
            is_rare = False if vals[6] == 'FALSE' else True
            group = KeywordsGroup(keywords, keywords_mapping, tp, priority, is_rare)
            groups.append(group)

        self.keywords_groups = groups
        self.position_type = position_tp
        # return groups, position_tp

    def _parse_jobinfo(self, data1, data2):
        msg = {
            'job_description': data1['results'][0]['description'],
            'summary': data1['results'][0]['summary'],
            'comments': data1['comments'],
            'employer': data2['results'],
        }
        msg = json.dumps(msg)
        resp = bot_io.send(msg, ENUM_MODEL_ID.JOBINFO_PARSER)
        data = bot_io.parse(resp)

        pass

    def _parse_hard_reqs(self, data):
        pass
