"""诗歌校验模块内容，可以校验五言或七言的绝句或律诗，可以校验孤雁入群的特殊格式。支持拗救。支持三韵。"""

import time
import math
from collections import defaultdict

from pingshui_rhythm import rhythm_name, rhythm_correspond  # 平水韵模块
from common import *
from num_to_cn import num_to_cn
from shi_first import get_first_type_main  # 判断首句格式

lyu_ju_rule_dict = {
    1: ['11221', '21121', '11121'],  # 平起押韵
    2: ['01122', '11212'],  # 平起不押韵
    3: ['02211'],  # 仄起押韵
    4: ['02012', '02022'],  # 仄起不押韵（含拗句）
    5: ['0211221', '0221121', '0211121'],  # 仄起押韵
    6: ['0201122', '0211212'],  # 仄起不押韵
    7: ['0102211'],  # 平起押韵
    8: ['0102012', '0102022']  # 平起不押韵（含拗句）
}  # 一定要将拗句放在后检验

sh = ['〇', '错', '中']  # 如果需要更改符号在这里改


def most_frequent_rhythm(nested_list: list[list[int]]) -> int:
    """
    统计以数字表示的韵字韵部列表中各个元素的出现频率，并找出出现次数最多的元素。
    Args:
        nested_list: 韵部列表
    Returns:
        诗所押的韵的数字表示（如果可能出现多个，即全为多音字，那么返回第一个）
    """
    freq = defaultdict(int)
    for sublist in nested_list:
        for num in sublist:
            freq[num] += 1
    max_count = max(freq.values())
    most_num = [num for num, count in freq.items() if count == max_count]
    return most_num[0]


def first_hard(first_hanzi: str, second_hanzi: str, yun_shu: int) -> list | bool:
    """
    分析首句是否为韵字。
    Args:
        first_hanzi: 第一句末汉字
        second_hanzi: 第二句末汉字
        yun_shu: 使用的韵书代码
    Returns:
        返回共同韵部的列表，如果没有共同韵部，返回 False。
    """
    if yun_shu == 1:
        first_list = hanzi_rhythm(first_hanzi)  # 平水
        second_list = hanzi_rhythm(second_hanzi)
    else:  # 新韵通韵
        yun_shu = nw.xin_yun if yun_shu == 2 else nw.tong_yun
        first_list = nw.convert_yun(nw.get_new_yun(first_hanzi), yun_shu)
        second_list = nw.convert_yun(nw.get_new_yun(second_hanzi), yun_shu)
    duplicates = set(first_list) & set(second_list)
    if yun_shu == 1 and not duplicates:  # 使用平水韵时首句检测词林，首句可能押邻韵
        first_ci = hanzi_rhythm(first_hanzi, ci_lin=True)
        second_ci = hanzi_rhythm(second_hanzi, ci_lin=True)
        duplicates = set(first_ci) & set(second_ci)
    if duplicates:
        return list(duplicates)
    return False


def poetry_yun_jiao(poem: str, yun_shu: int) -> tuple[str, list | bool, str, str]:
    """
    提取一首诗中所有的韵字。
    Args:
        poem: 诗的全部汉字内容
        yun_shu: 使用的韵书代码
    Returns:
        返回四个值：
            韵字字符串
            第一句末汉字与第二句末汉字共同的韵列表，如果没有共同韵部，返回 False
            第一句末汉字
            第二句末汉字
    """
    poem_length = len(poem)
    indices = []
    if poem_length % 10 == 0:
        indices = list(range(10, poem_length + 1, 10))
    elif poem_length % 14 == 0:
        indices = list(range(14, poem_length + 1, 14))
    extracted = [poem[hanzi_yun_jiao - 1] for hanzi_yun_jiao in indices]
    if poem_length % 5 == 0:
        first_hanzi = poem[4]
        second_hanzi = poem[9]
    else:
        first_hanzi = poem[6]
        second_hanzi = poem[13]
    first_yayun = first_hard(first_hanzi, second_hanzi, yun_shu)
    if first_yayun:
        extracted.insert(0, first_hanzi)
    return ''.join(extracted), first_yayun, first_hanzi, second_hanzi


