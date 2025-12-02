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

from src.config.path import *
