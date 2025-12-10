"""
@describe:
@fileName: strategy.py
@time    : 2025/12/2 上午10:37
@author  : duke
"""
from typing import Sequence
from .hard_reqs import HardRequirements
from .keywords_group import KeywordsGroup
from .job_analysis import Analysis
from .tier import Tier
from src.config.lp import TEMP_LP_SEARCH_PARAMS_INPUT_VO
from copy import deepcopy


class SearchStrategy:
    class Option:
        def __init__(self, values: Sequence, index: int):
            self.values = values
            self.index = index
            self.len = len(values)

        def zoom_in(self):
            self.index += 1
            if self.index >= self.len:
                self.index = self.len - 1
                raise IndexError('cannot zoom out')
            return self.value()

        def zoom_out(self):
            self.index -= 1
            if self.index < 0:
                self.index = 0
                raise IndexError('cannot zoom in')
            return self.value()

        def value(self):
            return self.values[self.index]

    def __init__(self, hard_reqs: HardRequirements, analysis: Analysis):
        a_options = dict()[SearchStrategy.Option]
        b_options = dict()[SearchStrategy.Option]
        c_options = dict()[SearchStrategy.Option]

        self.a_options = a_options
        self.b_options = b_options
        self.c_options = c_options

        a_options['active_status'] = SearchStrategy.Option(('07', '05', '04'), 1)
        a_options['position_name'] = SearchStrategy.Option(
            (analysis.position_name.core_titles, analysis.position_name.title_keywords), 1)
        a_options['major'] = SearchStrategy.Option(([], analysis.major_reqs.keywords),
                                                   0 if analysis.major_reqs.tier.tp is Tier.Type.Nice else 1)
        a_options['stability'] = SearchStrategy.Option(('', '1'), 0)

    def get_lp_payload_inner(self):
        r = deepcopy(TEMP_LP_SEARCH_PARAMS_INPUT_VO)
        r['activeStatus'] = self.a_options['active_status'].value()
        r['jobName'] = ' '.join(self.a_options['position_name'].value())
        r['major'] = ' '.join(self.a_options['major'].value())
        r['jobStability'] = self.a_options['stability'].value()
