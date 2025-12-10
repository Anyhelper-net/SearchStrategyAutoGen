"""
@describe:
@fileName: strategy.py
@time    : 2025/12/2 上午10:37
@author  : duke
"""
import json
from typing import Sequence
from src.model.hard_reqs import HardRequirements
from src.model.keywords_group import KeywordsGroup
from src.model.job_analysis import Analysis
from src.model.tier import Tier
from src.config.lp import TEMP_LP_SEARCH_PARAMS_INPUT_VO, SALARY_MAX_ZOOM_FACTOR, LAN_CODE_DICT, SEX_CODE_DICT
from copy import deepcopy
from src.config.path import LP_DQS_CODE_PATH


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
        with open(LP_DQS_CODE_PATH, 'r', encoding='utf-8') as f:
            self.lp_dqs_code_dict = json.load(f)

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

        b_options['city'] = SearchStrategy.Option(
            (analysis.location.nearby, analysis.location.default, analysis.location.best_cities), 1)
        if hard_reqs.salary_max is None:
            b_options['max_salary'] = SearchStrategy.Option(('',), 0)
        else:
            b_options['max_salary'] = SearchStrategy.Option(
                (int(hard_reqs.salary_max * SALARY_MAX_ZOOM_FACTOR), hard_reqs.salary_max), 1)
        if hard_reqs.working_years_min - 2 < 2:
            b_options['working_years_min'] = SearchStrategy.Option((hard_reqs.working_years_min,), 0)
        else:
            b_options['working_years_min'] = SearchStrategy.Option(
                (hard_reqs.working_years_min - 2, hard_reqs.working_years_min), 1)

        if hard_reqs.language:
            c_options['language'] = SearchStrategy.Option(('', hard_reqs.language), 0)
        else:
            c_options['language'] = SearchStrategy.Option(('',), 0)
        c_options['max_age'] = SearchStrategy.Option((hard_reqs.max_age + 2, hard_reqs.max_age), 1)
        if hard_reqs.gender:
            c_options['sex'] = SearchStrategy.Option(('', hard_reqs.gender), 0)
        else:
            c_options['sex'] = SearchStrategy.Option(('',), 0)

    def get_lp_payload_inner(self):
        r = deepcopy(TEMP_LP_SEARCH_PARAMS_INPUT_VO)
        r['activeStatus'] = self.a_options['active_status'].value()
        r['jobName'] = ' '.join(self.a_options['position_name'].value())
        r['major'] = ' '.join(self.a_options['major'].value())
        r['jobStability'] = self.a_options['stability'].value()

        r['wantDqs'] = ','.join(map(lambda x: self.lp_dqs_code_dict[x], self.b_options['city'].value()))
        r['wantSalaryHigh'] = self.b_options['max_salary'].value()
        r['workYearsLow'] = self.b_options['working_years_min'].value()

        r['languageSkills'] = LAN_CODE_DICT[self.c_options['language'].value()]
        r['ageHigh'] = self.c_options['max_age'].value()
        r['sex'] = SEX_CODE_DICT[self.c_options['sex'].value()]
