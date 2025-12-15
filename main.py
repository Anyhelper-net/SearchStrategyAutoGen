"""
@describe:
@fileName: main.py
@time    : 2025/11/27 上午11:03
@author  : duke
"""
import argparse
import src.config as cfg

parser = argparse.ArgumentParser()
parser.add_argument('--dev', '-d', action='store_true')
parser.add_argument('--pycharm', action='store_true')
args = parser.parse_args()
cfg.IS_PYCHARM = args.pycharm
cfg.IS_DEV = args.dev

from src import *

if __name__ == '__main__':
    app.run(
        debug=False,  # 调试
        host='0.0.0.0',  # ip
        port=PORT,  # 端口
        # ssl_context='adhoc',  # 默认SSL证书，实现https
        threaded=True,  # 多线程
    )
