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
from src.config.lp import TEMP_LP_SEARCH_PARAMS_INPUT_VO, SALARY_MAX_ZOOM_FACTOR, Mapping
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
                raise self.ZoomException('cannot zoom out')
            return self.value()

        def zoom_out(self):
            self.index -= 1
            if self.index < 0:
                self.index = 0
                raise self.ZoomException('cannot zoom in')
            return self.value()

        def value(self):
            return self.values[self.index]

        class ZoomException(RuntimeError):
            def __init__(self, *args, **kwargs):
                super().__init__(args, kwargs)

    def export(self):
        r = {}
        for k, v in self.a_options.items():
            r[k] = v.index
        for k, v in self.b_options.items():
            r[k] = v.index
        for k, v in self.c_options.items():
            r[k] = v.index
        for k, v in self.n_options.items():
            r[k] = v.index
        r['keywords'] = self.keywords
        r['is_any_keywords'] = self.is_any_keywords
        r['count'] = self.count
        return r

    def load(self, r):
        for k in self.a_options:
            self.a_options[k].index = r[k]
        for k in self.b_options:
            self.b_options[k].index = r[k]
        for k in self.c_options:
            self.c_options[k].index = r[k]
        for k in self.n_options:
            self.n_options[k].index = r[k]
        self.keywords = r['keywords']
        self.is_any_keywords = r['is_any_keywords']
        self.count = r['count']

    def __init__(self, hard_reqs: HardRequirements, analysis: Analysis):
        with open(LP_DQS_CODE_PATH, 'r', encoding='utf-8') as f:
            self.lp_dqs_code_dict = json.load(f)

        self.count = None

        a_options = dict[str: SearchStrategy.Option]()
        b_options = dict[str: SearchStrategy.Option]()
        c_options = dict[str: SearchStrategy.Option]()
        n_options = dict[str: SearchStrategy.Option]()

        self.a_options = a_options
        self.b_options = b_options
        self.c_options = c_options
        self.n_options = n_options

        # A
        a_options['active_status'] = SearchStrategy.Option(('07', '05', '04'), 1)
        a_options['position_name'] = SearchStrategy.Option(
            (analysis.position_name.core_titles, analysis.position_name.title_keywords), 1)
        if analysis.major_reqs.tier is None or analysis.major_reqs.tier.tp is Tier.Type.Nice:
            a_options['major'] = SearchStrategy.Option(([], analysis.major_reqs.keywords), 0)
        else:
            a_options['major'] = SearchStrategy.Option(([], analysis.major_reqs.keywords), 1)
        a_options['stability'] = SearchStrategy.Option(('', '1'), 0)

        # B
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

        # C
        if hard_reqs.language:
            c_options['language'] = SearchStrategy.Option(('', hard_reqs.language), 0)
        else:
            c_options['language'] = SearchStrategy.Option(('',), 0)
        c_options['max_age'] = SearchStrategy.Option((hard_reqs.max_age + 2, hard_reqs.max_age), 1)
        if hard_reqs.gender:
            c_options['sex'] = SearchStrategy.Option(('', hard_reqs.gender), 0)
        else:
            c_options['sex'] = SearchStrategy.Option(('',), 0)
        if hard_reqs.academic_requirements == '硕士':
            c_options['academic'] = SearchStrategy.Option(('本科', '硕士', '博士'), 1)
        else:
            c_options['academic'] = SearchStrategy.Option((hard_reqs.academic_requirements,), 0)
        if hard_reqs.college_requirements == '无要求':
            c_options['college'] = SearchStrategy.Option(('', '统招'), 0)
        else:
            c_options['college'] = SearchStrategy.Option(('', '统招', '985/211'), 1)

        # E
        self.keywords = ''
        self.is_any_keywords = False

        # N
        self.n_options['industry'] = SearchStrategy.Option(('', analysis.industry.core),
                                                           0 if analysis.industry.core_tier.tp is Tier.Type.Nice else 1)

        self.all_keys = list(self.a_options.keys()) + list(self.b_options.keys()) + list(self.c_options.keys()) + list(
            self.n_options.keys())

    def get_lp_payload_inner(self):
        r = deepcopy(TEMP_LP_SEARCH_PARAMS_INPUT_VO)
        r['activeStatus'] = self.a_options['active_status'].value()
        r['jobName'] = ' '.join(self.a_options['position_name'].value())
        r['major'] = ' '.join(self.a_options['major'].value())
        r['jobStability'] = self.a_options['stability'].value()

        r['wantDqs'] = ','.join(map(lambda x: self.lp_dqs_code_dict[x], self.b_options['city'].value()))
        r['wantSalaryHigh'] = str(self.b_options['max_salary'].value())
        r['workYearsLow'] = str(self.b_options['working_years_min'].value())

        r['languageSkills'] = Mapping.LAN_CODE_DICT[self.c_options['language'].value()]
        r['ageHigh'] = str(self.c_options['max_age'].value())
        r['sex'] = Mapping.SEX_CODE_DICT[self.c_options['sex'].value()]
        r['eduLevels'] = Mapping.EDU_LEVEL_CODE_DICT[self.c_options['academic'].value()]
        if self.c_options['college'] == '':
            pass
        elif self.c_options['college'] == '985/211':
            r['schoolKindList'] = ["1", "2"]
        elif self.c_options['college'] == '统招':
            r['eduLevelTzCode'] = r['eduLevels'][-1]

        r['keyword'] = self.keywords
        r['anyKeyword'] = '1' if self.is_any_keywords else '0'

        return r

    def _get_option(self, key):
        try:
            return self.a_options[key]
        except KeyError:
            pass
        try:
            return self.b_options[key]
        except KeyError:
            pass
        try:
            return self.c_options[key]
        except KeyError:
            pass
        try:
            return self.n_options[key]
        except KeyError:
            pass

    def zoom_out(self, key):
        option = self._get_option(key)
        return option.zoom_out()

    def zoom_in(self, key):
        option = self._get_option(key)
        return option.zoom_in()
