"""
@describe:
@fileName: keywords_group.py
@time    : 2025/12/5 下午2:25
@author  : duke
"""
from dataclasses import dataclass
from typing import List
from src.model.tier import Tier


@dataclass
class KeywordsGroup:
    keywords: List[str]
    keywords_mapping: List[str]
    tp: str
    tier: Tier
    is_rare: bool
