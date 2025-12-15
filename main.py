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
    client = Client()
    client.ws.run_forever()

    # app.run(
    #     debug=False,
    #     host='0.0.0.0',
    #     port=23332,
    #     # ssl_context='adhoc',
    #     threaded=True,
    # )
