import json
import os

from couyun import CI_LIST, CI_LONG, CI_INDEX

with open(CI_INDEX, 'r', encoding='utf-8') as f:
    ci_idx = json.load(f)


def search_ci(input_name: str, ci_pu: int) -> str:
    """
    从词牌名称，在词牌索引中读取编号。或者通过编号读取词牌名。
    Args:
        input_name: 词牌实际名称或编号
        ci_pu: 给定的词谱
    Returns:
        词牌的编号值（字符串）或编号值对应的词牌名，如果没有，返回None
    """
    for single_ci in ci_idx:
        if input_name in single_ci['names'] or input_name in single_ci['names_trad']:
            if ci_pu == 1:
                return single_ci['idx']
            else:
                if single_ci['long_exist']:
                    return single_ci['idx']
                return 'err2'
    return 'err1'


def ci_type_extraction(ci_number: str | int, ci_pu: int) -> list[dict]:
    base = CI_LIST if ci_pu == 1 else CI_LONG
    last = '' if ci_pu == 1 else '_long'
    file_name = f'cipai_{ci_number}{last}.json'
    file_path = os.path.join(base, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
