"""
@describe:
@fileName: bot.py
@time    : 2025/10/9 11:08
@author  : duke
"""
from enum import Enum

API_MODELS = 'https://chat.anyhelper.net/api/completions/quora.php'


class ENUM_MODEL_ID(Enum):
    REQUIREMENT_PARSER = 'ZE1aLzJUTkhPYnd3ZEpVYmx4UzFvZz09'
    JOBINFO_PARSER = 'MFAwRmFPbXA5MVF6YmNTVDBjc0NmZz09'
    STRATEGY_NAME_GEN = 'c2tNWDlmRGwwbWduMjNETy95alRzZz09'
    COMP_RANGE2NAMES = 'N2dwOGRRWExrU0hxeXUrMG56ZU1SQT09'


BOT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded;",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}
