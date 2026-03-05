"""
----------------------------------------------------
 File Name:        Candidate
 Author:           hoges
 Created Date:     2025/9/22
 Last Modified:    2025/9/22
 Python Version:   
----------------------------------------------------
"""
import json
from pathlib import Path
from typing import Union

import src.io.bot as bot_io
from datetime import datetime
from src.io.anyhelper import get_job_data, duplicate_screening, add_screening_resume, \
    h5_post, get_user_role, get_ah_result_dict
from src.config.anyhelper import ENUM_CANDIDATE_CLASSIFY
from src.config.bot import ENUM_MODEL_ID
from src.utils.regex_utils import RegexUtils


class Candidate:
    def __init__(
            self,
            name,
            currentCompany,
            currentPosition,
            schoolName,
            major,
            rawResume: str,
            salary,
            position_id,
            incharge_id,
            now_region,
            gold_collar=None,
            link: str = "",
            recentActiveTime: datetime = None,
    ):
        """
        execl列头
        name:简历获取
        current company : 简历最后一段经历获取
        current position : 简历最后一段经历获取
        link : 无
        liepin key words : 公司加岗位加学校加专业
        resume : bot清洗, VEgxZGZtSHFGS0YwOGpnY0pIL3d0QT09 ,简单简历关键字清洗(对应simple_resume)
        salary : 从resume里面拿取
        comment :  firstCheckComment (这里不存推荐语,推荐语上传的时候添加)
        comment_simplified : firstCheckCommentLabel
        gold collar : 简历里面有一个值是resumeLevel
        raw resume : 简历里有resume.language
        note : 放空
        time_stamp : 当前时间戳
        事实判断是否 : 二次判断的label
        事实判断 : 二次判断的原始值
        是否重复 : 查重结果(Yes,No)
        上传情况 : 上传后填入,是否上传看二次判断label
        最近活跃时间 : 简历里有lastActiveTime
        """

        self.resume_id = None
        self.is_duplicate_with_current_position = False
        self.name = name

        self.currentCompany = currentCompany
        self.currentPosition = currentPosition
        self.link = link
        self.schoolName = schoolName
        self.major = major
        self.liepin_keywords = f'{currentCompany} {currentPosition} {schoolName} {major}'

        self.rawResume = rawResume

        self.simple_resume = ''

        self.salary = salary

        self.position_id = position_id
        self.incharge_id = incharge_id

        self.job_requirement = ''
        self.job_deep_requirement = ''

        self.firstCheckComment = ""
        self.firstCheckCommentLabel = ""

        self.gold_collar = gold_collar
        self.time_stamp = datetime.now()
        self.note = ''

        self.fact_check_comment = ''
        self.fact_check_comment_label = ''

        self.now_region = now_region

        self.is_clients = False

        self.is_duplicate = False
        self.is_duplicate_pass = False
        self.duplicate_position_id_list = []
        self.duplicate_position_name_list = []

        self.recentActiveTime = recentActiveTime

    def set_simple_resume(self):
        self.simple_resume = bot_io.send(self.rawResume, ENUM_MODEL_ID.GET_SIMPLE_RESUME)

    def set_job_requirement(self):
        self.job_requirement = get_ah_result_dict(get_job_data(self.position_id))['results'][0][
            'summary']
        self.job_deep_requirement = self.job_requirement.split('深匹要求：')[1]

    def set_first_check(self):
        self.set_job_requirement()

        self.firstCheckComment = bot_io.send(f'【个人信息：】{self.rawResume}【岗位要求：】{self.job_deep_requirement}',
                                              ENUM_MODEL_ID.GET_FIRST_CHECK)
        if self.firstCheckComment.find("非常匹配") >= 0:
            self.firstCheckCommentLabel = "非常匹配"
            return
        if self.firstCheckComment.find("不匹配") >= 0:
            self.firstCheckCommentLabel = "不匹配"
            return
        if self.firstCheckComment.find("匹配") >= 0:
            self.firstCheckCommentLabel = "匹配"
            return

    def set_fact_check(self):

        self.set_first_check()

        self.fact_check_comment = bot_io.send(
            f'【requirements：岗位要求】{self.job_deep_requirement}【name ：候选人名字】{self.name}【comment: 判断结果和原因】{self.firstCheckComment}【raw resume：候选人简历】{self.rawResume}',
            ENUM_MODEL_ID.GET_FACT_CHECK)
        if '不匹配' in self.fact_check_comment:
            self.fact_check_comment_label = '不匹配'
        elif '非常匹配' in self.fact_check_comment:
            self.fact_check_comment_label = '非常匹配'
        else:
            self.fact_check_comment_label = '匹配'

    def check_screening_is_duplicate_with_keywords(self):
        duplicate_response = get_ah_result_dict(duplicate_screening(self.liepin_keywords,self.incharge_id))
        if 'yes' == duplicate_response['duplicate']:
            self.is_duplicate = True

            for duplicate_position in duplicate_response['records']:
                self.duplicate_position_id_list.append(duplicate_position['position_id'])
                self.duplicate_position_name_list.append(duplicate_position['Position'])

            for index, duplicate_position_id in enumerate(self.duplicate_position_id_list):
                # 如果当前上传的岗位中的人才冲突了,跳过
                if str(duplicate_position_id) == self.position_id:
                    self.is_duplicate_pass = True
                    self.is_duplicate_with_current_position = True
                    self.resume_id = duplicate_response['records'][index]['id']

            # 如果当前岗位是客户岗位
            if self.is_clients:
                self.is_duplicate_pass = True

        else:
            self.is_duplicate_pass = False

    def check_is_clients(self):
        if 'client' == get_ah_result_dict(get_user_role(self.incharge_id))['type']:
            self.is_clients = True
        else:
            self.is_clients = False

    def upload_screening_resume_to_anyJob(self):
        self.check_is_clients()

        self.check_screening_is_duplicate_with_keywords()

        # 查重
        if self.is_duplicate_pass:
            return

        self.set_fact_check()

        # 事实判断
        if self.fact_check_comment_label == '不匹配':
            return

        clean_resume = bot_io.send(self.rawResume, ENUM_MODEL_ID.GET_CLEAN_RESUME)

        # 判断是否是客户,做备注拼接逻辑
        recommendation = RegexUtils.extract_recommendation(clean_resume)
        if self.is_clients:
            comment = f"{self.fact_check_comment_label}，{recommendation[0]}"
        else:
            # 如果不是客户岗位
            # 重复了
            if self.is_duplicate:
                if self.duplicate_position_name_list:
                    comment = f"重复：{'，'.join(self.duplicate_position_name_list)}" + '，' + f'{self.fact_check_comment}'
                else:
                    comment = f"重复：但是无具体岗位" + '，' + f'{self.fact_check_comment}'
            else:
                comment = f"{self.fact_check_comment_label}，{'，'.join(self.fact_check_comment.split('，')[3:])}"

        self.set_simple_resume()

        salary = RegexUtils.extract_salary(clean_resume)

        location = RegexUtils.extract_location(clean_resume)

        tags = RegexUtils.extract_tags(clean_resume)


        # 每判断一个合适上传人才，h5发帖一次
        h5_post(self.position_id, '发现匹配人才', f'姓名：{"猎聘 " + self.name} 匹配原因：{comment}')

        if self.gold_collar:
            source = ENUM_CANDIDATE_CLASSIFY.LIE_PIN_GOLD.value
        else:
            source = ENUM_CANDIDATE_CLASSIFY.LIE_PIN.value

        params = {
            'name': self.name,
            'liepin_keywords': self.liepin_keywords,
            'current_company': self.currentCompany,
            'current_position': self.currentPosition,
            'resume_content': clean_resume,
            'ai_summary': self.simple_resume,
            'comment': comment,
            'source': source
        }

        if self.recentActiveTime:

            last_active_timestamp = self.recentActiveTime

            active_time_str = last_active_timestamp.strftime("%Y-%m-%d")

            params['activity_time'] = active_time_str
        if salary:
            params['salary'] = salary[0]
        if location:
            params['location'] = location[0]
        if tags:
            params['tags'] = tags[0]

        response = add_screening_resume(
            position_id=self.position_id,
            incharge_id=self.incharge_id,
            status='待联系',
            coins_cost=2,
            **params
        )
        pass

    @classmethod
    def from_raw_resume(cls, base_info_dict, work_exp_dict, position_id, incharge_id=None):
        """
        base_info_dict : 第一个 JSON 的 data 字段
        work_exp_dict  : 第二个 JSON 的 data 字段（数组）
        """

        name = base_info_dict.get("showName", "") or ""

        active_time_str = base_info_dict.get("activeTime")  # "2025/12/10"
        recentActiveTime = None
        if isinstance(active_time_str, str):
            try:
                dt = datetime.strptime(active_time_str, "%Y/%m/%d")
                # 转换为 13 位时间戳再恢复 datetime
                ts_13 = int(dt.timestamp() * 1000)
                recentActiveTime = datetime.fromtimestamp(ts_13 / 1000)
            except Exception:
                recentActiveTime = None


        work_list = work_exp_dict if isinstance(work_exp_dict, list) else []
        first_work = work_list[0] if len(work_list) > 0 else {}

        currentCompany = first_work.get("rwCompname", "") or ""
        currentPosition = first_work.get("rwTitle", "") or ""


        edu_list = base_info_dict.get("eduExpFormList") or []
        first_edu = edu_list[0] if len(edu_list) > 0 else {}

        schoolName = first_edu.get("redSchool", "") or ""
        major = first_edu.get("redSpecial", "") or ""


        purposes = base_info_dict.get("resExpectInfoDtos") or []
        first_purpose = purposes[0] if len(purposes) > 0 else {}

        salary = first_purpose.get("wantSalaryShow", "") or ""
        if salary:
            salary = bot_io.send(salary,ENUM_MODEL_ID.GET_CLEAN_SALARY)

        now_region = base_info_dict.get('basicInfoForm').get('dqName','')

        raw_resume = {
            "base": base_info_dict,
            "workExp": work_exp_dict
        }

        raw_resume_str = json.dumps(raw_resume, ensure_ascii=False)


        return cls(
            name=name,
            currentCompany=currentCompany,
            currentPosition=currentPosition,
            schoolName=schoolName,
            major=major,
            rawResume=raw_resume_str,
            salary=salary,
            position_id=position_id,
            incharge_id=incharge_id,
            recentActiveTime=recentActiveTime,
            now_region=now_region
        )

    def to_excel_row(self, filepath: Union[str, Path]):
        filepath = Path(filepath)

        if filepath.exists():
            # ✅ 文件存在：加载并追加数据行
            generator = excel_generator(filepath)
            generator.add_data_object_row(self, EXECL_ATTRIBUTES)
            generator.save()
        else:
            # ✅ 文件不存在：新建文件并写入表头
            generator = excel_generator(filepath)
            generator.set_headers(EXECL_HEADER)  # 仅第一次写表头
            generator.add_data_object_row(self, EXECL_ATTRIBUTES)
            generator.save()



if __name__ == "__main__":
    pass
