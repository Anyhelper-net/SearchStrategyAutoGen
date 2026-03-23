import json
import os.path
from pathlib import Path


def get_zhlian_code_by_liepin_dqname(dq_name,kind):
    with open(os.path.join(Path(__file__).parents[2] / 'resource',f'zhilian_{kind}_code.json'), "r", encoding="utf-8") as f:
        kind_list = json.load(f)
    for kind in kind_list['data']:
        if kind['label'] == dq_name:
            return kind['value']
        for region_children in kind['children']:
            if region_children['label'] == dq_name:
                return kind['value']