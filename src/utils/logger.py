"""
@describe:
@fileName: logger.py
@time    : 2025/12/15 上午10:27
@author  : duke
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from src.config.path import LOG_DIR
import os

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

# 创建logger
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

# 控制台Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 按时间轮转的Handler
timed_handler = TimedRotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)
timed_handler.setLevel(logging.DEBUG)

# 创建formatter
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
timed_handler.setFormatter(formatter)

# 添加handler到logger
logger.addHandler(console_handler)
logger.addHandler(timed_handler)
