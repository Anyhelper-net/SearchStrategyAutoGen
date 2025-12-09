"""
@describe:
@fileName: tier.py
@time    : 2025/12/5 下午2:26
@author  : duke
"""
from enum import Enum


class Tier:
    class Type(Enum):
        Must = 'Must'
        Strong = 'Strong'
        Nice = 'Nice'

    def __init__(self, tp: str, lv: int = 0):
        self.lv = lv
        self.tp = Tier.Type(tp)
