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
from src.model.search_strategy import SearchKeywordsGroup, Priority, PositionType


class Generator:
    def __init__(self, cookies, pid):
        self.lp_io = UserProxy(cookies)
        self.pid = pid
        self.keywords_groups, self.position_type = self._get_parse_reqs(pid)

    def _get_parse_reqs(self, pid):
        resp = ah_io.get_position_info(pid)
        data = resp.json()
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

        groups: List[SearchKeywordsGroup] = []
        for line in lines:
            vals = line.split('|')
            keywords = vals[3].split()
            keywords_mapping = vals[5].split()
            tp = vals[1]
            priority = Priority(vals[4], int(vals[0].replace(vals[4], '')))
            is_rare = False if vals[6] == 'FALSE' else True
            group = SearchKeywordsGroup(keywords, keywords_mapping, tp, priority, is_rare)
            groups.append(group)

        return groups, position_tp
