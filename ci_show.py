"""韵脚的所有信息整合为数据框"""

import new_rhythm as nw
from collections import Counter
from num_to_cn import num_to_cn
from typing import List, Dict


class YunData:
    def __init__(self, pos: int, hanzi: str, yun_num: List[int]):
        self.pos = pos
        self.hanzi = hanzi
        self.yun_num = yun_num
        self.xie_yun = False
        self.group = None
        self.is_yayun = False


class YunDataProcessor:
    def __init__(self, yun_jiao_pos: List[int], yun_list: List[str], yun_jiao_class: Dict, yun_num_list: List[List[int]]):
        self.yun_data = [
            YunData(pos, hanzi, yun_num)
            for pos, hanzi, yun_num in zip(yun_jiao_pos, yun_list, yun_num_list)
        ]
        self.yun_jiao_class = yun_jiao_class
        self.xie_yun_map = {}
        self.group_map = {}
        self.group_most_common = {}

        for group, positions in yun_jiao_class.items():
            for p in positions:
                absolute_p = abs(p)
                self.xie_yun_map[absolute_p] = p < 0
                self.group_map[absolute_p] = group

    def process(self):
        for yun in self.yun_data:
            yun.xie_yun = self.xie_yun_map.get(yun.pos, False)
            yun.group = self.group_map.get(yun.pos, None)

        group_min_pos = {}
        for yun in self.yun_data:
            if yun.group is not None:
                group_min_pos[yun.group] = min(
                    group_min_pos.get(yun.group, yun.pos), yun.pos)

        sorted_groups = sorted(group_min_pos.items(), key=lambda x: x[1])
        new_group_map = {group: idx + 1 for idx, (group, _) in enumerate(sorted_groups)}

        for yun in self.yun_data:
            if yun.group is not None:
                yun.group = new_group_map[yun.group]

        for group_name in set(yun.group for yun in self.yun_data):
            elements = []
            for yun in self.yun_data:
                if yun.group == group_name:
                    yun_num = yun.yun_num
                    if yun.xie_yun:
                        yun_num = [-num for num in yun_num]
                    elements.extend(yun_num)
            if elements:
                counter = Counter(elements)
                most_common_element = counter.most_common(1)[0][0]
                self.group_most_common[group_name] = most_common_element
            else:
                self.group_most_common[group_name] = None

        for yun in self.yun_data:
            most_common = self.group_most_common.get(yun.group)
            if most_common is not None:
                yun_num = yun.yun_num
                if yun.xie_yun:
                    yun_num = [-num for num in yun_num]
                if most_common in yun_num:
                    yun.is_yayun = True

        result = []
        for yun in self.yun_data:
            result.append({
                'pos': yun.pos,
                'hanzi': yun.hanzi,
                'yun_num': yun.yun_num,
                'xie_yun': yun.xie_yun,
                'group': yun.group,
                'is_yayun': yun.is_yayun,
            })
        return result


def yun_data_process(yun_jiao_pos: List[int], yun_list: List[str], yun_jiao_class: Dict, yun_num_list: List[List[int]]):
    processor = YunDataProcessor(yun_jiao_pos, yun_list, yun_jiao_class, yun_num_list)
    return processor.process()


def ci_yun_list_to_hanzi_yun(yun_list: list[int], yun_shu: int):
    """
    将数字表示的韵部转换为汉字表示的韵部
    Args:
        yun_list: 单个字的韵数字代码列表
        yun_shu: 使用的韵书代码
    Returns:
        汉字表示的韵部
    """
    yun_shu = int(yun_shu)
    if yun_shu == 1:
        hanzi_yun_list = []
        for i in yun_list:
            if i < 0:
                i = -i
                ping_ze = '仄'
            else:
                ping_ze = '入声' if i > 14 else '平'
            hanzi_yun_list.append(num_to_cn(i) + '部' + ping_ze)
        return '、'.join(hanzi_yun_list)
    elif yun_shu == 2:
        return nw.show_yun(yun_list, nw.xin_yun, nw.xin_hanzi)
    return nw.show_yun(yun_list, nw.tong_yun, nw.tong_hanzi)


def yun_right_list(ci_seperate_lis: list[str], ci_content_right: list[bool | str]):
    """
    根据分割好的词列表以及布尔平仄正误列表得到分割好的字符串平仄正误列表
    Args:
        ci_seperate_lis: 分割好的词列表
        ci_content_right: 布尔平仄正误列表
    Returns:
        分割好的字符串平仄正误列表
    """
    conversion = {True: '〇', 'duo': '中', False: '错'}
    result_list = []
    ptr = 0

    for poem in ci_seperate_lis:
        non_space_chars = [c for c in poem if c != '\u3000']
        non_space_count = len(non_space_chars)
        sub_right = ci_content_right[ptr:ptr + non_space_count]
        converted = []
        j = 0
        for char in poem:
            if char == '\u3000':
                converted.append('\u3000')
            else:
                converted_char = conversion.get(sub_right[j], sub_right[j])
                converted.append(converted_char)
                j += 1
        ptr += non_space_count
        result_list.append(''.join(converted))
    return result_list
