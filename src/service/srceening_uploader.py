
from src.model import SearchStrategy
from src.model.candidate import Candidate
from src.service.lp import LpService
import json


class ScreeningUploader:
    def __init__(self,lp_service,strategy):
        self.lp_service:LpService = lp_service
        self.strategy:SearchStrategy = strategy

    def liepin_upload(self,pid,hid):
        resumes = []
        while True:
            data = self.lp_service.get_resumes(self.strategy.get_lp_payload_inner())
            tmp_resumes = data.get('data', {}).get('resList')
            if not tmp_resumes:
                break
            resumes += tmp_resumes

        for resume in resumes:
            response = self.lp_service.get_resume_detail(resume['simpleResumeForm']['resIdEncode'])

            resume_detail = json.loads(response.text)['data']

            response = self.lp_service.get_work_exp(resume_detail.get('basicInfoForm', {}).get('resJobtitle'),
                                           resume['simpleResumeForm']['resIdEncode'])

            resume_work_exp = json.loads(response.text).get('data', {})

            candidate = Candidate.from_raw_resume(resume_detail, resume_work_exp, pid, hid)

            if resume_detail.get('goldUser', False):
                candidate.gold_collar = True

            candidate.upload_screening_resume_to_anyJob()



