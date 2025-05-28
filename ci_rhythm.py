"""词校验模块内容，支持三韵。"""

import time

from ci_cut import *
from ci_show import *
from ci_confirm import *
from common import *
from cipai_word_counts import ci_and_num


def search_ci(input_name: str, reverse_search=False) -> str | None:
    """
    从词牌名称，在词牌索引中读取编号。或者通过编号读取词牌名。
    Args:
        input_name: 词牌实际名称或编号
        reverse_search: 是否反向搜索，通过编号读取词牌名。
    Returns:
        词牌的编号值（字符串）或编号值对应的词牌名，如果没有，返回None
    """
    file_path = os.path.join(current_dir, 'ci_list', 'ci_index.txt')
    with open(file_path, 'r', encoding='utf-8') as file:
        ci_dict = {}
        for line in file:
            line = line.strip()
            number, ci_name = line.split()
            ci_dict[ci_name] = number
    if reverse_search:
        for key, value in ci_dict.items():
            if value == input_name:
                return key
        return None
    else:
        ci_number = ci_dict.get(input_name)
        if ci_number is not None:
            return ci_number
        return None


def ci_type_extraction(ci_number: str) -> list[list[str]]:
    """
    提取此编号词牌的格式，不同的格式以两行存储。
    Args:
        ci_number: 词牌的编号值
    Returns:
        词牌所有格式的列表，列表中的列表包含每一个格式的例词内容，格律和词牌描述。
    """
    file_path = os.path.join(current_dir, 'ci_list', f'cipai_{ci_number}.txt')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    sections = content.strip().split("\n\n")
    formatted_sections = []
    ci_format = []
    for section in sections:
        lines = section.strip().split("\n")
        ci_format.append(lines[1])
        lines = lines[3:]
        formatted_sections.append("\n".join(lines))

    processed_sections = []
    for section in formatted_sections:
        lines = section.split("\n")
        odd_lines = []
        even_lines = []

        for i in range(0, len(lines), 2):
            odd_line = lines[i]
            even_line = lines[i + 1]
            odd_line_padded = odd_line.ljust(len(even_line), '\u3000')
            odd_lines.append(odd_line_padded)
            even_lines.append(even_line)
        odd_combined = "".join(odd_lines)
        even_combined = "".join(even_lines)
        processed_sections.append([odd_combined, even_combined])
    for i in range(len(ci_format)):
        processed_sections[i].append(ci_format[i])
    return processed_sections


def process_rhyme_data(rhyme_words: list, rhyme_position: list) -> tuple[list, list]:
    """
    给定句读及韵标识词的列表以及其在词中位置的列表，将不需要的“句、读”以及特殊情况下的和声词及其位置从两列表移出。
    Args:
        rhyme_words: 给定句读及韵标识词的列表
        rhyme_position: 标识词在词中位置的列表
    Returns:
        返回两个值：
            只含韵标识词的列表
            修正后标识词在词中位置的列表
    """
    chars_to_remove = "竹枝女儿举棹年少句读\u3000"
    processed_rhyme_words = []
    processed_rhyme_position = []
    for i, (word, position) in enumerate(zip(rhyme_words, rhyme_position)):
        if word == '叠' and rhyme_words[i - 1] == '句':  # 如果当前词是“叠”，检查前一个词是否是“句”，此时为“叠句”而非“叠韵”
            continue
        processed_word = ''.join(char for char in word if char not in chars_to_remove)
        if processed_word:
            processed_rhyme_words.append(processed_word)
            processed_rhyme_position.append(position)
    return processed_rhyme_words, processed_rhyme_position


