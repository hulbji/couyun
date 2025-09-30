import json
import os
from opencc import OpenCC
from common import current_dir

idx_file = os.path.join(current_dir, 'ci_list', 'ci_index.json')

with open(idx_file, encoding='utf-8') as f:
    idx = json.load(f)


def search_ci(input_name: str, ci_pu: int, reverse_search=False, traditial=False) -> str:
    """
    从词牌名称，在词牌索引中读取编号。或者通过编号读取词牌名。
    Args:
        input_name: 词牌实际名称或编号
        ci_pu: 给定的词谱。
        reverse_search: 是否反向搜索，通过编号读取词牌名。
        traditial: 是否为繁体
    Returns:
        词牌的编号值（字符串）或编号值对应的词牌名，如果没有，返回None
    """
    if traditial:
        cc = OpenCC('t2s')
        input_name = cc.convert(input_name)
    if reverse_search:
        return idx[int(input_name)]['names'][0]
    else:
        for single_ci in idx:
            if input_name in single_ci['names']:
                if ci_pu == 1:
                    return single_ci['idx']
                else:
                    file_path = os.path.join(current_dir, 'ci_long', f'cipai_{single_ci["idx"]}_long.json')
                    if os.path.exists(file_path):
                        return single_ci['idx']
                    return 'err2'
        return 'err1'


def ci_type_extraction(ci_number: str | int, ci_pu: int) -> list[dict]:
    """
    提取此编号词牌的格式，不同的格式以两行存储。
    Args:
        ci_number: 词牌的编号值
        ci_pu: 选择的词谱
    Returns:
        词牌所有格式的列表，列表中的列表包含每一个格式的例词内容，格律和词牌描述。
    """
    middle = 'ci_list' if ci_pu == 1 else 'ci_long'
    last = '' if ci_pu == 1 else '_long'
    file_path = os.path.join(current_dir, middle, f'cipai_{ci_number}{last}.json')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = json.load(file)
    return content
