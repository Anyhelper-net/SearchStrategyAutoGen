"""
----------------------------------------------------
 File Name:        regex_utils
 Author:           hoges
 Created Date:     2025/9/22
 Last Modified:    2025/9/22
 Python Version:   
----------------------------------------------------
"""

from typing import List
from src.utils.regex_patterns import *


class RegexUtils:
    @staticmethod
    def extract_recommendation(text: str) -> List[str]:
        return ResumePatterns.RECOMMENDATION_PATTERN.findall(text)
    @staticmethod
    def extract_salary(text: str) -> List[str]:
        return ResumePatterns.SALARY_PATTERN.findall(text)
    @staticmethod
    def extract_location(text: str) -> List[str]:
        return ResumePatterns.LOCATION_PATTERN.findall(text)
    @staticmethod
    def extract_tags(text: str) -> List[str]:
        return ResumePatterns.TAGS_PATTERN.findall(text)
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        将文件名中的非法 Windows 字符替换为下划线，并移除末尾的空格或点。
        """
        # 替换 <>:"/\\|?* 以及控制字符
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
        # 移除末尾的空格和点（Windows 不允许）
        name = name.rstrip(' .')
        return name
    @staticmethod
    def clean_chat_history(chat_text:str) -> str:
        lines = []
        for line in chat_text.splitlines():
            stripped_line = line.strip()
            if not line.strip():
                continue  # 跳过空行
            # 包含任意一个跳过短语就忽略
            if any(phrase in stripped_line for phrase in clean_chat_word.SKIP_CHAT):
                continue
            lines.append(line)

        return '\n'.join(lines)

    @staticmethod
    def get_position_id(web_str:str) -> str:
        match = position_patterns.GET_POSITION_ID_BY_WEB_ELEMENT_PATTERN.search(web_str)
        return match.group(1)

    @staticmethod
    def get_img_uuid(img_str:str) -> str:
        match = session_img_patterns.GET_SESSION_IMG_PATTERN.search(img_str)
        return match.group(1)

if __name__ == '__main__':
    text = RegexUtils.extract_salary('''# 候选人姓名：任先生

**年龄**：49岁
**性别**：男
**求职意向**：离职-正在找工作
**期待薪资**：25K-35K/月
**居住地**：上海 浦东新区
**学历**：硕士

**推荐语**：
具有25年丰富嵌入式软件及电控系统开发经验，精通STM32系列芯片及FOC算法，擅长电机驱动及智能家电控制系统设计，具备多项目主导经验，熟悉Linux+LVGL及多种通信协议，能高效完成复杂系统软硬件设计与调试。

---''')
