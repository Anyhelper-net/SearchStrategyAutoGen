"""
@describe:
@fileName: strategy.py
@time    : 2025/12/2 上午10:37
@author  : duke
"""
import json
from typing import Sequence
from src.model.hard_reqs import HardRequirements
from src.model.job_analysis import Analysis
from src.model.tier import Tier
from src.config.lp import TEMP_LP_SEARCH_PARAMS_INPUT_VO, SALARY_MAX_ZOOM_FACTOR, Mapping
from copy import deepcopy
from src.utils.logger import logger

strategy_logger = logger.getChild('strategy')


class SearchStrategy:
    class Option:
        def __init__(self, values: Sequence, index: int):
            self.values = values
            self.index = index
            self.length = len(values)

        def zoom_in(self):
            self.index += 1
            try:
                return self.value()
            except IndexError:
                self.index -= 1
                raise self.ZoomException('cannot zoom in')

        def zoom_out(self):
            self.index -= 1
            try:
                return self.value()
            except IndexError:
                self.index += 1
                raise self.ZoomException('cannot zoom out')

        def value(self):
            if self.index < 0:
                raise IndexError
            return self.values[self.index]

        class ZoomException(RuntimeError):
            pass

    def export(self):
        r = {
            'count': self.count,
            'comp_name': self.comp_name,
            'is_any_keywords': self.is_any_keywords,
        }
        for options in self.all_options_dict.values():
            for k, v in options.items():
                r[k] = v.index
        return r

    def load(self, r):
        self.comp_name = r['comp_name']
        self.is_any_keywords = r['is_any_keywords']
        self.count = r['count']
        for options in self.all_options_dict.values():
            for k in options:
                options[k].index = r[k]

    def __str__(self):
        r = {
            'count': self.count,
            'comp_name': self.comp_name,
            'is_any_keywords': self.is_any_keywords,
        }
        for options in self.all_options_dict.values():
            for k, v in options.items():
                r[k] = v.value()
        return json.dumps(r, ensure_ascii=False)

    def __init__(self, hard_reqs: HardRequirements, analysis: Analysis):

        self.count = None
        self.r_limit = None

        a_options = dict[str: SearchStrategy.Option]()
        b_options = dict[str: SearchStrategy.Option]()
        c_options = dict[str: SearchStrategy.Option]()
        d_options = dict[str: SearchStrategy.Option]()
        e_options = dict[str: SearchStrategy.Option]()
        n_options = dict[str: SearchStrategy.Option]()

        self.a_options = a_options
        self.b_options = b_options
        self.c_options = c_options
        self.d_options = d_options
        self.e_options = e_options
        self.n_options = n_options

        self.all_options_dict = {
            'A': a_options,
            'B': b_options,
            'C': c_options,
            'D': d_options,
            'E': e_options,
            'N': n_options,
        }

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

        # D
        self.comp_name: str = ''
        d_options['comp_period'] = SearchStrategy.Option(('0', '1'), 0)

        # E
        e_options['keywords'] = SearchStrategy.Option(('',), 0)
        self.is_any_keywords: bool = False

        # N
        self.n_options['industry'] = SearchStrategy.Option(('', analysis.industry.core),
                                                           0 if analysis.industry.core_tier.tp is Tier.Type.Nice else 1)

    def get_lp_local_storage(self):
        r = deepcopy(TEMP_LP_SEARCH_PARAMS_INPUT_VO)
        r['activeStatus'] = self.a_options['active_status'].value()
        r['jobName'] = ' '.join(self.a_options['position_name'].value())
        r['major'] = ' '.join(self.a_options['major'].value())
        r['jobStability'] = self.a_options['stability'].value()

        # r['wantDqs'] = ','.join(map(lambda x: Mapping.DQS_CODE_DICT[x], self.b_options['city'].value()))
        r['wantDqsOut'] = [{'dqCode': Mapping.DQS_CODE_DICT[x], 'dqName': x} for x in self.b_options['city'].value() if
                           x in Mapping.DQS_CODE_DICT]
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

        r['compName'] = self.comp_name
        r['compPeriod'] = self.d_options['comp_period'].value()

        r['keyword'] = self.e_options['keywords'].value()
        r['anyKeyword'] = '1' if self.is_any_keywords else '0'

        try:
            r['industryArr'] = [{'code': Mapping.INDUSTRY_CODE_DICT[self.n_options['industry'].value()],
                                 'name': self.n_options['industry'].value()}]
        except KeyError:
            strategy_logger.warn(f'no industry <{self.n_options['industry'].value()}>')
            r['industryArr'] = ''

        return r

    def get_lp_payload_inner(self):
        r = deepcopy(TEMP_LP_SEARCH_PARAMS_INPUT_VO)
        r['activeStatus'] = self.a_options['active_status'].value()
        r['jobName'] = ' '.join(self.a_options['position_name'].value())
        r['major'] = ' '.join(self.a_options['major'].value())
        r['jobStability'] = self.a_options['stability'].value()

        # r['wantDqs'] = ','.join(map(lambda x: Mapping.DQS_CODE_DICT[x], self.b_options['city'].value()))
        r['wantDqs'] = ','.join(
            [Mapping.DQS_CODE_DICT[x] for x in self.b_options['city'].value() if x in Mapping.DQS_CODE_DICT])
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

        r['compName'] = self.comp_name
        r['compPeriod'] = self.d_options['comp_period'].value()

        r['keyword'] = self.e_options['keywords'].value()
        r['anyKeyword'] = '1' if self.is_any_keywords else '0'

        try:
            r['industrys'] = Mapping.INDUSTRY_CODE_DICT[self.n_options['industry'].value()]
        except KeyError:
            strategy_logger.warn(f'no industry <{self.n_options['industry'].value()}>')
            r['industrys'] = ''

        return r

    def get_option_keys(self, s: str):
        r = []
        for c in s:
            r += list(self.all_options_dict[c].keys())
        return r

    def _get_option(self, key) -> Option:
        for options in self.all_options_dict.values():
            try:
                return options[key]
            except KeyError:
                pass

        raise RuntimeError('unknown option key')

    def zoom_out(self, key):
        option = self._get_option(key)
        before = option.value()
        return before, option.zoom_out()

    def zoom_in(self, key):
        option = self._get_option(key)
        before = option.value()
        return before, option.zoom_in()

    def set_keywords_options(self, val: Option):
        self.e_options['keywords'] = val

    def set_comp_name(self, val: str):
        self.comp_name = val