def extract_rhyme_words(example_ci: str, ci_rhythm: str, ci_rule: list) -> tuple[list, list[list[int]], str, list[int]]:
    """
    提取一个格式中的韵位置，以及格律的平仄，以列表表示。
    Args:
        example_ci: 例词的内容
        ci_rhythm: 词的格律
        ci_rule: 词牌韵脚数目的列表，分别告诉每一段有几个韵脚
    Returns:
        返回四个值：
            只含韵标识词的列表
            标识词在词中位置的嵌套列表，列表中每个列表表示词的每一段
            删去标识词句读韵等的词的格律
            标识词在词中位置的列表
    """
    rhyme_words = []  # 用于存储提取的韵脚词汇
    rhyme_positions = []  # 用于存储实际韵脚的位置
    remaining_str = []  # 用于存储剩余的字符
    current_word = ""  # 当前正在构建的韵脚词汇
    in_rhyme_section = False  # 标记是否处于韵脚区域
    last_non_rhyme_char = None  # 上一个非韵脚字符

    for index, (char1, char2) in enumerate(zip(example_ci, ci_rhythm)):
        if char1 == "\u3000":  # 当前字符处于韵脚区域
            if not in_rhyme_section:  # 开始新的韵脚词汇
                in_rhyme_section = True
                current_word = char2
                if last_non_rhyme_char is not None:
                    correct = len(''.join(rhyme_words))  # 修正因为出现引导词产生的偏差
                    rhyme_positions.append(index - 1 - correct)  # 记录实际韵脚的位置
            else:  # 继续构建当前韵脚词汇
                current_word += char2
        else:  # 当前字符不在韵脚区域
            if in_rhyme_section:  # 结束当前韵脚词汇
                in_rhyme_section = False
                rhyme_words.append(current_word)  # 将韵脚词汇加入列表
                current_word = ""
            last_non_rhyme_char = char2  # 更新上一个非韵脚字符
            remaining_str.append(char2)  # 将非韵脚字符加入剩余字符串列表
    rhyme_words.append(current_word)
    remaining_str = "".join(remaining_str)
    rhyme_words, rhyme_positions = process_rhyme_data(rhyme_words, rhyme_positions)
    proceeded_rhyme_positions = split_yun_place(rhyme_positions, ci_rule)
    return rhyme_words, proceeded_rhyme_positions, remaining_str, rhyme_positions


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


def split_yun_place(all_yun: list[int], split_method: list[int]) -> list[list[int]]:
    """
    将提取到的韵脚位置按照段落分割。
    Args:
        all_yun: 标识词在词中位置的列表
        split_method: 词牌韵脚数目的列表，分别告诉每一段有几个韵脚
    Returns:
        标识词在词中位置的嵌套列表，列表中每个列表表示词的每一段
    """
    result = []
    start = 0
    for length in split_method:
        end = start + length
        result.append(all_yun[start:end])
        start = end
    return result


def find_ci_part(ci_info: str) -> list[int]:
    """
    提取词牌中分段信息，每一段几个韵。
    Args:
        ci_info: 词牌描述，包括字数、段数、押韵情况
    Returns:
        词牌韵脚数目的列表，分别告诉每一段有几个韵脚
    """
    parts = ci_info.split("句")
    segments = [part.strip() for part in parts[1:]] if len(parts) > 1 else []
    result = []
    for segment in segments:
        current_list = []
        for keyword in ["仄", "平", "叠", "叶"]:
            index = segment.find(keyword)
            if index != -1 and index > 0:
                current_list.append(segment[index - 1])
        result.append(current_list)

    if "前后段" in ci_info:  # 双调重复
        first_segment = result[0]
        result = result + [first_segment]
    elif "后两段" in ci_info:
        second_segment = result[1]
        result.append(second_segment)
    elif "前两段" in ci_info:
        first_segment = result[0]
        result = [first_segment] + result
    elif "每段" in ci_info:  # 三段重复
        first_segment = result[0]
        result += [first_segment, first_segment]
    elif "第一、第二段" in ci_info:
        first_segment = result[0]
        result = [first_segment] + result
    elif "第三段、第四段" in ci_info:  # 四段重复，只有莺啼序会出现这些情况
        third_segment = result[2]
        result.append(third_segment)

    sum_list = []
    for segment in result:
        sum_value = 0
        for hanzi in segment:
            sum_value += cn_nums[hanzi]
        sum_list.append(sum_value)
    return sum_list


def yun_jiao_classify(yun_jiao_position: list[list[int]], hint_list: list[str]) -> dict:
    """
    根据韵脚列表与韵标识词的列表分类韵
    Args:
        yun_jiao_position: 嵌套的韵脚列表
        hint_list: 韵标识词的列表
    Returns:
        将韵脚进行分类的字典
    """
    flattened = []
    indices = []
    current = 0
    for sublist in yun_jiao_position:
        indices.append(current)
        flattened.extend(sublist)
        current += len(sublist)
    positions = indices[1:]  # 平展列表并保留分段位置
    for _ in range(len(flattened)):
        if '叶' in hint_list[_]:
            flattened[_] = - flattened[_]

    n = len(hint_list)
    pointers = []
    count = 0
    count2 = -1
    switch = False  # 对于平仄转换格才会启用，True仄 False平
    two = set()  # 如果前半段都是平，后半段都是仄或相反用这个。
    for i in range(n):
        if i in positions:
            if "换韵" in hint_list[i]:
                count += 1
            elif "换平韵" in hint_list[i]:
                count += 1
                switch = False
            elif "换仄韵" in hint_list[i]:
                count2 -= 1
                switch = True
            elif '平韵' in hint_list[i] and two == {'仄'}:
                switch = False
                count += 1
            elif '仄韵' in hint_list[i] and two == {'平'}:
                switch = True
                count2 -= 1
            elif '换叶' in hint_list[i]:
                count += 1
            else:
                count = 0
                count2 = -1
                if hint_list[i] == '仄韵':
                    switch = True
                elif hint_list[i] == '平韵':
                    switch = False
        else:
            if "平韵" in hint_list[i]:
                switch = False
                two.add('平')
            if '仄韵' in hint_list[i]:
                switch = True
                two.add('仄')
            if "换" in hint_list[i]:
                if switch:
                    count2 -= 1
                else:
                    count += 1
        if switch:
            pointers.append(count2)
        else:
            pointers.append(count)  # 记录分韵

    result = {}
    for i in range(len(flattened)):
        key = pointers[i]
        if key not in result:
            result[key] = []
        result[key].append(flattened[i])  # 分类写入字典
    return result


