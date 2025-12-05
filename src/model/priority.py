"""
@describe:
@fileName: priority.py
@time    : 2025/12/5 下午2:26
@author  : duke
"""
from enum import Enum


class PriorityType(Enum):
    Must = 'Must'
    Strong = 'Strong'
    Nice = 'Nice'


class Priority:
    def __init__(self, tp: str, lv: int):
        self.lv = lv
        self.tp = PriorityType(tp)
