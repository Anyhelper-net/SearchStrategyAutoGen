"""
@describe:
@fileName: classes.py
@time    : 2025/12/5 下午2:27
@author  : duke
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List


class AlphaTier(Enum):
    A = auto()
    B = auto()
    C = auto()
    E = auto()
    N = auto()


class PositionType(Enum):
    SingleCore = '单核心岗位'
    MutiCore = '多核心岗位'
