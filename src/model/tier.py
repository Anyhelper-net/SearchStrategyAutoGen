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

        def __lt__(self, other):
            if not isinstance(other, Tier.Type):
                return NotImplemented

            if self == other:
                return False

            if self == Tier.Type.Must:
                return False
            elif self == Tier.Type.Strong:
                return other == Tier.Type.Must
            else:  # self == Type.Nice
                return other in (Tier.Type.Must, Tier.Type.Strong)

    def __init__(self, tp: str, lv: int = 0):
        self.lv = lv
        self.tp = Tier.Type(tp)

    def __str__(self):
        return f'{self.Type.value}{self.lv}'

    def __eq__(self, other):
        if not isinstance(other, Tier):
            return False
        return self.tp == other.tp and self.lv == other.lv

    def __hash__(self):
        return hash((self.tp, self.lv))

    def __lt__(self, other):
        if not isinstance(other, Tier):
            return NotImplemented

        if self.tp == other.tp:
            return self.lv < other.lv
        else:
            return self.tp < other.tp
