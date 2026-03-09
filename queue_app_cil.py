import json
import traceback
from src.service.ss_generator import Generator


if __name__ == '__main__':
    print('lp_cookies file path:')
    with open(input().strip('"'), 'r') as f:
        lp_cookies = json.load(f)
    print('mm_cookies file path:')
    with open(input().strip('"'), 'r') as f:
        mm_cookies = json.load(f)

    while True:
        try:
            print('position id list (split by ,):')
            pids = input().split(",")
            for pid in pids:
                generator = Generator(pid,lp_cookies,mm_cookies)
                generator.run()
        except:
            traceback.print_exc()
