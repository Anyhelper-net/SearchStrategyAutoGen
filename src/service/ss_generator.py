"""
@describe:
@fileName: ss_generator.py
@time    : 2025/12/4 上午10:44
@author  : duke
"""
import json
import math
from enum import Enum
import os

from concurrent_log_handler import ConcurrentRotatingFileHandler

from src.config.lp import RangeTargetResumes, DFS_STEP_MAX
from src.service.lp import LpService
import src.io.bot as bot_io
import src.io.anyhelper as ah_io
from src.config.bot import ENUM_MODEL_ID
from typing import List
from src.model import *
import copy
from src.utils.logger import logger
from src.utils.method import random_sleep
from src.config.path import LOG_DIR


class Generator:
    class PositionType(Enum):
        SingleCore = '单核心岗位'
        MutiCore = '多核心岗位'

    def __init__(self, cookies, pid):
        self.logger = logger.getChild(f'strategy_generator_{pid}')
        handler = ConcurrentRotatingFileHandler(
            os.path.join(LOG_DIR, f'pid_{pid}.log'),
            maxBytes=1024 * 1024,
            backupCount=5
        )
        self.logger.addHandler(handler)

        self.logger.info(f'building generator for pid:{pid}...')

        self.lp_service = LpService(cookies)
        self.pid = pid
        data1, data2 = self._get_position_info()

        self.keywords_groups: List[KeywordsGroup]
        self.position_type: Generator.PositionType
        self.job_analysis: Analysis
        self.hard_reqs: HardRequirements
        self.strategy: SearchStrategy
        self.trace: List[dict]
        self.default_group_num: int = 0

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
        msg = json.dumps(msg, ensure_ascii=False)
        self.logger.info(f'bot1 input:\n{msg}')
        resp = bot_io.send(msg, ENUM_MODEL_ID.REQUIREMENT_PARSER)
        data = bot_io.parse(resp)
        self.logger.info(f'bot1 output:\n{data}')

        lines = data.split('\n')
        position_tp = self.PositionType(lines.pop()[5:])

        groups: List[KeywordsGroup] = []
        for line in lines:
            if not line:
                continue
            vals = line.split('|')
            keywords = vals[3].split()
            keywords_mapping = vals[4].split()
            tp = vals[1]
            tier = Tier(vals[0][:-1], int(vals[0][-1]))
            # tier = Tier(vals[4], int(vals[0].replace(vals[4], '')))
            is_rare = False if vals[5] == 'FALSE' else True
            group = KeywordsGroup(keywords, keywords_mapping, tp, tier, is_rare)
            groups.append(group)
            if tier.tp is not Tier.Type.Nice:
                self.default_group_num += 1

        groups = sorted(groups, key=lambda g: g.tier, reverse=True)
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
        msg = json.dumps(msg, ensure_ascii=False)
        self.logger.info(f'bot2 input:\n{msg}')
        resp = bot_io.send(msg, ENUM_MODEL_ID.JOBINFO_PARSER)
        data = bot_io.parse(resp)
        self.logger.info(f'bot2 output:\n{data}')

        data = json.loads(data)
        self.job_analysis = Analysis(**data)

    def _parse_hard_reqs(self, data):
        kwargs = {k: v for k, v in data['results'][0].items() if k in HardRequirements.__annotations__}
        self.hard_reqs = HardRequirements(**kwargs)

    def _set_default_strategy(self, r_limit):
        self.strategy = SearchStrategy(self.hard_reqs, self.job_analysis)
        self.strategy.r_limit = r_limit
        self.trace = []

    def _set_strategy_count(self):
        self.strategy.count = self.lp_service.get_resume_count(self.strategy.get_lp_payload_inner())
        # return self.strategy.count

    def dfs_strategy_company(self):
        if self.job_analysis.company.type != '明确列出名字':
            self.logger.info('no target comp strategy')
            return

        self.logger.info('start comps strategy generation')

        l, r = RangeTargetResumes.A.value if self.job_analysis.company.tier.tp is Tier.Type.Must else RangeTargetResumes.B.value
        self._set_default_strategy(r)

        self.strategy.set_comp_name(' '.join(self.job_analysis.company.comps))

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r

        keys = self.strategy.get_option_keys('DCBA' if is_zoom_in else 'DABC')

        # if not self._maxima_test(keys, is_zoom_in, l, r):
        #     self.logger.info('cant zoom into legal range')
        #     return

        self._dfs_strategy(keys, is_zoom_in, l, r)

    def dfs_strategy_cores(self):
        self.logger.info('start cores strategy generation')

        l, r = RangeTargetResumes.A.value
        self._set_default_strategy(r)

        if self.position_type is self.PositionType.SingleCore:
            self.logger.info('single core')

            keywords = []
            for group in self.keywords_groups:
                if group.tier.tp is Tier.Type.Must:
                    # keywords += group.keywords
                    keywords += group.keywords_mapping
            keywords = ' '.join(keywords)
            keywords = SearchStrategy.Option((keywords,), 0)
            self.strategy.set_keywords_options(keywords)
            self.strategy.is_any_keywords = True

        # elif self.position_type is self.PositionType.MutiCore:
        else:
            self.logger.info('multiple cores')

            values = LazyTieredKeywordSequence(self.keywords_groups, k_min=2)
            self.strategy.set_keywords_options(
                SearchStrategy.Option(values, values.encode_idx(self.default_group_num, (0,) * self.default_group_num)))
            self.strategy.is_any_keywords = False

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r

        if self.position_type is self.PositionType.SingleCore:
            keys = self.strategy.get_option_keys('CBA' if is_zoom_in else 'ABCN')
        else:
            keys = self.strategy.get_option_keys('ECBA' if is_zoom_in else 'EABCN')

        # if not self._maxima_test(keys, is_zoom_in, l, r):
        #     self.logger.info('cant zoom into legal range')
        #     return

        self._dfs_strategy(keys, is_zoom_in, l, r)

    def _dfs_strategy_rares_b(self):
        self.logger.info('start rares strategy B generation')

        l, r = RangeTargetResumes.B.value
        self._set_default_strategy(r)

        if self.position_type is self.PositionType.SingleCore:
            self.logger.info('single core')

            values = LazyTieredKeywordSequence(self.keywords_groups, k_min=2)
            self.strategy.set_keywords_options(
                SearchStrategy.Option(values, values.encode_idx(self.default_group_num, (0,) * self.default_group_num)))
            self.strategy.is_any_keywords = False
        else:
            self.logger.info('multiple cores')

            keywords = []
            for group in self.keywords_groups:
                if group.tier.tp is Tier.Type.Must or group.tier.tp is Tier.Type.Strong:
                    # keywords += group.keywords
                    keywords += group.keywords_mapping
            keywords = ' '.join(keywords)

            keywords = SearchStrategy.Option((keywords,), 0)
            self.strategy.set_keywords_options(keywords)
            self.strategy.is_any_keywords = True

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r

        if self.position_type is self.PositionType.SingleCore:
            keys = self.strategy.get_option_keys('ECBA' if is_zoom_in else 'EABCN')
        else:
            keys = self.strategy.get_option_keys('CBA' if is_zoom_in else 'ABCN')

        # if not self._maxima_test(keys, is_zoom_in, l, r):
        #     self.logger.warn('cant zoom into legal range')
        #     return

        self._dfs_strategy(keys, is_zoom_in, l, r)

    # as keywords zooming is no longer line space after 3.1.0, _maxima_test should not be used anymore
    def _maxima_test(self, keys, is_zoom_in, l, r) -> bool:
        backup = self.strategy.export()

        # for key in keys:
        #     while True:
        #         try:
        #             if is_zoom_in:
        #                 self.strategy.zoom_in(key)
        #             else:
        #                 self.strategy.zoom_out(key)
        #         except SearchStrategy.Option.ZoomException:
        #             break
        for key in keys:
            opt = self.strategy._get_option(key)
            if is_zoom_in:
                opt.index = opt.length - 1
            else:
                opt.index = 0

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

    def _dfs_strategy(self, keys, is_zoom_in, l, r, limitation=DFS_STEP_MAX) -> bool:
        self._set_strategy_count()
        backup = self.strategy.export()
        self.trace.append(backup)
        id = len(self.trace)
        self.logger.info(f'<{id}>: {self.strategy}')
        if id > limitation:
            tmp = min(self.trace, key=lambda x: abs(x['count'] - r))
            self.strategy.load(tmp)
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

        next_keys = copy.copy(keys)
        for key in keys:
            self.strategy.load(backup)
            try:
                if is_zoom_in:
                    before, after = self.strategy.zoom_in(key)
                    self.logger.info(f'based on <{id}> zoom in <{key}> from <{before}> into <{after}>')
                else:
                    before, after = self.strategy.zoom_out(key)
                    self.logger.info(f'based on <{id}> zoom out <{key}> from <{before}> into <{after}>')
            except SearchStrategy.Option.ZoomException:
                continue

            if self._dfs_strategy(next_keys, is_zoom_in, l, r):
                return True

            next_keys.remove(key)

        return False

    def _upload_strategy(self, mid_name):
        if self.strategy.count:
            resp = bot_io.send(str(self.strategy), ENUM_MODEL_ID.STRATEGY_NAME_GEN)
            data = bot_io.parse(resp)
            name = f'{self.strategy.count}/{self.strategy.r_limit}_{mid_name}_{data}'
            payload = json.dumps(self.strategy.get_lp_local_storage(), ensure_ascii=False)
            resp = ah_io.upload_search_strategy(self.pid, name, payload, 'liepin')
            if resp.ok:
                self.logger.info(
                    f'strategy {name} uploaded:\n {self.strategy}\n')
            else:
                self.logger.warn(resp.text)
        else:
            self.logger.warn('got no candidate')

    def _remove_current_keywords(self):
        to_be_removed_keywords = self.strategy.e_options['keywords'].values().split()

        for group in self.keywords_groups:
            group: KeywordsGroup
            for to_be_removed_keyword in to_be_removed_keywords:
                try:
                    group.keywords.remove(to_be_removed_keyword)
                    continue
                except ValueError:
                    pass
                try:
                    group.keywords_mapping.remove(to_be_removed_keyword)
                    continue
                except ValueError:
                    pass

    def run(self):
        # cores strategy
        self.dfs_strategy_cores()
        self._upload_strategy('cores')

        # company strategy
        if self.job_analysis.company.type == '明确列出名字':
            self.dfs_strategy_company()
            self._upload_strategy('comp')
        else:
            self.logger.warn('no target comp strategy\n')

        # rares strategy B & backup strategy
        self._dfs_strategy_rares_b()
        self._upload_strategy('rares_b')

        # backup
        self._remove_current_keywords()
        self._dfs_strategy_rares_b()
        self._upload_strategy('backup')
