"""
@describe:
@fileName: hard_reqs.py
@time    : 2025/12/5 下午2:27
@author  : duke
"""
from dataclasses import dataclass


@dataclass
class HardRequirements:
    academic_requirements: str
    college_requirements: str
    gender: str
    min_age: int
    max_age: int
    language: str
    working_years_min: int
    working_years_max: int
    salary_min: int
    salary_max: int
    stability_requirements: str
