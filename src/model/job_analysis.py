"""
@describe:
@fileName: job_analysis.py
@time    : 2025/12/5 下午3:50
@author  : duke
"""
from dataclasses import dataclass
from typing import Iterable
from src.model.tier import Tier
import json


class Analysis:
    @dataclass
    class Industry:
        core: str
        core_tier: Tier
        detailed: Iterable[str]
        detailed_tier: Tier

    @dataclass
    class TargetComp:
        type: str
        comps: Iterable[str]
        tier: Tier

    @dataclass
    class Location:
        is_remote: bool
        best_cities: Iterable[str]
        default: Iterable[str]
        nearby: Iterable[str]

    @dataclass
    class PositionName:
        level: str
        type: str
        title_keywords: Iterable
        core_titles: Iterable

    @dataclass
    class MajorReqs:
        tier: Tier
        keywords: Iterable

    def __init__(self, **kwargs):
        tmp = kwargs['TargetIndustry']
        self.industry = Analysis.Industry(tmp['core_category'], Tier(tmp['core_category_tier']),
                                          tmp['detailed_category'], Tier(tmp['detailed_category_tier']))
        tmp = kwargs['TargetCompany']
        self.company = Analysis.TargetComp(tmp['type'],
                                           tmp['companies'].split(',') if tmp['type'] == '明确列出名字' else [],
                                           None if tmp['Tier'] == '无' else Tier(tmp['Tier']))

        tmp = kwargs['TargetLocation']
        self.location = Analysis.Location(True if tmp['is_remote'] == 'true' else False, tmp['best_cities'].split(','),
                                          tmp['default_location'].split(','), tmp['nearby'].split(','))

        tmp = kwargs['PositionName']
        self.position_name = Analysis.PositionName(tmp['level'], tmp['type'],
                                                   tmp['title_keywords'].split(','), tmp['core_titles'].split(','))

        tmp = kwargs['MajorRequirements']
        self.major_reqs = Analysis.MajorReqs(None if tmp['Tier'] == '无' else Tier(tmp['Tier']),
                                             [] if tmp['Keywords'] == '无' else tmp['Keywords'].split(','))