def lyu_ju(sentence: str, rule: int, yun_shu: int, poem_pingze: int,
           input_flag: int = 0) -> tuple[list[bool], int, str, str]:
    """
    判断一个句子是不是律句，包括拗句。
    Args:
        sentence: 诗的单个句子
        rule: 句子匹配的对应规则代码
        yun_shu: 使用的韵书代码
        input_flag: 拗句标记代码
        poem_pingze: 诗的平仄代码
    Returns:
        返回三个值：
            表示该字平仄正确与否的布尔列表
            拗句代码，0正常 1平平仄平仄 2中仄中仄仄
            展示的拗句提示词
    """
    hint_word = ''
    if poem_pingze == -1:
        lyu_ju_rule_dict[1] = ['11221', '21121', '11121', '21221']  # 仄韵无孤平
        lyu_ju_rule_dict[4] = ['02012']
        lyu_ju_rule_dict[8] = ['0102012']  # 仄韵无“中仄中仄仄”拗句，因为没法对句救
    else:
        lyu_ju_rule_dict[1] = ['11221', '21121', '11121']
        lyu_ju_rule_dict[4] = ['02012', '02022']
        lyu_ju_rule_dict[8] = ['0102012', '0102022']
    if input_flag == 2:
        patterns = lyu_ju_rule_dict[rule][-2:]
    else:
        patterns = lyu_ju_rule_dict[rule]

    sentence_pattern = ''.join(hanzi_to_pingze(char, yun_shu) for char in sentence)

    best_match = None
    best_match_score = float('inf')
    for pattern in patterns:
        match_list = [False] * len(sentence_pattern)
        match_score = 0

        for i_ljuju, (s_char, p_char) in enumerate(zip(sentence_pattern, pattern)):
            if p_char == '0':
                match_list[i_ljuju] = True
            elif p_char == '1' and s_char in '01':
                match_list[i_ljuju] = True
            elif p_char == '2' and s_char in '02':
                match_list[i_ljuju] = True

            if not match_list[i_ljuju]:
                match_score += 1  # 记录平仄不匹配的个数

        if match_score < best_match_score:
            best_match_score = match_score
            best_match = (pattern, match_list)

    matched_rule, match_list = best_match
    change_to_hanzi_rule = {'0': '中', '1': '平', '2': '仄'}
    hanzi_rule = ''.join(change_to_hanzi_rule[char] for char in matched_rule)
    hint_word += f'\n{hanzi_rule}'

    ao_word = ''
    if matched_rule in ['02022', '0102022']:  # 拗救需提示
        input_flag = 2
        ao_word += "\n本句可能为“中仄中仄仄”拗句。四拗对句须三救。"
    elif matched_rule in ['0211212', '11212']:
        input_flag = 1
        ao_word += "\n“平平仄平仄”拗句，为本句自救。"
    else:
        input_flag = 0
    return match_list, input_flag, hint_word, ao_word


def check_real_first(first: list | bool, second: int, first_sen: str,
                     yun_shu: int, sen_type: int) -> tuple[int, int]:
    """
    检测可能出现的特殊情况：首句不押韵但是第一句末字平仄与第二句末字同，此时修整第一句格式，判断为押韵但是此处用韵有误。
    Args:
        first: 第一个判断标准。即两字共同的韵列表，若无则为 False
        second: 第二个判断标准，如果为 1，则两字均为平，如果为 -1，则两字均为仄，如果为 0，则表示平仄不同
        first_sen: 诗的第一句内容
        yun_shu: 使用的韵书代码
        sen_type: 句子匹配的对应规则代码
    Returns:
        返回两个值：
            修正后的 sen_type
            修正后的 second
    """
    last1 = hanzi_to_pingze(first_sen[-1], yun_shu)
    last3 = hanzi_to_pingze(first_sen[-3], yun_shu)
    if last1 != '0':
        return sen_type, second
    change_dict = {1: 2, 3: 4, 4: 3, 2: 1, 5: 6, 6: 5, 7: 8, 8: 7}
    if not first and second:  # 那就一定不押韵
        return change_dict[sen_type], 0
    if first and second:  # 押不押韵得看格式以及倒数第三个字
        if sen_type in [3, 7] and last3 == '1':
            return change_dict[sen_type], 0
        if sen_type in [2, 6] and last3 == '2':
            return change_dict[sen_type], 0
    return sen_type, second


