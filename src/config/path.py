"""
@describe:
@fileName: path.py
@time    : 2025/10/10 16:18
@author  : duke
"""
import os
import sys

import src.config as cfg

ROOT_PATH = None
WEB_PATH = None
LOG_DIR = None
RSC_DIR = None

if cfg.IS_PYCHARM:
    # ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    ROOT_PATH = r'D:\Workspace\project\AnyHelper\SearchStrategyAutoGen'
else:
    ROOT_PATH = os.path.dirname(os.path.abspath(sys.executable))

if cfg.IS_PYCHARM:
    WEB_PATH = os.path.join(ROOT_PATH, 'web_gui/dist')
else:
    WEB_PATH = os.path.join(ROOT_PATH, 'dist')

LOG_DIR = os.path.join(ROOT_PATH, 'log')
RSC_DIR = os.path.join(ROOT_PATH, 'resource')

print(f'Root Path: {ROOT_PATH}\n')
