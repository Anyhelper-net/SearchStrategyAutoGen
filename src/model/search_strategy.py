"""
@describe:
@fileName: search_strategy.py
@time    : 2025/12/2 上午10:37
@author  : duke
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List


class PriorityType(Enum):
    Must = 'Must'
    Strong = 'Strong'
    Nice = 'Nice'


class Priority:
    def __init__(self, tp: str, lv: int):
        self.lv = lv
        self.tp = PriorityType(tp)


@dataclass
class SearchKeywordsGroup:
    keywords: List[str]
    keywords_mapping: List[str]
    tp: str
    priority: Priority
    is_rare: bool


class Tier(Enum):
    A = auto()
    B = auto()
    C = auto()
    E = auto()
    N = auto()


class PositionType(Enum):
    SingleCore = '单核心岗位'
    MutiCore = '多核心岗位'
