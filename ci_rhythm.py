"""词校验模块内容，支持三韵。"""

from ci_show import *
from common import *
from cipai_word_counts import ci_and_num
import json

idx_file = os.path.join(current_dir, 'ci_list', 'ci_index.json')
with open(idx_file, encoding='utf-8') as f:
    idx = json.load(f)
show_mark = ['◎', '●', '〇', '？']


def search_ci(input_name: str, reverse_search=False) -> str | None:
    """
    从词牌名称，在词牌索引中读取编号。或者通过编号读取词牌名。
    Args:
        input_name: 词牌实际名称或编号
        reverse_search: 是否反向搜索，通过编号读取词牌名。
    Returns:
        词牌的编号值（字符串）或编号值对应的词牌名，如果没有，返回None
    """
    if reverse_search:
        return idx[input_name][0]
    else:
        for num, names in idx.items():
            if input_name in names:
                return num
        return None


def ci_type_extraction(ci_number: str | int) -> list[dict]:
    """
    提取此编号词牌的格式，不同的格式以两行存储。
    Args:
        ci_number: 词牌的编号值
    Returns:
        词牌所有格式的列表，列表中的列表包含每一个格式的例词内容，格律和词牌描述。
    """
    file_path = os.path.join(current_dir, 'ci_list', f'cipai_{ci_number}.json')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = json.load(file)
    return content


def ping_ze_right(text: str, cipai: str, yun_shu: int) -> list[str | bool]:
    """
    检验一首词是否符合一个词牌特定格式的平仄。
    Args:
        text: 校验的词汉字内容
        cipai: 删去标识词句读韵等的词的格律
        yun_shu: 使用的韵书代码
    Returns:
        平仄正误的列表 True对 False错 "duo"多音字无法判断
    """
    yun_shu = int(yun_shu)
    result = []
    for hanzi_num in range(len(text)):
        ping_ze = hanzi_to_pingze(text[hanzi_num], yun_shu)
        if ping_ze == '0':
            result.append('duo')
        elif ping_ze == '3':
            result.append('pi')
        elif ping_ze == '1':
            result.append(True) if cipai[hanzi_num] in '平中' else result.append(False)
        else:
            result.append(True) if cipai[hanzi_num] in "仄中" else result.append(False)
    return result


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


def show_ci(ge_lyu_final: list, text_final: list, yun_final: list, your_lyu_final: list) -> str:
    """
    将所有得到的结果组合称为最终的结果
    Args:
        ge_lyu_final: 词的格律
        text_final: 输入的词的内容
        yun_final: 押韵结果
        your_lyu_final: 平仄符合与否的结果
    Returns:
        组合的结果
    """
    result = ''
    for _ in range(len(ge_lyu_final)):
        result += ge_lyu_final[_] + '\n'
        result += text_final[_] + '\u3000'
        result += yun_final[_] + '\n'
        if "不押韵" in yun_final[_]:
            result += your_lyu_final[_][:-1] + '■' + '\n\n'
        if "不" not in yun_final[_]:
            if your_lyu_final[_][-1] == '●':
                result += your_lyu_final[_][:-1] + '■' + '\n\n'
            else:
                result += your_lyu_final[_][:-1] + '□' + '\n\n'
        if "不知韵部" in yun_final[_]:
            result += your_lyu_final[_] + '\n\n'
    return result.rstrip() + '\n'


def find_punctuation_positions(text: str) -> list[int]:
    comma_syms = {',', '.', '?', '!', ':', "，", "。", "？", "！", "、", "：", '\u3000'}
    position = []
    correct = 1
    is_comma = False
    for index, ch in enumerate(text):
        if ch in comma_syms:
            if not is_comma:
                position.append(index - correct)
            correct += 1
            is_comma = True
        else:
            is_comma = False
    return position


def cipai_confirm(ci_input: str, ci_comma: str, sg_cipai_forms: list[dict]) -> list:
    right_list = []
    zi_conunt = len(ci_input)
    form_count = 0
    for single_form in sg_cipai_forms:
        single_sample_ci = '\u3000'.join(single_form['ci_sep'])
        if zi_conunt != len(single_form['ge_lyu_str']):
            form_count += 1
            continue
        cipai_form = find_punctuation_positions(single_sample_ci)
        input_form = find_punctuation_positions(ci_comma)
        right = len(set(input_form).intersection(cipai_form))
        right_rate = right / len(set(input_form) | set(cipai_form))
        if zi_conunt <= 14:
            set_rate = 0
        elif zi_conunt >= 100:
            set_rate = 0.7
        else:
            set_rate = 0.7 * (zi_conunt - 14) / (100 - 14)
        if right_rate > set_rate:
            right_list.append(form_count)
        form_count += 1
    return right_list