def which_sentence(first_sen_type: int, how_many: int, first_yayun: int, poem_pingze: int) -> list[int]:
    """
    根据首句推测后续句的格式。
    Args:
        first_sen_type: 首句的句式格式代码
        how_many: 诗的句数
        first_yayun: 首句是否押韵，-1押仄韵 1押平韵 0不押韵
        poem_pingze: 诗歌的平仄代码
    Returns:
        每个句子对应的规则代码的列表
    """
    sen_list = []
    turn_rule = {1: 2, 2: 3, 3: 4, 4: 1, 5: 6, 6: 7, 7: 8, 8: 5}
    first_rule = {1: 3, 2: 4, 3: 1, 4: 2, 5: 7, 6: 8, 7: 5, 8: 6}
    ze_turn_rule = {2: 1, 3: 2, 4: 3, 1: 4, 6: 5, 7: 6, 8: 7, 5: 8}
    ze_first_rule = {3: 1, 4: 2, 1: 3, 2: 4, 7: 5, 8: 6, 5: 7, 6: 8}
    for _ in range(how_many):
        sen_list.append(first_sen_type)
        if first_yayun and _ == 0:  # 若首句押韵
            if poem_pingze == 1:
                first_sen_type = first_rule[first_sen_type]
            else:
                first_sen_type = ze_first_rule[first_sen_type]
        else:
            if poem_pingze == 1:
                first_sen_type = turn_rule[first_sen_type]
            else:
                first_sen_type = ze_turn_rule[first_sen_type]
    return sen_list


def yun_jiao_show(zi: str, poem_rhythm_num: int, yun_shu: int, is_first_sentence: bool) -> str:
    """
    展示韵脚。
    Args:
        zi: 韵脚汉字
        poem_rhythm_num: 诗所押的韵的数字表示
        yun_shu: 使用的韵书代码
        is_first_sentence: 是否为首句
    Returns:
        韵脚的展示结果
    """
    yun_jiao_content = ''
    zi_list = []
    if yun_shu == 1:
        zi_rhythm = hanzi_rhythm(zi)
        zi_rhythm.sort()
        for _ in zi_rhythm:
            zi_list.append(''.join(rhythm_name)[_ - 1])
    elif yun_shu == 2:
        zi_rhythm = nw.convert_yun(nw.get_new_yun(zi), nw.xin_yun)
        for _ in zi_rhythm:
            zi_list.append(''.join(nw.xin_hanzi)[int(math.fabs(_)) - 1])
    else:
        zi_rhythm = nw.convert_yun(nw.get_new_yun(zi), nw.tong_yun)
        for _ in zi_rhythm:
            zi_list.append(''.join(nw.tong_hanzi)[int(math.fabs(_)) - 1])
    if_ya_yun = True if poem_rhythm_num in zi_rhythm else False
    if not if_ya_yun and is_first_sentence and poem_rhythm_num <= 30 and yun_shu == 1:  # 首句用邻韵
        all_ci = rhythm_correspond[poem_rhythm_num]
        if isinstance(all_ci, int):
            all_ci = {all_ci}
        elif isinstance(all_ci, list):
            all_ci = set(all_ci)
        first_ci = []
        for _ in zi_rhythm:
            if _ < 31:
                remain = rhythm_correspond[_]
                if isinstance(remain, int):
                    first_ci.append(remain)
                elif isinstance(remain, list):
                    first_ci.extend(remain)
        first_ci = set(first_ci)
        ci_both = all_ci & first_ci
        if not ci_both:
            yun_jiao_content += f'{"韵、".join(zi_list)}韵 ' + '不押韵 '
        else:
            yun_jiao_content += f'{"韵、".join(zi_list)}韵 ' + '用邻韵 押韵 '
    else:
        yun_jiao_content += f'{"韵、".join(zi_list)}韵 ' + f'{"" if if_ya_yun else "不"}押韵 '
    return yun_jiao_content


