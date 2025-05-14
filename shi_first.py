"""判断诗歌首句格式的模块，由于相对比较复杂，需要考虑多音字、拗救以及诗歌中可能的错误，单独设置。"""
from common import hanzi_to_pingze


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
    给定一句诗的内容，返回二四五字对应平仄代号的字符串
    Args:
        poem_sen: 诗歌某一句的内容
        yun_shu: 使用的韵书代码
    Returns:
        二四五字对应平仄代号的字符串
    """
    hanzi1 = hanzi_to_pingze(poem_sen[1], yun_shu)
    hanzi3 = hanzi_to_pingze(poem_sen[3], yun_shu)
    hanzi5 = hanzi_to_pingze(poem_sen[-1], yun_shu)
    return hanzi1 + hanzi3 + hanzi5


def get_current_pattern(sen: int, ping_ze: str) -> list[int]:
    """
    如果首句押韵，给定当前的句数，返回应该的当句格式代号列表。比如如果此时是第一句，且全诗押平声韵，那么句式格式一定是1或3
    Args:
        sen: 当前的诗句数
        ping_ze: 诗歌的平仄
    Returns:
        二四五字对应平仄代号的字符串
    """
    ping_initial = [[1, 3], [3, 1], [4, 2], [1, 3]]
    ping_cycle = [[2, 4], [3, 1], [4, 2], [1, 3]]
    ze_initial = [[2, 4], [4, 2], [1, 3], [2, 4]]
    ze_cycle = [[3, 1], [4, 2], [1, 3], [2, 4]]

    if ping_ze == "ping":
        current = ping_initial[sen] if sen <= 4 else ping_cycle[sen % 4]
    else:
        current = ze_initial[sen] if sen <= 4 else ze_cycle[sen % 4]
    return current


def first_poem(matched_lists: list[list[str]], first_yayun: int,
               sen_num: int, poem_pingze: int, match_time=0) -> int:
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
    matched_list = matched_lists[match_time]
    rule = {'111': 0, '112': 2, '121': 1, '122': 2, "211": 3, '212': 4, '221': 0, '222': 4}
    changed_set = set([rule[i] for i in matched_list])
    if first_yayun == 1:
        intersection = changed_set.intersection(set(get_current_pattern(match_time, 'ping')))
        if len(intersection) == 1:
            current = next(iter(intersection))
            place = get_current_pattern(match_time, 'ping').index(current)
            return get_current_pattern(0, 'ping')[place]
    elif first_yayun == -1:
        intersection = changed_set.intersection(set(get_current_pattern(match_time, 'ze')))
        if len(intersection) == 1:
            current = next(iter(intersection))
            place = get_current_pattern(match_time, 'ze').index(current)
            return get_current_pattern(0, 'ze')[place]
    else:
        if len(changed_set) == 1:
            result = next(iter(changed_set)) - match_time
            while result <= 0:
                result += 4
            return result
    if sen_num == match_time + 1:
        if not matched_list:
            return 1 if poem_pingze == 1 else 2
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


def seperate_poem(poem: str, set_len: int) -> tuple[list[str], int]:
    """
    将诗歌切分为数个句子。
    Args:
        poem: 诗歌的汉字内容
        set_len: 排律使用，应对字数为 70 的倍数
    Returns:
        返回两个值：
            拆分的句子列表
            句数
    """
    poem_str_list = []
    sen_num = 0
    while len(poem) > 0:
        if len(poem) % 7 == 0 and set_len != 5:
            poem_str_list.append(poem[2:7])
            poem = poem[7:]
            sen_num += 1
        else:
            poem_str_list.append(poem[0:5])
            poem = poem[5:]
            sen_num += 1
    return poem_str_list, sen_num


def get_first_type_main(poem: str, yun_shu: int, first_yayun: int, poem_pingze: int, set_len: int) -> int:
    """
    最终的判断诗歌首句格式的代码
    Args:
        yun_shu: 使用的韵书代码
        poem: 诗歌的全汉字内容
        first_yayun: 第二个判断标准
        poem_pingze: 诗歌平仄
        set_len: 一句的字数，应为5或7
    Returns:
        句子匹配的对应规则代码
    """
    poem_lists, sentence_num = seperate_poem(poem, set_len)
    num_lists = []
    for sentence in poem_lists:
        check_poem_str = sen_to_poem_str(sentence, yun_shu)
        poem_list = match_combinations(check_poem_str)
        num_lists.append(poem_list)
    matched_method = first_poem(num_lists, first_yayun, sentence_num, poem_pingze)
    return matched_method if set_len == 5 else matched_method + 4
