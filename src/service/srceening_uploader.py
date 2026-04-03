from src.model import SearchStrategy
from src.model.candidate import Candidate
from src.model.zl_strategy import zhilian_search_conditon
from src.service.lp import LpService
from src.model.mm_strategy import MMStrategy
from src.service.mm import MMService
from src.service.zl import ZlService
from src.utils import random_sleep
from src.config.screening import *


class ScreeningUploader:
    def __init__(
            self,
            strategy,
            lp_service=None,
            mm_service=None,
            zl_service=None,
            lp_plate_count=0,
            mm_plate_count=0,
            zl_plate_count=0,
        ):
        self.lp_service: LpService = lp_service
        self.strategy: SearchStrategy = strategy
        self.mm_service: MMService = mm_service
        self.zl_service: ZlService = zl_service
        self.strategy_limit_count = STRATEGY_VIEWED_LIMIT
        self.plate_limit_count = PLATE_VIEWED_LIMIT
        self.lp_strategy_count = 0
        self.mm_strategy_count = 0
        self.zl_strategy_count = 0
        self.lp_plate_count = lp_plate_count
        self.mm_plate_count = mm_plate_count
        self.zl_plate_count = zl_plate_count

    def _get_strategy_count(self, platform):
        if platform == 'lp':
            return self.lp_strategy_count
        if platform == 'mm':
            return self.mm_strategy_count
        if platform == 'zl':
            return self.zl_strategy_count
        raise ValueError(f'unknown platform: {platform}')

    def _get_plate_count(self, platform):
        if platform == 'lp':
            return self.lp_plate_count
        if platform == 'mm':
            return self.mm_plate_count
        if platform == 'zl':
            return self.zl_plate_count
        raise ValueError(f'unknown platform: {platform}')

    def _can_upload(self, platform):
        return self._get_strategy_count(platform) < self.strategy_limit_count and \
            self._get_plate_count(platform) < self.plate_limit_count

    def _increase_count(self, platform):
        if platform == 'lp':
            self.lp_strategy_count += 1
            self.lp_plate_count += 1
        elif platform == 'mm':
            self.mm_strategy_count += 1
            self.mm_plate_count += 1
        elif platform == 'zl':
            self.zl_strategy_count += 1
            self.zl_plate_count += 1
        else:
            raise ValueError(f'unknown platform: {platform}')

    def liepin_upload(self, pid, hid):
        cur_page = 0
        _PAGE_SIZE = 30
        while self._can_upload('lp'):
            random_sleep()
            data = self.lp_service.get_resumes(self.strategy.get_lp_payload_inner(), cur_page=cur_page)
            tmp_resumes = data.get('data', {}).get('resList')
            if not tmp_resumes:
                break
            for resume in tmp_resumes:
                if not self._can_upload('lp'):
                    break
                data = self.lp_service.get_resume_detail(resume['simpleResumeForm']['resIdEncode'])
                resume_detail = data['data']
                candidate = Candidate.from_lp_raw_resume(resume_detail, pid, hid)
                if resume_detail.get('goldUser', False):
                    candidate.gold_collar = True
                candidate.upload_screening_resume_to_anyJob()
                self._increase_count('lp')
            cur_page += 1

    def maimai_upload(self, pid, hid):
        lp_strategy = self.strategy.get_lp_payload_inner()
        mm_strategy = MMStrategy()
        mm_strategy.load_from_lp(lp_strategy)
        page_index = 0
        _PAGE_SIZE = 30
        total = self.mm_service.search_candidate(mm_strategy, page_index, _PAGE_SIZE)['total']
        if not int(total):
            return
        while self._can_upload('mm'):
            random_sleep()
            data = self.mm_service.search_candidate(mm_strategy, page_index, _PAGE_SIZE)
            mm_uids = data['all_uids']
            if not len(mm_uids):
                break
            mm_uids = list(mm_uids)
            if not len(mm_uids):
                page_index += 1
                continue
            for mm_uid in mm_uids:
                if not self._can_upload('mm'):
                    break
                resume = self.mm_service.get_resume(mm_uid)['data']
                candidate = Candidate.from_mm_raw_resume(resume, pid, hid)
                candidate.upload_screening_resume_to_anyJob()
                self._increase_count('mm')
            page_index += 1

    def zhilian_upload(self, pid, hid):
        lp_strategy = self.strategy.get_lp_payload_inner()
        zl_strategy = zhilian_search_conditon.from_liepin_condition(lp_strategy)
        cur_page = 0
        _PAGE_SIZE = 20
        while self._can_upload('zl'):
            random_sleep()
            response = self.zl_service.get_resumes(zl_strategy, cur_page=cur_page)
            candidate_list = response.get('data', {}).get('list', [])
            if not candidate_list:
                break
            for resume in candidate_list:
                if not self._can_upload('zl'):
                    break
                candidate = Candidate.from_zl_raw_resume(resume, pid, hid)
                candidate.upload_screening_resume_to_anyJob()
                self._increase_count('zl')
            cur_page += 1
