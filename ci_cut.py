def split_cipai_text(cipai_text, yun_jiao_places):
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


def split_yun_str_by_ci(ci_list, yun_str, yun_list, ci_num):
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


def replace_user_ci_text(user_ci_text, ci_cut_text):
    merged_ci = ''.join(ci_cut_text)
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
    for part in ci_cut_text:
        length = len(part)
        user_cut_text.append(''.join(new_ci[current_pos:current_pos + length]))
        current_pos += length

    return user_cut_text