def sentence_show(show_sentence: str, sen_ge_lyu: list[bool], yun_shu: int) -> str:
    """
    展示律句的平仄情况。
    Args:
        show_sentence: 展示的句子
        sen_ge_lyu: 表示该字平仄正确与否的列表
        yun_shu: 使用的韵书代码
    Returns:
        实际展示格律的字符串，用“〇、中、错”表示
    """
    sp_zi = []
    ge_lju_show = ''
    for char in show_sentence:
        ping_ze = hanzi_to_pingze(char, yun_shu)
        sp_zi.append('duo') if ping_ze == '0' else sp_zi.append('no')

    for i, is_valid in enumerate(sen_ge_lyu):
        if is_valid:
            ge_lju_show += sh[2] if sp_zi[i] == 'duo' else sh[0]
        else:
            ge_lju_show += sh[1]
    return ge_lju_show


def special_two_pingze(hanzi1: str, hanzi2: str, yun_shu: int, poem_pingze: int) -> int:
    """
    根据第一句末字与第二句末字，诗的平仄得到第二个判断标准。
    Args:
        hanzi1: 第一句末汉字
        hanzi2: 第二句末汉字
        yun_shu: 使用的韵书代码
        poem_pingze: 全诗的押韵平仄，1平 -1仄
    Returns:
        第二个判断标准
    """
    ping_ze1 = hanzi_to_pingze(hanzi1, yun_shu)
    ping_ze2 = hanzi_to_pingze(hanzi2, yun_shu)
    if ping_ze1 + ping_ze2 in ['12', '21']:
        return 0  # 不一致
    if '1' in ping_ze1 + ping_ze2 and poem_pingze == 1:
        return 1  # 一致且为平
    if '2' in ping_ze1 + ping_ze2 and poem_pingze == -1:
        return -1  # 一致且为仄
    if ping_ze1 + ping_ze2 == '00':
        return 1 if poem_pingze == 1 else -1
    return 0


def is_all_duo_yin(yun_jiao_content: str, yun_shu: int) -> bool:
    """
    判断韵脚字是不是全部是多音字。
    Args:
        yun_jiao_content: 韵脚汉字的字符串
        yun_shu: 使用的韵书代码
    Returns:
        是否全部为多音字
    """
    for i in yun_jiao_content:
        ping_ze = hanzi_to_pingze(i, yun_shu)
        if ping_ze != '0':
            return False
    return True


def part_shi(yun_shu: int, poem: str) -> tuple[str, str, int, list | bool, int]:
    """
    诗歌检验函数集成一
    Args:
        yun_shu: 使用的韵书代码
        poem: 诗歌的全汉字内容
    Returns:
        返回五个结果：
            首句末汉字
            第二句末汉字
            诗平仄
            第一个判断标准
            诗所押的韵的数字表示
    """
    yun_jiaos, f_rhythm, f_hanzi, s_hanzi = poetry_yun_jiao(poem, yun_shu)
    rhythm_lists = [hanzi_to_yun(yun_jiao, yun_shu) for yun_jiao in yun_jiaos]
    this_rhythm = most_frequent_rhythm(rhythm_lists)
    if f_rhythm:
        f_rhythm_check = set(f_rhythm) & {this_rhythm}
        f_rhythm = next(iter(f_rhythm_check)) if f_rhythm_check else f_rhythm[0]
    if yun_shu == 1:
        poem_pingze = 1 if this_rhythm < 31 else -1
    else:
        poem_pingze = 1 if this_rhythm > 0 else -1  # 1 全诗平 -1 仄 无法判断多音 0
    if is_all_duo_yin(yun_jiaos, yun_shu):
        poem_pingze = 0
    return f_hanzi, s_hanzi, poem_pingze, f_rhythm, this_rhythm


