"""
@describe:
@fileName: manual_acc.py
@time    : 2025/11/27 上午11:04
@author  : duke
"""
import traceback

import src.config as cfg

# cfg.IS_PYCHARM = True

from src.service.ss_generator import Generator
import json

if __name__ == '__main__':
    print('cookies file path:')
    with open(input().strip('"'), 'r') as f:
        cookies = json.load(f)

    while True:
        try:
            print('position id:')
            pid = int(input())
            generator = Generator(cookies, pid)
            generator.run()
        except:
            traceback.print_exc()
