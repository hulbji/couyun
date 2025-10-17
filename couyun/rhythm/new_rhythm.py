"""新韵模块，支持新韵和通韵。"""

import math
from couyun.common.num_to_cn import num_to_cn
from couyun.hanzi.hanzi_pinyin_class import pinyin_dict

xin_yun = {1: ['a', 'ia', 'ua'], 2: ['o', 'e', 'uo'], 3: ['ie', 'ue', 've'], 4: ['ai', 'uai'],
           5: ['ei', 'uei', 'ui'], 6: ['ao', 'iao'], 7: ['ou', 'iu', 'iou'], 8: ['an', 'ian', 'uan', 'van'],
           9: ['en', 'in', 'un', 'vn', 'uen'], 10: ['ang', 'iang', 'uang'], 11: ['ueng', 'eng', 'ing', 'ong', 'iong'],
           12: ['i', 'er', 'v'], 13: ['-i'], 14: ['u']}
tong_yun = {1: ['a', 'ia', 'ua'], 2: ['o', 'uo'], 3: ['e', 'ie', 'ue', 've'], 4: ['i', '-i'], 5: ['u'], 6: ['v'],
            7: ['ai', 'uai'], 8: ['ei', 'ui', 'uei'], 9: ['ao', 'iao'], 10: ['ou', 'iu', 'iou'],
            11: ['an', 'ian', 'uan', 'van'], 12: ['en', 'in', 'uen', 'un', 'vn'], 13: ['ang', 'iang', 'uang'],
            14: ['ueng', 'eng', 'ing'], 15: ['ong', 'iong'], 16: ['er']}

xin_hanzi = ['麻', '波', '皆', '开', '微', '豪', '尤', '寒', '文', '唐', '庚', '齐', '支', '姑']
tong_hanzi = ['啊', '喔', '鹅', '衣', '乌', '迂', '哀', '欸', '熬', '欧', '安', '恩', '昂', '英', '雍', '儿']

xin_hanzi_trad = ['麻', '波', '皆', '開', '微', '豪', '尤', '寒', '文', '唐', '庚', '齊', '支', '姑']
tong_hanzi_trad = ['啊', '喔', '鵝', '衣', '烏', '迂', '哀', '欸', '熬', '歐', '安', '恩', '昂', '英', '雍', '兒']


def get_new_yun(hanzi: str) -> list:
    """
    给定一个汉字，返回其所有韵母和声调的列表。
    Args:
        hanzi: 给定的汉字
    Returns:
        该汉字所有读音的韵母和声调的列表
    """
    return pinyin_dict.get(hanzi, [])


def convert_yun(yun_list: list, rhyme_dict: dict) -> list:
    """
    将拼音韵转换为对应的新韵或通韵韵部。
    Args:
        yun_list: 汉字所有读音的韵母和声调的列表
        rhyme_dict: 使用的新韵或通韵韵母韵部对照字典
    Returns:
        韵部的列表
    """
    converted_list = []
    for yun, pingze in yun_list:
        # 遍历字典，找到韵母对应的类别
        for category, rhymes in rhyme_dict.items():
            if yun in rhymes:
                if pingze == 0:
                    converted_list.append(category)
                else:
                    converted_list.append(-category)
                break
    return converted_list if converted_list else [107]


def new_ping_ze(yun_list: list) -> str:
    """
    根据新韵通韵返回平仄，或多音。
    Args:
        yun_list: 韵部的列表
    Returns:
        平仄结果 0多音 1平 2仄
    """
    ping = ze = False
    for converted_yun in yun_list:
        if not converted_yun[-1]:
            ping = True
        else:
            ze = True
    if not ping and not ze:
        return '3'
    return '0' if ping and ze else '1' if ping else '2'


def show_yun(hanzi: str | list, yun_rule: dict, yun_hanzi: list) -> str:
    """
    展示一个汉字或直接给定韵列表的新韵、通韵韵部。
    Args:
        hanzi: 一个汉字或直接给定的韵列表
        yun_rule: 使用的新韵或通韵韵母韵部对照字典
        yun_hanzi: 新韵或通韵韵部的部汉字
    Returns:
        汉字或列表对应的新韵、通韵韵部
    """
    if type(hanzi) is str:
        hanzi_yun_list = convert_yun(get_new_yun(hanzi), yun_rule)
    else:
        hanzi_yun_list = hanzi
    if not hanzi_yun_list or hanzi_yun_list == [107]:
        return ''
    show_list = []
    for _ in hanzi_yun_list:
        yun_num = int(math.fabs(_))
        show_list.append(num_to_cn(yun_num) + yun_hanzi[yun_num - 1] + ('仄' if _ < 0 else '平'))
    show_list = list(set(show_list))
    show_list.sort()
    return '、'.join(show_list)
