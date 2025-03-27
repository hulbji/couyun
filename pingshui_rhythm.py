"""平水韵相关模块"""

from num_to_cn import num_to_cn  # 自用数字转换汉字代码
import hanzi_class  # 平水韵表

rhythm_name = [
    '东冬江支微鱼虞齐佳灰真文元寒删先萧肴豪歌麻阳庚青蒸尤侵覃盐咸',
    '董肿讲纸尾语麌荠蟹贿轸吻阮旱潸铣筱巧皓哿马养梗迥有寝感俭豏',
    '送宋绛寘未御遇霁泰卦队震问愿翰谏霰啸效号个祃漾敬径宥沁勘艳陷',
    '屋沃觉质物月曷黠屑药陌锡职缉合叶洽'
]

rhythm_correspond = {1: 1, 2: 1, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 3, 9: [5, 10], 10: [3, 5],
                     11: 6, 12: 6, 13: [6, 7], 14: 7, 15: 7, 16: 7, 17: 8, 18: 8, 19: 8, 20: 9, 21: 10,
                     22: 2, 23: 11, 24: 11, 25: 11, 26: 12, 27: 13, 28: 14, 29: 14, 30: 14}


def traverse_lists_and_find(search_hanzi: str) -> list[list]:
    """
    查找并返回包含特定字符串的列表。
    Args:
        search_hanzi: 单个汉字
    Returns:
        在 hanzi_class.py 中包含这一汉字的所有列表的列表
    """
    matching_list = []
    for var_name in dir(hanzi_class):
        var = getattr(hanzi_class, var_name)
        if isinstance(var, list) and len(var) > 0 and isinstance(var[0], str):
            if search_hanzi in var[0]:
                matching_list.append(var)
    return matching_list


def matching_list_to_rhythm_name(matching_list: list[list]) -> list[str]:
    """
    将韵表列表转换为韵律名称。
    Args:
        matching_list: 包含某一汉字的所有列表的列表
    Returns:
        描述汉字所在韵部的列表
    """
    rhythm_name_list = []
    for single_list in matching_list:
        rh1 = abs(int(single_list[1])) - 1
        rh2 = abs(int(single_list[2])) - 1
        rh3_re = '平' if rh1 == 0 else ('仄' if rh1 in [1, 2] else '入声')
        if rh3_re == '平' and rh2 + 1 > 15:
            pingshui_rh = f'平水韵{num_to_cn((rh2 + 1) - 15)}{rhythm_name[rh1][int(abs(single_list[2])) - 1]}'
        else:
            pingshui_rh = f'平水韵{num_to_cn(rh2 + 1)}{rhythm_name[rh1][int(abs(single_list[2])) - 1]}'
        rh3 = f'词林正韵{num_to_cn(abs(int(single_list[3])))}部{rh3_re}'
        rhythm_name_list.append(pingshui_rh + '，' + rh3)
    return rhythm_name_list


def hanzi_rhythm(search_str: str, showit=False, only_ping_ze=False, ci_lin=False) -> bool | str | list:
    """
    根据汉字查找韵律信息。
    Args:
        search_str: 查询的汉字
        showit: 是否展示
        only_ping_ze: 仅告知平仄
        ci_lin: 输出词林正韵而非平水韵结果
    Returns:
        输出对应的展示或平仄或韵部的数字代码列表
    """
    matching_lists = traverse_lists_and_find(search_str)
    if showit:
        result = ''
        real_rhythm = matching_list_to_rhythm_name(matching_lists)
        result += f'{search_str}在：' + '\n'
        for rhythms in real_rhythm:
            result += rhythms + '\n'
        return result
    elif only_ping_ze:
        ping, ze = False, False
        for rh_list in matching_lists:
            if rh_list[2] > 0 and not ping:
                ping = True
            elif rh_list[2] < 0 and not ze:
                ze = True
        return '0' if ping and ze else ('1' if ping else '2')  # 0 中 1 平 2 仄
    elif ci_lin:
        return list(set(rh_list[3] for rh_list in matching_lists))
    else:
        return list(set(rh_list[4] for rh_list in matching_lists))
