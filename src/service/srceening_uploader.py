from src.model import SearchStrategy
from src.model.candidate import Candidate
from src.model.zl_strategy import zhilian_search_conditon
from src.service.lp import LpService
from src.model.mm_strategy import MMStrategy
from src.service.mm import MMService
from src.service.zl import ZlService
from src.utils import random_sleep


class ScreeningUploader:
    def __init__(self,strategy,lp_service=None,mm_service=None,zl_service=None):
        self.lp_service:LpService = lp_service
        self.strategy:SearchStrategy = strategy
        self.mm_service:MMService = mm_service
        self.zl_service:ZlService = zl_service
        self.limit_count = 200

    def liepin_upload(self,pid,hid):
        resumes = []
        cur_page = 0
        while cur_page * 30 < self.limit_count:
            random_sleep()
            data = self.lp_service.get_resumes(self.strategy.get_lp_payload_inner(),cur_page=cur_page)
            tmp_resumes = data.get('data', {}).get('resList')
            if not tmp_resumes:
                break
            resumes += tmp_resumes
            cur_page += 1

        for resume in resumes:
            data = self.lp_service.get_resume_detail(resume['simpleResumeForm']['resIdEncode'])

            resume_detail = data['data']

            data = self.lp_service.get_work_exp(resume_detail.get('basicInfoForm', {}).get('resJobtitle'),
                                           resume['simpleResumeForm']['resIdEncode'])

            resume_work_exp = data.get('data', {})

            candidate = Candidate.from_lp_raw_resume(resume_detail, resume_work_exp, pid, hid)

            if resume_detail.get('goldUser', False):
                candidate.gold_collar = True

            candidate.upload_screening_resume_to_anyJob()
    
    def maimai_upload(self,pid,hid):
        lp_strategy = self.strategy.get_lp_payload_inner()
        mm_strategy = MMStrategy()
        mm_strategy.load_from_lp(lp_strategy)
        page_index = 0
        _PAGE_SIZE = 30
        total = self.mm_service.search_candidate(mm_strategy,page_index,_PAGE_SIZE)['total']
        if not int(total):
            return

        while page_index * _PAGE_SIZE < self.limit_count:
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
                resume = self.mm_service.get_resume(mm_uid)['data']
                candidate = Candidate.from_mm_raw_resume(resume,pid,hid)
                candidate.upload_screening_resume_to_anyJob()

    def zhilian_upload(self,pid,hid):
        lp_strategy = self.strategy.get_lp_payload_inner()
        zl_strategy = zhilian_search_conditon.from_liepin_condition(lp_strategy)
        cur_page = 0
        resp = self.zl_service.get_resumes(zl_strategy, cur_page=cur_page)
        current_candidate_list = []
        while cur_page * 20 < self.limit_count:
            random_sleep()
            if not resp.get("data", {}).get("list", {}):
                break
            response = self.zl_service.get_resumes(zl_strategy, cur_page=cur_page)
            candidate_list = response['data']['list']
            current_candidate_list = [*current_candidate_list, *candidate_list]
        for resume in current_candidate_list:
            candidate = Candidate.from_zl_raw_resume(resume, pid, hid)
            candidate.upload_screening_resume_to_anyJob()




