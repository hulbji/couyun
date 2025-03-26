"""判断诗歌首句格式的模块，由于相对比较复杂，需要考虑多音字、拗救以及诗歌中可能的错误，单独设置。"""

from pingshui_rhythm import hanzi_rhythm
import new_rhythm as nw


def match_combinations(poem_str: str) -> list[str]:
    """
    将一个五言句中二四五字对应平仄代号转换为可能的组合结果。
    Args:
        poem_str: 二四五字对应平仄代号的字符串，0中 1平 2仄
    Returns:
        匹配的可能的组合结果
    """
    combinations = ["111", "112", "121", "122", "211", "212", "221", "222"]
    matched_combinations = []
    for combo in combinations:
        match = True
        for i in range(3):
            if poem_str[i] != '0' and poem_str[i] != combo[i]:
                match = False
                break
        if match:
            matched_combinations.append(combo)
    return matched_combinations


def sen_to_poem_str(poem_sen: str, yun_shu: int) -> str:
    """
    Args:
        poem_sen: 诗歌某一句的内容
        yun_shu: 使用的韵书代码
    Returns:
        二四五字对应平仄代号的字符串
    """
    if yun_shu == 1:
        hanzi1 = hanzi_rhythm(poem_sen[1], only_ping_ze=True)
        hanzi3 = hanzi_rhythm(poem_sen[3], only_ping_ze=True)
        hanzi5 = hanzi_rhythm(poem_sen[-1], only_ping_ze=True)
    else:
        hanzi1 = nw.new_ping_ze(nw.get_new_yun(poem_sen[1]))
        hanzi3 = nw.new_ping_ze(nw.get_new_yun(poem_sen[3]))
        hanzi5 = nw.new_ping_ze(nw.get_new_yun(poem_sen[-1]))
    return hanzi1 + hanzi3 + hanzi5


def first_poem(matched_lists: list[list[str]], first_yayun: int,
               sen_num: int, poem_pingze: int, match_time=1) -> int:
    """
    递归计算每一个句子，直到其匹配到特定的格式，得到首句的格式。
    Args:
        matched_lists: 每一句匹配到的可能的组合结果的列表
        first_yayun: 第一句是否押韵 1平 -1仄 0不押韵
        sen_num: 诗的句数
        poem_pingze: 诗的平仄 1平 -1仄
        match_time:匹配次数，上限为诗的句数
    Returns:
        句子匹配的规则代码（五言，七言需要在此基础上 +4）
    """
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


def seperate_poem(poem: str) -> tuple[list[str], int]:
    """
    将诗歌切分为数个句子。
    Args:
        poem: 诗歌的汉字内容
    Returns:
        返回两个值：
            拆分的句子列表
            句数
    """
    poem_str_list = []
    sen_num = 0
    while len(poem) % 7 == 0:
        poem_str_list.append(poem[2:7])
        poem = poem[7:]
        sen_num += 1
        if len(poem) == 0:
            return poem_str_list, sen_num
    while len(poem) % 5 == 0:
        poem_str_list.append(poem[0:5])
        poem = poem[5:]
        sen_num += 1
        if len(poem) == 0:
            return poem_str_list, sen_num


def get_first_type_main(poem: str, yun_shu: int, first_yayun: int, poem_pingze: int) -> int:
    """
    最终的判断诗歌首句格式的代码
    Args:
        yun_shu: 使用的韵书代码
        poem: 诗歌的全汉字内容
        first_yayun: 第二个判断标准
        poem_pingze: 诗歌平仄
    Returns:
        句子匹配的对应规则代码
    """
    poem_lists, sentence_num = seperate_poem(poem)
    num_lists = []
    for sentence in poem_lists:
        check_poem_str = sen_to_poem_str(sentence, yun_shu)
        poem_list = match_combinations(check_poem_str)
        num_lists.append(poem_list)
    matched_method = first_poem(num_lists, first_yayun, sentence_num, poem_pingze)
    return matched_method if len(poem) % 5 == 0 else matched_method + 4
