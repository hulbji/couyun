"""韵脚的所有信息整合为数据框"""

import pandas as pd
import new_rhythm as nw
from collections import Counter
from num_to_cn import num_to_cn


def yun_data_process(yun_jiao_pos: list[int], yun_list: list[str], yun_jiao_class: dict,
                     yun_num_list: list[list[int]]) -> pd.DataFrame:
    """
    根据韵脚位置、韵脚列表、韵脚分类、每个字的韵数字代码列表组成的列表
    构造包含韵位置、韵脚汉字、每个字的韵数字代码列表、是否为叶韵、韵组别、是否正确押韵的数据框
    Args:
        yun_jiao_pos: 韵脚位置
        yun_list: 韵脚列表
        yun_jiao_class: 韵脚分类
        yun_num_list: 每个字的韵数字代码列表组成的列表
    """
    df = pd.DataFrame({
        "pos": yun_jiao_pos,
        "hanzi": yun_list,
        "yun_num": yun_num_list  # 直接添加列表
    })
    xie_yun_map = {}
    group_map = {}
    for group, positions in yun_jiao_class.items():
        for p in positions:
            absolute_p = abs(p)
            xie_yun_map[absolute_p] = p < 0
            group_map[absolute_p] = group

    df["xie_yun"] = df["pos"].map(lambda x: xie_yun_map.get(x, False))
    df["group"] = df["pos"].map(lambda y: group_map.get(y, None))

    group_min_pos = df.groupby("group")["pos"].min().reset_index()
    group_min_pos_sorted = group_min_pos.sort_values(by="pos", ascending=True)
    group_min_pos_sorted["new_group"] = range(1, len(group_min_pos_sorted) + 1)
    df = df.merge(group_min_pos_sorted[["group", "new_group"]], on="group", how="left")
    df["group"] = df["new_group"]
    df.drop(columns=["new_group"], inplace=True)

    df["is_yayun"] = False
    group_most_common = {}
    for group_name, group_data in df.groupby("group"):
        elements = []
        for index, row in group_data.iterrows():
            yun_num = row['yun_num']
            xie_yun = row['xie_yun']
            if xie_yun:
                processed = [-num for num in yun_num]
            else:
                processed = yun_num
            elements.extend(processed)
        if elements:
            counter = Counter(elements)
            most_common_element = counter.most_common(1)[0][0]
            group_most_common[group_name] = most_common_element
        else:
            group_most_common[group_name] = None

    for index, row in df.iterrows():
        group = row['group']
        most_common = group_most_common.get(group)
        if most_common is not None:
            yun_num = row['yun_num']
            xie_yun = row['xie_yun']
            processed = [-num for num in yun_num] if xie_yun else yun_num
            if most_common in processed:
                df.at[index, "is_yayun"] = True
    return df


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
