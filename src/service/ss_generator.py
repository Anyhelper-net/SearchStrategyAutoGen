"""
@describe:
@fileName: ss_generator.py
@time    : 2025/12/4 上午10:44
@author  : duke
"""
import json
from enum import Enum

from src.service.lp import LpService
import src.io.bot as bot_io
import src.io.anyhelper as ah_io
from src.config.bot import ENUM_MODEL_ID
from typing import List
from src.model import *


class Generator:
    class PositionType(Enum):
        SingleCore = '单核心岗位'
        MutiCore = '多核心岗位'

    def __init__(self, cookies, pid):
        self.lp_service = LpService(cookies)
        self.pid = pid
        data1, data2 = self._get_position_info()

        self.keywords_groups: List[KeywordsGroup]
        self.position_type: Generator.PositionType
        self.job_analysis: Analysis
        self.hard_reqs: HardRequirements
        self.strategy: SearchStrategy

        self._parse_search_keywords_groups(data1)
        self._parse_job_analysis(data1, data2)
        self._parse_hard_reqs(data1)
        self._set_default_strategy()

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
        position_tp = self.PositionType(lines.pop()[5:])

        groups: List[KeywordsGroup] = []
        for line in lines:
            vals = line.split('|')
            keywords = vals[3].split()
            keywords_mapping = vals[5].split()
            tp = vals[1]
            tier = Tier(vals[4], int(vals[0].replace(vals[4], '')))
            is_rare = False if vals[6] == 'FALSE' else True
            group = KeywordsGroup(keywords, keywords_mapping, tp, tier, is_rare)
            groups.append(group)

        self.keywords_groups = groups
        self.position_type = position_tp
        # return groups, position_tp

    def _parse_job_analysis(self, data1, data2):
        msg = {
            'job_description': data1['results'][0]['description'],
            'summary': data1['results'][0]['summary'],
            'comments': data1['comments'],
            'employer': data2['results'],
        }
        msg = json.dumps(msg)
        resp = bot_io.send(msg, ENUM_MODEL_ID.JOBINFO_PARSER)
        data = bot_io.parse(resp)
        data = json.loads(data)
        self.job_analysis = Analysis(**data)

    def _parse_hard_reqs(self, data):
        kwargs = {k: v for k, v in data['results'][0].items() if k in HardRequirements.__annotations__}
        self.hard_reqs = HardRequirements(**kwargs)

    def _set_default_strategy(self):
        self.strategy = SearchStrategy(self.hard_reqs, self.job_analysis)

    def bfs_strategy_company(self):
        if self.job_analysis.company.type != '明确列出名字':
            return None

        self._set_default_strategy()
        self.strategy.keywords = ' '.join(self.job_analysis.company.comps[:8])
        self.strategy.is_any_keywords = False

        pass

    def bfs_strategy_cores(self):
        if self.position_type is self.PositionType.SingleCore:
            return self._bfs_strategy_cores_single()
        else:
            return self._bfs_strategy_cores_multi()

    def _bfs_strategy_cores_single(self):
        pass

    def _bfs_strategy_cores_multi(self):
        pass
