"""
@describe:
@fileName: api.py
@time    : 2025/12/15 上午10:23
@author  : duke
"""

from flask import Flask, render_template, request
import src.config
from src.config.path import WEB_PATH
import logging

if not src.config.IS_DEV:
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__,
            static_folder=WEB_PATH,
            template_folder=WEB_PATH,
            static_url_path='')

# @app.route('/')
# def index():
#     return render_template('index.html', name='index')