def part_shi_2(yun_shu: int, poem: str, f_hanzi: str, s_hanzi: str,
               poem_pingze: int, f_rhythm: list | bool, this_rhythm: int, sen_len: int = None) -> str:
    """
    诗歌检验函数集成二。
    Args:
        yun_shu: 使用的韵书代码
        poem: 诗歌的全汉字内容
        f_hanzi: 首句末汉字
        s_hanzi: 第二句末汉字
        poem_pingze: 诗歌平仄
        f_rhythm: 第一个判断标准
        this_rhythm: 诗所押的韵的数字表示
        sen_len: 指定一句的长度，用于排律字数无法确定是五言句还是七言句时使用
    Returns:
        诗歌的检验结果（还需要校验）
    """
    s_rhythm = special_two_pingze(f_hanzi, s_hanzi, yun_shu, poem_pingze)
    shi_result = ''
    if not sen_len:
        sen_len = 5 if len(poem) % 5 == 0 else 7
    if len(poem) // sen_len == 4:
        poem_type = '绝句'
    elif len(poem) // sen_len == 8:
        poem_type = '律诗'
    else:
        poem_type = '排律'
    shi_result += f'{num_to_cn(sen_len)}言{poem_type}\n'
    first_sen = get_first_type_main(poem, yun_shu, s_rhythm, poem_pingze, sen_len)
    first_sen, s_rhythm = check_real_first(f_rhythm, s_rhythm, poem[0: sen_len], yun_shu, first_sen)
    max_yun_jiao = len(poem) // 5 if sen_len == 5 else len(poem) // 7
    yun_jiao_list = list(range(2, max_yun_jiao + 1, 2))
    if s_rhythm:
        yun_jiao_list.append(1)
    if not first_sen:
        return '无法判断。'  # 如果没有识别，中止。
    rule_list = which_sentence(first_sen, int(len(poem) / sen_len), s_rhythm, poem_pingze)

    sen_mode = 0  # 一般律句，如果有拗句，对应值变化
    for i in range(len(rule_list)):
        a_sentence = poem[sen_len * i: sen_len * (i + 1)]
        ge_lju, sen_mode, hint, ao = lyu_ju(a_sentence, rule_list[i], yun_shu, poem_pingze, sen_mode)
        shi_result += hint + '\n' + a_sentence + '\t'
        yun_jiao_result = ''
        if i + 1 in yun_jiao_list:
            is_first_sen = True if i == 0 else False
            yun_jiao_result = yun_jiao_show(a_sentence[-1], this_rhythm, yun_shu, is_first_sen)
        ge_lju_show = sentence_show(a_sentence, ge_lju, yun_shu)
        shi_result += yun_jiao_result + '\n' + ge_lju_show + '\t' + ao + '\n'
    return shi_result


def real_shi(yun_shu: int, poem: str) -> str:
    """
    最终在tk上运行的主模块。
    Args:
        yun_shu: 使用的韵书代码
        poem: 诗歌的全汉字内容
    Returns:
        最终的诗歌校验结果
    """
    start_time = time.time()
    if len(poem) % 70 == 0:
        all_check_time = 2
        d_check = [5, 7]
    else:
        all_check_time = 1
        d_check = [None]
    all_post_result = final_result = ''
    for _ in range(all_check_time):
        post_result = ''
        f_hanzi, s_hanzi, poem_pingze, f_rhythm, this_rhythm = part_shi(yun_shu, poem)
        poem_pingze = [1, -1] if poem_pingze == 0 else [poem_pingze]
        for single_pingze in poem_pingze:
            temp_result = part_shi_2(yun_shu, poem, f_hanzi, s_hanzi, single_pingze, f_rhythm, this_rhythm, d_check[_])
            final_result = result_check(post_result, temp_result)
            post_result = temp_result
        if all_check_time == 1:
            break
        all_temp_result = final_result
        final_result = result_check(all_post_result, all_temp_result)
        all_post_result = all_temp_result
    end_time = time.time()
    final_result += f'检测完毕，耗时{end_time - start_time:.5f}s\n'
    return final_result.lstrip()
