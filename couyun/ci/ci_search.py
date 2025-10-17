import json
from couyun.ui.paths import CI_LIST, CI_LONG

idx_file = CI_LIST / 'ci_index.json'
with idx_file.open(encoding='utf-8') as f:
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
    """
    提取此编号词牌的格式，不同的格式以两行存储。
    Args:
        ci_number: 词牌的编号值
        ci_pu: 选择的词谱
    Returns:
        词牌所有格式的列表，列表中的列表包含每一个格式的例词内容，格律和词牌描述。
    """
    base = CI_LIST if ci_pu == 1 else CI_LONG
    last = '' if ci_pu == 1 else '_long'
    file_path = base / f'cipai_{ci_number}{last}.json'
    with file_path.open('r', encoding='utf-8') as file:
        return json.load(file)