def real_ci(yun_shu: int, ci_pai_name: str, ci_content: str, ci_comma: str, give_type: str) -> str | int:
    """
    校验词牌的最终方法
    Args:
        yun_shu: 使用的韵书代码
        ci_pai_name: 输入的词牌名
        ci_content: 输入的词内容（已经除去了除汉字以外的内容）
        ci_comma: 保留标点符号的输入内容
        give_type: 给定的词牌格式，如果没有，那么按照自动格式检验
    Returns:
        校验结果。如果输入的词牌没有对应，返回 0，如果词内容不能与词牌匹配，返回 1
    """
    rate_dict = {}
    all_type_dict = {}
    if ci_pai_name:  # 如果输入了词牌名称
        ci_num = search_ci(ci_pai_name)
        if ci_num is None:
            return 0
        ci_nums = [ci_num]
        all_type_dict[ci_num] = ci_type_extraction(ci_num)
        rate_dict[ci_num] = cipai_confirm(ci_content, ci_comma, all_type_dict[ci_num])
    else:
        if len(ci_content) in ci_and_num.keys():
            ci_num_list = ci_and_num[len(ci_content)]
        else:
            return 3
        for single_ci_type in ci_num_list:
            this_type = ci_type_extraction(single_ci_type)
            current_rate = cipai_confirm(ci_content, ci_comma, this_type)
            if not current_rate:
                continue
            all_type_dict[single_ci_type] = this_type
            rate_dict[single_ci_type] = current_rate
        # print(rate_dict)
        ci_nums = rate_dict.keys()
        if not ci_nums:
            return 3
    real_final = real_post = ''
    for ci_num in ci_nums:
        type_list = all_type_dict[ci_num]
        final_result = post_result = ''
        correct_types = rate_dict[ci_num]
        incorrect_given_type = False
        if not correct_types:
            return 1
        if give_type:
            if give_type.isnumeric():
                give_type = int(give_type) - 1
                if give_type in correct_types:
                    correct_types = [give_type]
                else:
                    incorrect_given_type = True
            else:
                return 2
        for correct_type in correct_types:
            ci_result = ''
            ci_result += f'你的格式为 格{num_to_cn(correct_type + 1)}' + '\n'
            sg_type = type_list[correct_type]
            remain = sg_type['ge_lyu_str']
            yun_jiao_pos = sg_type['rhyme_pos']
            yun_jiao_class = sg_type['yun_classify']
            yun_list = [ci_content[i] for i in yun_jiao_pos]
            real_ci_lis = sg_type['ci_sep']
            cut_list = sg_type['ge_lyu_sep']
            my_cut_text = replace_user_ci_text(ci_content, real_ci_lis)  # 分割后词内容
            yun_num_list = []
            for yun_jiao in yun_list:
                yun_num_list.append(hanzi_to_yun(yun_jiao, yun_shu, ci_lin=True))

            yun_show_list = yun_data_process(yun_jiao_pos, yun_list, yun_jiao_class, yun_num_list)
            yun_info_list = []
            for single_show_dict in yun_show_list:
                yun_hanzi = ci_yun_list_to_hanzi_yun(single_show_dict['yun_num'], yun_shu)
                yun_group = f"第{num_to_cn(single_show_dict['group'])}组韵"
                is_yayun = f"{'' if single_show_dict['is_yayun'] else '不'}押韵"
                yun_info = yun_hanzi + ' ' + yun_group + ' ' + is_yayun
                if '零' in yun_info or len(yun_info) == 9:
                    yun_info = '不知韵部'
                yun_info_list.append(yun_info)  # 分割后词韵信息
            real_ci_right = ping_ze_right(ci_content, remain, yun_shu)
            yun_final_list = yun_right_list(real_ci_lis, real_ci_right)
            ci_result += '\n' + show_ci(cut_list, my_cut_text, yun_info_list, yun_final_list)
            if correct_type == 23 and ci_num == '658':  # 水龙吟格二十四特殊处理
                ci_result += f'\n仄句\n{ci_content[-1]}\n'
                last_pingze = hanzi_to_pingze(ci_content[-1], yun_shu)
                ci_result += f'{show_mark[int(last_pingze)]}\n'
            final_result = result_check(post_result, ci_result)
            post_result = final_result
        if incorrect_given_type:
            final_result = "给定格式与实际相差过大或没有此格式，将另行匹配。\n" + final_result
        if not ci_pai_name:
            name_show = search_ci(ci_num, reverse_search=True)
            final_result = name_show + '\n' + final_result
        current_result = final_result
        real_final = result_check(real_post, current_result)
        real_post = real_final
    return real_final
