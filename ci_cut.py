"""分割词牌、词内容的相关代码。"""


def split_cipai_text(cipai_text: str, yun_jiao_places: list) -> list:
    """
    根据例词内容以及韵脚位置，分割例词。
    Args:
        cipai_text: 带有空白的例词内容
        yun_jiao_places: 除去空白的韵脚位置
    Returns:
        例词根据韵脚位置分割成的列表
    """
    count = 0
    cut_str = ''
    cut_list = []
    for i in range(len(cipai_text)):
        char = cipai_text[i]
        cut_str += char
        if count in yun_jiao_places and char != '\u3000':
            cut_list.append(cut_str.lstrip())
            cut_str = ''
        if char != '\u3000':
            count += 1
    return cut_list


def split_yun_str_by_ci(ci_list: list[str], yun_str: str, yun_list: list[str], ci_num: int) -> list[str]:
    """
    通过分割好的例词列表，原始的词格律字符串，韵的标识列表，词牌代号，拆分原始的词格律字符串使其与分割好的例词列表匹配。
    Args:
        ci_list: 分割好的例词列表
        yun_str: 词格律字符串
        yun_list: 韵的标识列表
        ci_num: 词牌代号
    Returns:
        分割成的词格律列表
    """
    ci_lengths = [len(sentence) for sentence in ci_list]
    yun_cut_list = []
    remaining_yun_str = yun_str
    for i in range(len(yun_list)):
        current_length = ci_lengths[i] + len(yun_list[i])
        if ci_num in ['0', '35']:  # 特殊处理竹枝和采莲曲
            current_length += 3
        yun_cut = remaining_yun_str[:current_length]
        yun_cut_list.append(yun_cut)
        remaining_yun_str = remaining_yun_str[current_length:]
    return yun_cut_list


def replace_user_ci_text(user_ci_text: str, ci_cut_list: list[str]) -> list[str]:
    """
    根据输入的词内容与分割好的例词列表分割词内容。
    Args:
        user_ci_text: 输入的词内容
        ci_cut_list: 分割好的例词列表
    Returns:
        输入的词分割好的例词列表
    """
    merged_ci = ''.join(ci_cut_list)
    my_hanzi = list(user_ci_text)
    new_ci = []
    hanzi_index = 0
    for c in merged_ci:
        if c != '\u3000':
            new_ci.append(my_hanzi[hanzi_index])
            hanzi_index += 1
        else:
            new_ci.append(c)
    user_cut_text = []
    current_pos = 0
    for part in ci_cut_list:
        length = len(part)
        user_cut_text.append(''.join(new_ci[current_pos:current_pos + length]))
        current_pos += length
    return user_cut_text
