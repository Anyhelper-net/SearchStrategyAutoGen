"""
@describe:
@fileName: ss_generator.py
@time    : 2025/12/4 上午10:44
@author  : duke
"""
import json
from itertools import combinations

import math
from enum import Enum
import os

from concurrent_log_handler import ConcurrentRotatingFileHandler

from src.config.lp import RangeTargetResumes, DFS_STEP_MAX, IS_REACT_BRAIN_ACTIVE, LP_IS_COMP_STRATEGY_ACTIVE
from src.service.lp import LpService
import src.io.bot as bot_io
import src.io.anyhelper as ah_io
from src.config.bot import ENUM_MODEL_ID
from typing import List
from src.model import *
import copy
from src.utils.logger import logger
from src.config.path import LOG_DIR
import logging


class Generator:
    class PositionType(Enum):
        SingleCore = '单核心岗位'
        MutiCore = '多核心岗位'

    class GeneratorException(RuntimeError):
        pass

    class EmptyKeywordsException(GeneratorException):
        pass

    class EmptyCompanyStrategyException(GeneratorException):
        pass
    class EmptyMustStrategyException(GeneratorException):
        pass

    def __init__(self, cookies, pid):
        self.logger = logger.getChild(f'strategy_generator_{pid}')
        handler = ConcurrentRotatingFileHandler(
            os.path.join(LOG_DIR, f'pid_{pid}.log'),
            maxBytes=1024 * 1024,
            backupCount=5
        )
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
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

        self.total_api_acc_num = 0

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

    def _set_default_strategy(self, t):
        self.strategy = SearchStrategy(self.hard_reqs, self.job_analysis)
        self.strategy.target = t
        self.trace = []

    def _set_strategy_count(self):
        self.total_api_acc_num += 1
        try:
            self.strategy.count = self.lp_service.get_resume_count(self.strategy.get_lp_payload_inner())
        except LpService.LpHumanRobotVerification:
            self.logger.warn(f'waiting human_robot verification, total api acc: <{self.total_api_acc_num}>')
            self.lp_service.proxy.human_robot_verification()
            self.strategy.count = self.lp_service.get_resume_count(self.strategy.get_lp_payload_inner())
        # return self.strategy.count

    def _select_strategy(self, l, r, t):
        if l <= self.strategy.count <= r:
            return
        tmp = min(self.trace, key=lambda x: abs(x['count'] - t))
        self.strategy.load(tmp)

    def _preset_strategy_company(self):
        self.logger.info('start comps strategy generation')

        l, r, t = RangeTargetResumes.A.value if self.job_analysis.company.tier.tp is Tier.Type.Must else RangeTargetResumes.B.value
        self._set_default_strategy(t)

        if self.job_analysis.company.type == '明确列出名字':
            self.strategy.set_comp_name(' '.join(self.job_analysis.company.comps))
        elif self.job_analysis.company.type == '明确列出范围':
            msg = self.job_analysis.company.comps
            resp = bot_io.send(msg, ENUM_MODEL_ID.COMP_RANGE2NAMES)
            data = bot_io.parse(resp)
            self.strategy.set_comp_name(data)
        else:
            raise self.EmptyCompanyStrategyException('no company strategy')

        return l, r, t

    def _dfs_strategy_company(self):
        l, r, t = self._preset_strategy_company()

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r

        keys = self.strategy.get_option_keys('DCBA' if is_zoom_in else 'DABC')

        if not self._maxima_test(keys, is_zoom_in, l, r):
            self.logger.info('cant zoom into legal range')
            return

        self._dfs_strategy(keys, is_zoom_in, l, r)

        self._select_strategy(l, r, t)

    def _preset_strategy_cores(self):
        self.logger.info('start cores strategy generation')

        l, r, t = RangeTargetResumes.A.value
        self._set_default_strategy(t)

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
            self._keywords_pre_check_set(l, r)
        return l, r, t

    def _dfs_strategy_cores(self):
        l, r, t = self._preset_strategy_cores()

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r

        if self.position_type is self.PositionType.SingleCore:
            keys = self.strategy.get_option_keys('CBA' if is_zoom_in else 'ABCN')
        else:
            keys = self.strategy.get_option_keys('ECBA' if is_zoom_in else 'EABCN')

        if not self._maxima_test(keys, is_zoom_in, l, r):
            self.logger.info('cant zoom into legal range')
            return

        self._dfs_strategy(keys, is_zoom_in, l, r)

        self._select_strategy(l, r, t)

    def _preset_strategy_rares_b(self):
        self.logger.info('start rares strategy B generation')

        l, r, t = RangeTargetResumes.B.value
        self._set_default_strategy(t)

        # temp change
        keywords_group_backup = self.keywords_groups
        if self.position_type is not self.PositionType.SingleCore:
            self.keywords_groups = [g for g in self.keywords_groups if g.is_rare]

        if self.position_type is self.PositionType.SingleCore:
            self.logger.info('single core')
            self._b_rare_strategy_keywords_pre_check_set(l, r)
        else:
            self.logger.info('multiple cores')

            keywords = []
            for group in self.keywords_groups:
                if group.tier.tp is Tier.Type.Must or group.tier.tp is Tier.Type.Strong:
                    keywords += group.keywords_mapping
            keywords = ' '.join(keywords)

            keywords = SearchStrategy.Option((keywords,), 0)
            self.strategy.set_keywords_options(keywords)
            self.strategy.is_any_keywords = True

        # restore temp change
        self.keywords_groups = keywords_group_backup

        return l, r, t

    def _preset_strategy_rares_c(self):
        self.logger.info('start rares strategy C generation')

        l, r, t = RangeTargetResumes.C.value
        self._set_default_strategy(t)

        keywords = []
        for group in self.keywords_groups:
            if group.is_rare and group.tier.tp is Tier.Type.Nice:
                keywords += group.keywords_mapping
        keywords = ' '.join(keywords)

        keywords = SearchStrategy.Option((keywords,), 0)
        self.strategy.set_keywords_options(keywords)
        self.strategy.is_any_keywords = True

        return l, r, t

    def _dfs_strategy_rares_c(self):
        l, r, t = self._preset_strategy_rares_c()

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r
        keys = self.strategy.get_option_keys('CBA' if is_zoom_in else 'ABCN')

        if not self._maxima_test(keys, is_zoom_in, l, r):
            self.logger.warn('cant zoom into legal range')
            return

        self._dfs_strategy(keys, is_zoom_in, l, r)

        self._select_strategy(l, r, t)

    def _dfs_strategy_rares_b(self):
        l, r, t = self._preset_strategy_rares_b()

        self._set_strategy_count()
        is_zoom_in = self.strategy.count > r

        if self.position_type is self.PositionType.SingleCore:
            keys = self.strategy.get_option_keys('ECBA' if is_zoom_in else 'EABCN')
        else:
            keys = self.strategy.get_option_keys('CBA' if is_zoom_in else 'ABCN')

        if not self._maxima_test(keys, is_zoom_in, l, r):
            self.logger.warn('cant zoom into legal range')
            return

        self._dfs_strategy(keys, is_zoom_in, l, r)

        self._select_strategy(l, r, t)

    def _b_rare_strategy_keywords_pre_check_set(self,l,r):
        self.strategy.is_any_keywords = False
        keywords_map :dict[str,int] = {}
        must_groups = [g for g in self.keywords_groups if g.tier.tp is Tier.Type.Must]
        strong_groups = [g for g in self.keywords_groups if g.tier.tp is Tier.Type.Strong]
        nice_groups = [g for g in self.keywords_groups if g.tier.tp is Tier.Type.Nice]
        if not strong_groups and not nice_groups:
            self.logger.info('no strong_groups and nice_groups in b rare')
            return
        target_groups = strong_groups[:2] + nice_groups[:2]
        for current in must_groups[0].keywords_mapping:
            for layer_idx,group in enumerate(target_groups,start=1):
                self.logger.info(f'b rare strategy single try layer {layer_idx} group={group.tier.tp}')
                best_over_limit = None
                accepted = False
                for kw in group.keywords_mapping:
                    trial = f'{current} {kw}'
                    self.strategy.set_keywords_options(SearchStrategy.Option((trial,), 0))
                    self._set_strategy_count()
                    self.logger.info(f'b rare strategy single try <{trial}> count={self.strategy.count}')
                    if l <= self.strategy.count <= r:
                        self.logger.info(f'b rare strategy single accept <{trial}>')
                        keywords_map[trial] = self.strategy.count
                        current = trial
                        accepted = True
                        break
                    if (best_over_limit is None and r <= self.strategy.count ) or (r <= self.strategy.count < best_over_limit):
                        best_over_limit = (self.strategy.count, trial)
                if not accepted:
                    if best_over_limit is None:
                        self.logger.warn(f'b rare strategy single no usable keyword in group {group.tier.tp}, skip')
                        continue
                    kw = best_over_limit[1]
                    keywords_map[kw] = self.strategy.count
                    self.logger.info(f"b rare strategy single all keywords over r,use minimal one <{kw}> count={best_over_limit[0]}")
        if keywords_map:
            keywords = list(dict(sorted(keywords_map.items(),key= lambda x:x[1],reverse=True)).keys())
            self.logger.info(f'keywords option {keywords} being set')
            self.strategy.set_keywords_options(SearchStrategy.Option(keywords, 0))
        else:
            self.logger.warn(f'b rare strategy single keywords get empty keywords,skip')

    def _keywords_pre_check_set(self, l, r):
        self.strategy.is_any_keywords = False
        # values = LazyTieredKeywordSequence(self.keywords_groups, k_min=2)
        # self.strategy.set_keywords_options(
        #     SearchStrategy.Option(values, values.encode_idx(self.default_group_num, (0,) * self.default_group_num)))
        keywords = []
        # for layer_max in range(2, len(self.keywords_groups)):
        #     combs = LazyProductSequence(self.keywords_groups[:layer_max])
        #     tmp_count = 0
        #     tmp_comb = None
        #     for comb in combs:
        #         self.strategy.set_keywords_options(SearchStrategy.Option((comb,), 0))
        #         self._set_strategy_count()
        #         self.logger.info(f'keywords <{comb}> count: {self.strategy.count}')
        #
        #         if l <= self.strategy.count <= r:
        #             tmp_comb = comb
        #             break
        #
        #         if self.strategy.count > tmp_count:
        #             tmp_count = self.strategy.count
        #             tmp_comb = comb
        #     if tmp_comb:
        #         keywords.append(tmp_comb)
        #     else:
        #         break

        tmp_count = 0
        tmp_comb = None
        for keyword1 in self.keywords_groups[0].keywords_mapping:
            for keyword2 in self.keywords_groups[1].keywords_mapping:
                comb = keyword1 + ' ' + keyword2
                self.strategy.set_keywords_options(SearchStrategy.Option((comb,), 0))
                self._set_strategy_count()
                self.logger.info(f'keywords <{comb}> count: {self.strategy.count}')
                if l <= self.strategy.count <= r:
                    tmp_comb = comb
                    break
                if self.strategy.count > tmp_count:
                    tmp_count = self.strategy.count
                    tmp_comb = comb
        if tmp_comb:
            keywords.append(tmp_comb)
        else:
            raise self.EmptyKeywordsException('no useful keywords comb')

        for g in self.keywords_groups[2:]:
            tmp_count = 0
            tmp_comb = None
            for keyword in g.keywords_mapping:
                comb = keywords[-1] + ' ' + keyword
                self.strategy.set_keywords_options(SearchStrategy.Option((comb,), 0))
                self._set_strategy_count()
                self.logger.info(f'keywords <{comb}> count: {self.strategy.count}')
                if l <= self.strategy.count <= r:
                    tmp_comb = comb
                    break
                if self.strategy.count > tmp_count:
                    tmp_count = self.strategy.count
                    tmp_comb = comb
            if tmp_comb:
                keywords.append(tmp_comb)
            else:
                break

        self.logger.info(f'keywords option {keywords} being set')
        self.strategy.set_keywords_options(SearchStrategy.Option(keywords, 0))

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
                next_keys.remove(key)
                continue

            if self._dfs_strategy(next_keys, is_zoom_in, l, r):
                return True

            next_keys.remove(key)

        return False

    def _upload_strategy(self, mid_name):
        if self.strategy.count:
            resp = bot_io.send(str(self.strategy), ENUM_MODEL_ID.STRATEGY_NAME_GEN)
            data = bot_io.parse(resp)
            name = f'{self.strategy.count}/{self.strategy.target}_{mid_name}_{data}'
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
        to_be_removed_keywords = self.strategy.e_options['keywords'].value().split()

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
        total_count = 0

        # # cores strategy
        # try:
        #     if IS_REACT_BRAIN_ACTIVE:
        #         self._brain_controlled_cores_strategy()
        #     else:
        #         self._dfs_strategy_cores()
        #     self._upload_strategy('cores')
        #     total_count += self.strategy.count
        # except self.GeneratorException as e:
        #     self.logger.warn(e)
        #
        # # company strategy
        # if LP_IS_COMP_STRATEGY_ACTIVE and self.job_analysis.company.tier:
        #     try:
        #         if IS_REACT_BRAIN_ACTIVE:
        #             self._brain_controlled_comp_strategy()
        #         else:
        #             self._dfs_strategy_company()
        #         self._upload_strategy('comp')
        #         total_count += self.strategy.count
        #     except self.GeneratorException as e:
        #         self.logger.warn(e)

        # rares strategy B
        try:
            if IS_REACT_BRAIN_ACTIVE:
                self._brain_controlled_rares_b_strategy()
            else:
                self._dfs_strategy_rares_b()
            self._upload_strategy('rares_b')
            total_count += self.strategy.count
        except self.GeneratorException as e:
            self.logger.warn(e)

        # rares strategy C
        try:
            if IS_REACT_BRAIN_ACTIVE:
                self._brain_controlled_rares_c_strategy()
            else:
                self._dfs_strategy_rares_c()
            self._upload_strategy('rares_c')
            total_count += self.strategy.count
        except self.GeneratorException as e:
            self.logger.warn(e)

        # backup
        try:
            self._remove_current_keywords()
            if IS_REACT_BRAIN_ACTIVE:
                self._brain_controlled_rares_b_strategy()
            else:
                self._dfs_strategy_rares_b()
            self._upload_strategy('backup')
            total_count += self.strategy.count
        except self.GeneratorException as e:
            self.logger.warn(e)

        if total_count < 400:
            self.strategy.filter_viewed = True
        else:
            return

        # cores strategy
        try:
            if IS_REACT_BRAIN_ACTIVE:
                self._brain_controlled_cores_strategy()
            else:
                self._dfs_strategy_cores()
            self._upload_strategy('cores')
        except self.GeneratorException as e:
            self.logger.warn(e)

        # company strategy
        if LP_IS_COMP_STRATEGY_ACTIVE and self.job_analysis.company.tier:
            try:
                if IS_REACT_BRAIN_ACTIVE:
                    self._brain_controlled_comp_strategy()
                else:
                    self._dfs_strategy_company()
                self._upload_strategy('comp')
            except self.GeneratorException as e:
                self.logger.warn(e)

    @staticmethod
    def _react_brain_communication(l, r, t, history):
        msg = {'l': l, 'r': r, 'target': t, 'history': history}
        resp = bot_io.send(json.dumps(msg, ensure_ascii=False), ENUM_MODEL_ID.ZOOM_BRAIN)
        data = bot_io.parse(resp)
        data = json.loads(data)
        return data['action'], data['data']

    def _brain_controlled_cores_strategy(self):
        l, r, t = self._preset_strategy_cores()

        self._brain_controlled_zoom(l, r, t)
        self._select_strategy(l, r, t)

    def _brain_controlled_comp_strategy(self):
        l, r, t = self._preset_strategy_company()

        self._brain_controlled_zoom(l, r, t)
        self._select_strategy(l, r, t)

    def _brain_controlled_rares_b_strategy(self):
        l, r, t = self._preset_strategy_rares_b()

        self._brain_controlled_zoom(l, r, t)
        self._select_strategy(l, r, t)

    def _brain_controlled_rares_c_strategy(self):
        l, r, t = self._preset_strategy_rares_c()

        self._brain_controlled_zoom(l, r, t)
        self._select_strategy(l, r, t)

    def _brain_controlled_zoom(self, l, r, t):
        self._set_strategy_count()

        msg = {
            'id': 0,
            # 'is_zoom_in': None,
            # 'based_on': None,
            # 'key': None,
            'count': self.strategy.count
        }
        self.logger.info(json.dumps(msg, ensure_ascii=False))
        history = [msg]
        current_idx = 0
        self.trace.append(self.strategy.export())

        while len(self.trace) < DFS_STEP_MAX:
            action, data = self._react_brain_communication(l, r, t, history)
            if action == 'stop':
                break
            elif action == 'back':
                current_idx = data
                self.strategy.load(self.trace[current_idx])
                msg = {'action': action, 'id': current_idx}
                self.logger.info(json.dumps(msg, ensure_ascii=False))
                history.append(msg)
            elif action == 'zoom':
                is_zoom_in = data['is_zoom_in']
                key = data['key']
                before, after = None, None
                try:
                    if is_zoom_in:
                        before, after = self.strategy.zoom_in(key)
                    else:
                        before, after = self.strategy.zoom_out(key)
                except self.strategy.Option.ZoomException:
                    msg = f'try to zoom {'in' if is_zoom_in else 'out'} <{key}> based on <{current_idx}> failed cuz already at the border'
                    self.logger.info(msg)
                    history.append(msg)
                    continue
                self._set_strategy_count()
                self.trace.append(self.strategy.export())
                msg = {
                    'id': len(self.trace) - 1,
                    'based_on': current_idx,
                    'count': self.strategy.count,
                    'is_zoom_in': is_zoom_in,
                    'key': key,
                    'before': before,
                    'after': after,
                }
                history.append(msg)
                self.logger.info(json.dumps(msg, ensure_ascii=False))
                msg.pop('before')
                msg.pop('after')
                current_idx = len(self.trace) - 1
