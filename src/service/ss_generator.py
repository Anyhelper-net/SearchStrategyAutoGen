"""
@describe:
@fileName: ss_generator.py
@time    : 2025/12/4 上午10:44
@author  : duke
"""
import json
import math
from enum import Enum
from src.config.lp import RangeTargetResumes
from src.service.lp import LpService
import src.io.bot as bot_io
import src.io.anyhelper as ah_io
from src.config.bot import ENUM_MODEL_ID
from typing import List
from src.model import *
import copy


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
        self.trace: List[dict]

        self._parse_search_keywords_groups(data1)
        self._parse_job_analysis(data1, data2)
        self._parse_hard_reqs(data1)
        # self._set_default_strategy()

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

    def _set_default_strategy(self, keywords: SearchStrategy.Option):
        self.strategy = SearchStrategy(self.hard_reqs, self.job_analysis, keywords)
        self.trace = []

    def _set_strategy_count(self):
        self.strategy.count = self.lp_service.get_resume_count(self.strategy.get_lp_payload_inner())
        # return self.strategy.count

    def dfs_strategy_company(self):
        if self.job_analysis.company.type != '明确列出名字':
            return None

        pass

    def dfs_strategy_cores(self):
        print('start cores strategy generation\n')

        l, r = RangeTargetResumes.A.value

        if self.position_type is self.PositionType.SingleCore:
            print('single core\n')

            keywords = []
            for group in self.keywords_groups:
                if group.tier.tp is Tier.Type.Must:
                    keywords += group.keywords
                    keywords += group.keywords_mapping
            keywords = ' '.join(keywords)
            keywords = SearchStrategy.Option((keywords,), 0)
            self._set_default_strategy(keywords)
            self.strategy.is_any_keywords = True

        # elif self.position_type is self.PositionType.MutiCore:
        else:
            print('multiple cores\n')

            keywords1 = []
            keywords2 = []
            keywords3 = []
            for group in self.keywords_groups:
                if group.tier.tp is Tier.Type.Must:
                    keywords1 += group.keywords
                    keywords2 += group.keywords
                    keywords3 += group.keywords
                elif group.tier.tp is Tier.Type.Strong:
                    keywords2 += group.keywords
                    keywords3 += group.keywords
                elif group.tier.tp is Tier.Type.Nice:
                    keywords3 += group.keywords

            keywords1 = ''.join(keywords1)
            keywords2 = ''.join(keywords2)
            keywords3 = ''.join(keywords3)

            keywords = SearchStrategy.Option((keywords1, keywords2, keywords3), 1)
            self._set_default_strategy(keywords)
            self.strategy.is_any_keywords = False

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r

        if self.position_type is self.PositionType.SingleCore:
            keys = self.strategy.get_option_keys('CBA' if is_zoom_in else 'ABC')
        else:
            keys = self.strategy.get_option_keys('ECBA' if is_zoom_in else 'EABC')

        if not self._maxima_test(keys, is_zoom_in, l, r):
            print('cant zoom into legal range\n')
            return

        self._dfs_strategy(keys, is_zoom_in, l, r)

    def _maxima_test(self, keys, is_zoom_in, l, r) -> bool:
        backup = self.strategy.export()

        if is_zoom_in:
            for key in keys:
                try:
                    self.strategy.zoom_in(key)
                except SearchStrategy.Option.ZoomException:
                    pass
        else:
            for key in keys:
                try:
                    self.strategy.zoom_out(key)
                except SearchStrategy.Option.ZoomException:
                    pass

        self._set_strategy_count()
        res = None
        if is_zoom_in:
            res = self.strategy.count <= r
        else:
            res = self.strategy.count >= l

        if res:
            self.strategy.load(backup)
        else:
            self.trace.append(self.strategy.export())

        return res

    def _dfs_strategy(self, keys, is_zoom_in, l, r, limitation=math.inf) -> bool:
        self._set_strategy_count()
        backup = self.strategy.export()
        self.trace.append(backup)
        id = len(self.trace)
        print(f'<{id}>: {self.strategy}\n')

        if id > limitation:
            return True

        if is_zoom_in:
            if self.strategy.count < l:
                return False
            if self.strategy.count < r:
                return True
        else:
            if self.strategy.count > r:
                return False
            if self.strategy.count > l:
                return True

        for key in keys:
            self.strategy.load(backup)
            try:
                if is_zoom_in:
                    print(f'from <{id}> zoom in <{key}> into <{self.strategy.zoom_in(key)}>\n')
                else:
                    print(f'from <{id}> zoom out <{key}> into <{self.strategy.zoom_out(key)}>\n')
            except SearchStrategy.Option.ZoomException:
                continue
            next_keys = copy.copy(keys)
            next_keys.remove(key)

            if self._dfs_strategy(next_keys, is_zoom_in, l, r):
                return True

        return False
