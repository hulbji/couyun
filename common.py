"""一些都会用到的通用模块。"""

from pingshui_rhythm import hanzi_rhythm
import new_rhythm as nw
import os
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
cn_nums = {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}


def show_all_rhythm(single_hanzi: str) -> str:
    """
    给定一个汉字，返回其平水、词林、新韵、通韵韵部。
    Args:
        single_hanzi: 单个汉字
    Returns:
        平水、词林、新韵、通韵韵部
    """
    result = ''
    result += hanzi_rhythm(single_hanzi, showit=True)
    result += '\n中华新韵'
    result += nw.show_yun(single_hanzi, nw.xin_yun, nw.xin_hanzi) + '\n'
    result += '\n中华通韵'
    result += nw.show_yun(single_hanzi, nw.tong_yun, nw.tong_hanzi) + '\n'
    return result


def hanzi_to_yun(hanzis: str, yun_shu: int, ci_lin=False) -> list[list[int]]:
    """
    将一串汉字对应为韵书中韵部的嵌套列表。
    Args:
        hanzis: 一串汉字
        yun_shu: 使用韵书的代码
        ci_lin: 是否输出词林韵部
    Returns:
        所有汉字韵部列表的列表
    """
    rhythm_lists = []
    for hanzi in hanzis:
        if yun_shu == 1:
            if ci_lin:
                rhythm_lists.append(hanzi_rhythm(hanzi, ci_lin=True))
            else:
                rhythm_lists.append(hanzi_rhythm(hanzi))
        elif yun_shu == 2:
            rhythm_lists.append(nw.convert_yun(nw.get_new_yun(hanzi), nw.xin_yun))
        else:
            rhythm_lists.append(nw.convert_yun(nw.get_new_yun(hanzi), nw.tong_yun))
    return rhythm_lists


def result_check(post_result: str, temp_result: str) -> str:
    """
    如果一首诗、词可能对应多个结构，需要排查整体的结果，根据平仄和押韵符合字数的多少，是否押更多的韵数，是否有更少的韵种类，确定一个最接近的。
    Args:
        post_result: 上一个校验的结果
        temp_result: 目前校验的结果
    Returns:
        两者中更匹配的结果
    """
    if post_result == '':
        return temp_result
    post_count, post_yayun_count, post_yayun_type = count_poem_para(post_result)
    temp_count, temp_yayun_count, temp_yayun_type = count_poem_para(temp_result)
    if temp_count > post_count:
        return temp_result
    if temp_count == post_count:
        if post_yayun_count > temp_yayun_count:
            return post_result
        if post_yayun_count == temp_yayun_count:
            if temp_yayun_type > post_yayun_type:
                return post_result
            return temp_result
        return temp_result
    return post_result


def count_poem_para(string: str) -> tuple[int, int, int]:
    """
    对一个校验结果的字符串，检测其总正确平仄数、押韵数、韵种类
    Args:
        string: 验结果的字符串
    Returns:
        返回三个值：
            总正确平仄数
            押韵数
            韵种类
    """
    matches = re.findall(r'第([一二三四五六七八九十])组韵', string)
    if matches:
        yun_nums = [cn_nums[cn_num] for cn_num in matches]
        yun_types = max(yun_nums)
    else:
        yun_types = 1
    total_count = yayun_count = 0
    lines = string.split('\n')
    for line in lines:
        if '〇' in line:
            total_count += line.count('〇') + line.count('中')
        if '不押韵' in line:
            total_count -= 1
        if '押韵' in line:
            yayun_count += 1
    return total_count, yayun_count, yun_types
