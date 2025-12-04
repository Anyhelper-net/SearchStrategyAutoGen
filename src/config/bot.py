"""
@describe:
@fileName: bot.py
@time    : 2025/10/9 11:08
@author  : duke
"""
from enum import Enum

API_MODELS = 'https://chat.anyhelper.net/api/completions/quora.php'


class ENUM_MODEL_ID(Enum):
    REQUIREMENT_PARSER = 'V2JRaTJWUU5IR3ZKSG9HQnZHNDFQUT09'
    JOBINFO_PARSER = 'WURTVkZEbStwT1A4OEhzdVJWNC9Pdz09'


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
