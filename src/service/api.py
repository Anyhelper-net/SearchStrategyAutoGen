"""
@describe:
@fileName: api.py
@time    : 2025/12/15 上午10:23
@author  : duke
"""

from flask import Flask, render_template, request
from src.config.path import WEB_PATH
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__,
            static_folder=WEB_PATH,  # 设置静态文件夹目录
            template_folder=WEB_PATH,
            static_url_path='')  # 设置vue编译输出目录dist文件夹，为Flask模板文件目录


# @app.route('/')
# def index():
#     return render_template('index.html', name='index')