def find_type(text: str, all_types: list[list[str]], yun_shu: int) -> list[int] | None:
    """
    根据输入的文字以及词牌的全部格式格式，通过平仄确定可能的格式。
    Args:
        text: 输入词汉字内容
        all_types: 词牌所有格式的列表，列表中的列表包含每一个格式的例词内容，格律和词牌描述
        yun_shu: 使用韵书的代码
    Returns:
        所有可能格式的编号的列表
    """
    count_list = []
    for single_type in range(len(all_types)):
        ci, rhythm, rule = all_types[single_type]
        num_rule = find_ci_part(rule)
        yun_words, yun_position, remain_words = extract_rhyme_words(ci, rhythm, num_rule)[0:3]
        if len(remain_words) != len(text):
            continue
        right_list = ping_ze_right(text, remain_words, yun_shu)
        count = 0
        for _ in right_list:
            if _:
                count += 1
        count_list.append([single_type, count])
    if not count_list:
        return None
    count_list = sorted(count_list, key=lambda x: x[1], reverse=True)
    type_num = count_list[0][1]
    correct_types = []
    for _ in count_list:
        if _[1] / type_num >= 0.85:  # 按符合85%以上匹配
            correct_types.append(_[0])
    return correct_types


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
        result += text_final[_] + ' '
        result += yun_final[_] + '\n'
        result += your_lyu_final[_] + '\n\n'
    return result.rstrip() + '\n'


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
    start_time = time.time()
    if ci_pai_name:  # 如果输入了词牌名称
        ci_num = search_ci(ci_pai_name)
        if ci_num is None:
            return 0
        ci_nums = [ci_num]
    else:
        if len(ci_content) in ci_and_num.keys():
            ci_num_list = ci_and_num[len(ci_content)]
        else:
            return 3
        ci_nums = None
        rate_dict = {}
        for single_ci_type in ci_num_list:
            this_type = ci_type_extraction(single_ci_type)
            current_rate = cipai_confirm(ci_content, ci_comma, this_type)
            if not current_rate:
                continue
            rate_dict[single_ci_type] = current_rate
            max_rate = max(rate_dict.values())
            ci_nums = [key for key, value in rate_dict.items() if value >= max_rate * 0.9]
        if not ci_nums:
            return 3
    real_final = real_post = ''
    for ci_num in ci_nums:
        type_list = ci_type_extraction(ci_num)
        final_result = post_result = ''
        correct_types = find_type(ci_content, type_list, yun_shu)
        # print(correct_types)  # 展示可能的格式，最可能的在先， 0开头，若换算实际格式 +1
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
            ci, rhythm, rule = type_list[correct_type]
            num_rule = find_ci_part(rule)
            wds, pos, remain, yun_jiao_pos = extract_rhyme_words(ci, rhythm, num_rule)
            cipai_text = type_list[correct_type][0]
            ci_form_str = type_list[correct_type][1]
            yun_jiao_class = yun_jiao_classify(pos, wds)
            yun_list = [ci_content[i] for i in yun_jiao_pos]
            real_ci_lis = split_cipai_text(cipai_text, yun_jiao_pos)
            cut_list = split_yun_str_by_ci(real_ci_lis, ci_form_str, wds, ci_num)  # 分割后词格律信息
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
                if last_pingze == '0':
                    ci_result += '◎\n'
                elif last_pingze == '1':
                    ci_result += '●\n'
                elif last_pingze == '3':
                    ci_result += '？\n'
                else:
                    ci_result += '〇\n'
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
    end_time = time.time()
    real_final += f'检测完毕，耗时{end_time - start_time:.5f}s\n'
    return real_final
