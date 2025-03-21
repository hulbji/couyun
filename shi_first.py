from pingshui_rhythm import hanzi_rhythm
import new_rhythm as nw


def match_combinations(poem_str):
    combinations = ["111", "112", "121", "122", "211", "212", "221", "222"]
    matched_combinations = []
    for combo in combinations:
        match = True
        for i in range(3):
            # 如果输入字符串的当前字符不是0且与组合中的字符不匹配，则跳过该组合
            if poem_str[i] != '0' and poem_str[i] != combo[i]:
                match = False
                break
        if match:
            matched_combinations.append(combo)
    return matched_combinations


def sen_to_poem_str(poem_sen: str, yun_shu: int):
    if yun_shu == 1:
        hanzi1 = hanzi_rhythm(poem_sen[1], only_ping_ze=True)
        hanzi3 = hanzi_rhythm(poem_sen[3], only_ping_ze=True)
        hanzi5 = hanzi_rhythm(poem_sen[-1], only_ping_ze=True)
    else:
        hanzi1 = nw.new_ping_ze(nw.get_new_yun(poem_sen[1]))
        hanzi3 = nw.new_ping_ze(nw.get_new_yun(poem_sen[3]))
        hanzi5 = nw.new_ping_ze(nw.get_new_yun(poem_sen[-1]))
    return hanzi1 + hanzi3 + hanzi5


def first_poem(matched_lists, first_yayun, sen_num, poem_pingze, match_time=1):
    matched_list = matched_lists[match_time - 1]
    ping = {1: [1, 3], 2: [3, 1], 3: [4, 2], 4: [1, 3], 5: [2, 4], 6: [3, 1], 7: [4, 2], 8: [1, 3]}
    ze = {1: [2, 4], 2: [4, 2], 3: [1, 3], 4: [2, 4], 5: [3, 1], 6: [4, 2], 7: [1, 3], 8: [2, 4]}
    rule = {'111': 0, '112': 2, '121': 1, '122': 2, "211": 3, '212': 4, '221': 0, '222': 4}
    changed_set = set([rule[i] for i in matched_list])
    if first_yayun == 1:
        intersection = changed_set.intersection(set(ping[match_time]))
        if len(intersection) == 1:
            current = next(iter(intersection))
            place = ping[match_time].index(current)
            return ping[1][place]
    elif first_yayun == -1:
        intersection = changed_set.intersection(set(ze[match_time]))
        if len(intersection) == 1:
            current = next(iter(intersection))
            place = ze[match_time].index(current)
            return ze[1][place]
    else:
        if len(changed_set) == 1:
            result = next(iter(changed_set)) + 1 - match_time
            while result <= 0:
                result += 4
            return result
    if sen_num == match_time:
        co_rule = rule[matched_list[0]]
        if co_rule == 0:
            if matched_list[0] == '111' and poem_pingze > 0:
                co_rule = 1
            elif matched_list[0] == '221' and poem_pingze > 0:
                co_rule = 3
            elif matched_list[0] == '111' and poem_pingze < 0:
                co_rule = 2
            else:
                co_rule = 4
        if co_rule in [2, 4] and poem_pingze > 0:
            co_rule -= 1
        if co_rule in [1, 3] and poem_pingze < 0:
            co_rule += 1
        return co_rule if first_yayun else (co_rule + 1) % 4
    match_time += 1
    return first_poem(matched_lists, first_yayun, sen_num, poem_pingze, match_time)


def seperate_poem(poem_str):
    poem_str_list = []
    sen_num = 0
    while len(poem_str) % 7 == 0:
        poem_str_list.append(poem_str[2:7])
        poem_str = poem_str[7:]
        sen_num += 1
        if len(poem_str) == 0:
            return poem_str_list, sen_num
    while len(poem_str) % 5 == 0:
        poem_str_list.append(poem_str[0:5])
        poem_str = poem_str[5:]
        sen_num += 1
        if len(poem_str) == 0:
            return poem_str_list, sen_num


def get_first_type_main(poem, yun_shu, first_yayun, poem_pingze):
    poem_lists, sentence_num = seperate_poem(poem)
    num_lists = []
    for sentence in poem_lists:
        check_poem_str = sen_to_poem_str(sentence, yun_shu)
        poem_list = match_combinations(check_poem_str)
        num_lists.append(poem_list)
    matched_method = first_poem(num_lists, first_yayun, sentence_num, poem_pingze)
    return matched_method if len(poem) % 5 == 0 else matched_method + 4
