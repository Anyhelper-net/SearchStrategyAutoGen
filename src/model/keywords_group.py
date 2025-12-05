"""
@describe:
@fileName: keywords_group.py
@time    : 2025/12/5 下午2:25
@author  : duke
"""
from dataclasses import dataclass
from typing import List
from src.model.priority import Priority


@dataclass
class KeywordsGroup:
    keywords: List[str]
    keywords_mapping: List[str]
    tp: str
    priority: Priority
    is_rare: bool
