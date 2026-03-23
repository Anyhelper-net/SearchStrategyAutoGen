import json
import copy

from src.utils.lp_name2zl_code_dq import get_zhlian_code_by_liepin_dqname


class zhilian_search_conditon:
    def __init__(self):
        self.filteringRead = False
        self.filteringChatted = True
        self.matchLatestWorkExperience = False
        self.filteringDownloaded = False
        self.filteringOtherChattedType = 'DONT_FILTER'
        self.sort = {
            "type": "COMPLEX",
            "version": 17
        }
        self.frontExperiment = True
        self.freeMaskLimit = False
        self.searchExperimentalGroup = 'EXPERIMENT'
        self.firstPageCacheable = False
        self.experiment = ''

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls()

        for key in data.keys():
            value = data.get(key, None)
            # 仅当 value 不为空时才赋值
            if value not in (None, '', [], {}):
                setattr(obj, key, copy.deepcopy(value))
        return obj

    @classmethod
    def from_json_str(cls, str):
        return cls.from_dict(json.loads(str))

    @classmethod
    def from_json_file(cls, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_liepin_condition(cls, data: dict):
        obj = cls()

        def get_value(key, default=None):
            return data.get(key, default)

        def to_int_or_none(value):
            return int(value) if value not in (None, '') else None

        keyword = get_value('keyword')
        if keyword:
            obj.keywordIntentions = {"keyword": keyword}

        job_name = get_value('jobName')
        comp_name = get_value('compName')
        school = get_value('school')
        if job_name or comp_name or school:
            obj.conditions = []

        if job_name:
            obj.conditions.append({
                'exactMatch': False,
                'key': 'JOB',
                'values': [str(job_name)]
            })

        if comp_name:
            obj.conditions.append({
                'exactMatch': False,
                'key': 'ORG',
                'values': [str(comp_name)]
            })

        if school:
            obj.conditions.append({
                'exactMatch': False,
                'key': 'SCHOOL',
                'values': [str(school)]
            })

        major = get_value('major')
        if major:
            obj.majorNames = major

        edu_levels = get_value('eduLevels')
        if edu_levels:
            obj.educations = []
            education_map = {
                '060': '12',
                '050': '5',
                '040': '4',
                '030': '3',
                '010': '1'
            }
            for education_level in edu_levels:
                if education_level == '0100':
                    obj.educations.append('9')
                    obj.educations.append('7')
                elif education_level in education_map:
                    obj.educations.append(education_map[education_level])

        obj.maxAge = to_int_or_none(get_value('ageHigh'))
        obj.minAge = to_int_or_none(get_value('ageLow'))
        obj.maxWorkYears = to_int_or_none(get_value('workYearsHigh'))
        obj.minWorkYears = to_int_or_none(get_value('workYearsLow'))

        school_kind_list = get_value('schoolKindList')
        if school_kind_list:
            obj.schoolNatures = []
            school_kind_map = {
                '2': 'SCHOOL211',
                '1': 'SCHOOL985',
                '9': 'SCHOOL_DOUBLE_FIRST_CLASS'
            }
            for school_kind in school_kind_list:
                mapped = school_kind_map.get(school_kind)
                if mapped:
                    obj.schoolNatures.append(mapped)

        edu_level_tz_code = get_value('eduLevelTzCode')
        if edu_level_tz_code == '040':
            obj.schoolNatures = ['UNIFIED']

        study_abroad = get_value('studyAbroad')
        if study_abroad:
            obj.schoolNatures = ['SCHOOL_OVERSEASE']

        active_status = get_value('activeStatus')
        if active_status:
            active_time_map = {
                '01': 1,
                '02': 3,
                '03': 7,
                '04': 30,
                '05': 90,
                '06': 180,
                '07': 365
            }
            mapped = active_time_map.get(active_status)
            if mapped is not None:
                obj.activeTime = mapped

        sex = get_value('sex')
        if sex:
            gender_map = {
                '1': '1',
                '2': '0'
            }
            mapped = gender_map.get(sex)
            if mapped is not None:
                obj.gender = mapped

        user_hope = get_value('userHope')
        if user_hope:
            obj.careerStates = []
            hope_map = {
                '1': '2',
                '2': '1',
                '0': '4',
                '3': '3'
            }
            hope_list = user_hope.split(',')
            for hope in hope_list:
                mapped = hope_map.get(hope)
                if mapped:
                    obj.careerStates.append(mapped)

        want_dqs_out = get_value('wantDqsOut')
        if want_dqs_out:
            obj.expectedCityIds = []
            for dqs in want_dqs_out:
                dq_name = dqs.get('dqName') if isinstance(dqs, dict) else None
                if dq_name:
                    obj.expectedCityIds.append(get_zhlian_code_by_liepin_dqname(dq_name, 'region'))

        now_dqs_out = get_value('nowDqsOut')
        if now_dqs_out:
            obj.currentCityIds = []
            for dqs in now_dqs_out:
                dq_name = dqs.get('dqName') if isinstance(dqs, dict) else None
                if dq_name:
                    obj.currentCityIds.append(get_zhlian_code_by_liepin_dqname(dq_name, 'region'))

        industry_arr = get_value('industryArr')
        want_job_title_arr = get_value('wantJobTitleArr')
        if industry_arr or want_job_title_arr:
            industry_map = {
                'H01': [100030000, 100040000, 100050000],
                'H0001': [100120000],
                'H02': [100010000, 100090000, 100140000],
                'H03': [400000000],
                'H04': [300000000],
                'H08': [500000000],
                'H0060': [500000000],
                'H09': [1200000000],
                'H14': [1100000000, 1100060000],
                'H0039': [700050000, 700060000],
                'H05': [700000000, 700010000, 700030000],
                'H0072': [700120000],
                'H06': [1300000000],
                'H0052': [500210000],
                'H0056': [1600020000],
                'H07': [1600000000],
                'H13': [1000000000],
                'H0106': [1000020000],
                'H0108': [700000000],
                'H0114': [1100050000],
                'H0120': [600000000],
                'H10': [800000000],
                'H11': [900000000],
                'H12': [1500000000],
                'H0118': [1400000000],
                'H0119': [1400000000]
            }
            if industry_arr:
                obj.currentIndustries = []
                for industry in industry_arr:
                    code = industry.get('code') if isinstance(industry, dict) else None
                    if code in industry_map:
                        obj.currentIndustries = [*obj.currentIndustries, *industry_map[code]]
            if want_job_title_arr:
                obj.expectedIndustries = []
                want_industry_arr = get_value('wantIndustryArr') or []
                for industry in want_industry_arr:
                    code = industry.get('code') if isinstance(industry, dict) else None
                    if code in industry_map:
                        obj.expectedIndustries = [*obj.expectedIndustries, *industry_map[code]]

        want_salary_high = get_value('wantSalaryHigh')
        want_salary_low = get_value('wantSalaryLow')
        if want_salary_high not in (None, ''):
            obj.expectedSalaryMax = int(int(want_salary_high) * 10000 / 12) + 1
            if want_salary_low in (None, ''):
                obj.expectedSalaryMin = 0
        if want_salary_low not in (None, ''):
            obj.expectedSalaryMin = int(int(want_salary_low) * 10000 / 12) + 1
            if want_salary_high in (None, ''):
                obj.expectedSalaryMax = 999999

        res_language = get_value('resLanguage')
        if res_language is not None:
            if res_language == '0':
                obj.resumeLanguage = '1'
            else:
                obj.resumeLanguage = '2'

        job_stability = get_value('jobStability')
        if job_stability:
            if job_stability == '1':
                obj.jobHopping = [1]
            else:
                obj.jobHopping = [2]

        if get_value('filterViewed'):
            obj.filteringRead = True
        if get_value('filterChat'):
            obj.filteringChatted = True
        if get_value('filterDownload'):
            obj.filteringDownloaded = True

        return obj

    def to_dict(self):
        result = {}
        for k, v in self.__dict__.items():
            if v not in (None, '', [], {}):
                result[k] = copy.deepcopy(v)
        return result

    def to_json_str(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_json_file(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)


