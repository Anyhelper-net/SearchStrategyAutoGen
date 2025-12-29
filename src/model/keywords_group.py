"""
@describe:
@fileName: keywords_group.py
@time    : 2025/12/5 下午2:25
@author  : duke
"""
from dataclasses import dataclass
from src.model.tier import Tier
import itertools
from typing import Iterable, List, Tuple
import math
from collections.abc import Sequence


@dataclass
class KeywordsGroup:
    keywords: List[str]
    keywords_mapping: List[str]
    tp: str
    tier: Tier
    is_rare: bool


# def keyword_group_iter(groups, k):
#     for selected_groups in itertools.combinations(groups, k):
#         term_lists = [
#             g.keywords + g.keywords_mapping
#             for g in selected_groups
#         ]
#         yield from itertools.product(*term_lists)
#
#
# def tiered_keyword_iter(
#         groups: List[KeywordsGroup],
#         start_k: int,
#         max_k: int,
# ):
#     groups = sorted(groups, key=lambda g: g.tier)
#
#     for k in range(start_k, max_k + 1):
#         for combo in keyword_group_iter(groups[:k], k):
#             yield combo


class LazyProductSequence(Sequence):
    def __init__(self, groups: List[KeywordsGroup]):
        self.groups = groups
        self.term_lists = [
            g.keywords + g.keywords_mapping
            for g in groups
        ]

        self._lens = [len(t) for t in self.term_lists]
        self._len = math.prod(self._lens)

    def __len__(self):
        return self._len

    def __getitem__(self, idx):
        if idx < 0:
            raise IndexError

        result = []
        for terms in self.term_lists:
            size = len(terms)
            if size == 0:
                raise IndexError

            idx, offset = divmod(idx, size)
            try:
                result.append(terms[offset])
            except IndexError:
                raise IndexError

        if idx != 0:
            raise IndexError

        return ' '.join(result)


class LazyTieredKeywordSequence(Sequence):
    def __init__(self, groups, k_min=2):
        """
        groups: 已按 tier 排序
        k_min: 最小使用的 group 数
        """
        if k_min < 1 or k_min > len(groups):
            raise ValueError("invalid k_min")

        self.groups = groups
        self.k_min = k_min

        self.term_lists = [
            g.keywords + g.keywords_mapping
            for g in groups
        ]
        self.term_lens = [len(t) for t in self.term_lists]

        self.segment_lens = []
        self.segment_offsets = []

        offset = 0
        for k in range(k_min, len(groups) + 1):
            seg_len = 1
            for n in self.term_lens[:k]:
                seg_len *= n
            self.segment_offsets.append(offset)
            self.segment_lens.append(seg_len)
            offset += seg_len

        self._len = offset

    def __len__(self):
        return self._len

    def encode_idx(self, k, term_indices):
        if k < self.k_min or k > len(self.groups):
            raise IndexError

        if len(term_indices) != k:
            raise IndexError

        # 段内 offset
        inner = 0
        stride = 1
        for i in reversed(range(k)):
            size = self.term_lens[i]
            ti = term_indices[i]
            if ti < 0 or ti >= size:
                raise IndexError
            inner += ti * stride
            stride *= size

        seg = k - self.k_min
        return self.segment_offsets[seg] + inner

    def decode_idx(self, index):
        if index < 0 or index >= self._len:
            raise IndexError

        for i, (base, seg_len) in enumerate(
                zip(self.segment_offsets, self.segment_lens)
        ):
            if index < base + seg_len:
                k = self.k_min + i
                inner = index - base
                break
        else:
            raise IndexError

        term_indices = []
        for size in self.term_lens[:k]:
            if size == 0:
                raise IndexError
            inner, ti = divmod(inner, size)
            term_indices.append(ti)

        if inner != 0:
            raise IndexError

        return k, term_indices

    def __getitem__(self, index):
        k, term_indices = self.decode_idx(index)
        terms = []
        for i, ti in enumerate(term_indices):
            terms.append(self.term_lists[i][ti])
        return ' '.join(terms)
