"""
@describe:
@fileName: job_analysis.py
@time    : 2025/12/5 下午3:50
@author  : duke
"""
from dataclasses import dataclass


class Analysis:
    @dataclass
    class Industry:
        core: str
