import json
import traceback
from src.service.ss_generator import Generator


if __name__ == '__main__':
    print('cookies file path:')
    with open(input().strip('"'), 'r') as f:
        cookies = json.load(f)

    while True:
        try:
            print('position id list (split by ,):')
            pids = input().split(",")
            for pid in pids:
                generator = Generator(cookies, pid)
                generator.run()
        except:
            traceback.print_exc()
