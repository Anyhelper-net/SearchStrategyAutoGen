"""
@describe:
@fileName: manual_acc.py
@time    : 2025/11/27 上午11:04
@author  : duke
"""
import traceback

import src.config as cfg

cfg.IS_PYCHARM = True

from src.service.ss_generator import Generator
import json

if __name__ == '__main__':
    print('lp_cookies file path:')
    with open(input().strip('"'), 'r') as f:
        lp_cookies = json.load(f)
    print('mm_cookies file path:')
    with open(input().strip('"'), 'r') as f:
        mm_cookies = json.load(f)
    print('zl_cookies file path:')
    with open(input().strip('"'), 'r') as f:
        zl_cookies = json.load(f)

    while True:
        try:
            print('position id:')
            pid = int(input())
            generator = Generator(pid,lp_cookies,mm_cookies,zl_cookies)
            generator.run()
        except:
            traceback.print_exc()
