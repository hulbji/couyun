"""判断诗歌首句格式的模块，由于相对比较复杂，需要考虑多音字、拗救以及诗歌中可能的错误，单独设置。"""
from common import hanzi_to_pingze


class ShiFirst:
    def __init__(self, poem, yun_shu, first_yayun, poem_pingze, set_len):
        self.poem = poem
        self.yun_shu = yun_shu
        self.first_yayun = first_yayun
        self.poem_pingze = poem_pingze
        self.set_len = set_len

    @staticmethod
    def _match_combinations(poem_str: str) -> list[str]:
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

    def _sen_to_poem_str(self, poem_sen: str) -> str:
        """
        给定一句诗的内容，返回二四五字对应平仄代号的字符串
        Args:
            poem_sen: 诗歌某一句的内容
        Returns:
            二四五字对应平仄代号的字符串
        """
        hanzi1 = hanzi_to_pingze(poem_sen[1], self.yun_shu)
        hanzi3 = hanzi_to_pingze(poem_sen[3], self.yun_shu)
        hanzi5 = hanzi_to_pingze(poem_sen[-1], self.yun_shu)
        return hanzi1 + hanzi3 + hanzi5

    @staticmethod
    def _get_current_pattern(sen: int, ping_ze: str) -> list[int]:
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
            current = ping_initial[sen] if sen <= 3 else ping_cycle[sen % 4]
        else:
            current = ze_initial[sen] if sen <= 3 else ze_cycle[sen % 4]
        return current

    def _first_poem(self, matched_lists: list[list[str]], sen_num: int, match_time=0) -> int:
        """
        递归计算每一个句子，直到其匹配到特定的格式，得到首句的格式。
        Args:
            matched_lists: 每一句匹配到的可能的组合结果的列表
            sen_num: 诗的句数
            match_time:匹配次数，上限为诗的句数
        Returns:
            句子匹配的规则代码（五言，七言需要在此基础上 +4）
        """
        matched_list = matched_lists[match_time]
        rule = {'111': 0, '112': 2, '121': 1, '122': 2, "211": 3, '212': 4, '221': 0, '222': 4}
        changed_set = set([rule[i] for i in matched_list])
        if self.first_yayun == 1:
            intersection = changed_set.intersection(set(self._get_current_pattern(match_time, 'ping')))
            if len(intersection) == 1:
                current = next(iter(intersection))
                place = self._get_current_pattern(match_time, 'ping').index(current)
                return self._get_current_pattern(0, 'ping')[place]
        elif self.first_yayun == -1:
            intersection = changed_set.intersection(set(self._get_current_pattern(match_time, 'ze')))
            if len(intersection) == 1:
                current = next(iter(intersection))
                place = self._get_current_pattern(match_time, 'ze').index(current)
                return self._get_current_pattern(0, 'ze')[place]
        else:
            if len(changed_set) == 1:
                result = next(iter(changed_set)) - match_time
                while result <= 0:
                    result += 4
                return result
        if sen_num == match_time + 1:
            if not matched_list:
                return 1 if self.poem_pingze == 1 else 2
            co_rule = rule[matched_list[0]]
            if co_rule == 0:
                if matched_list[0] == '111' and self.poem_pingze > 0:
                    co_rule = 1
                elif matched_list[0] == '221' and self.poem_pingze > 0:
                    co_rule = 3
                elif matched_list[0] == '111' and self.poem_pingze < 0:
                    co_rule = 2
                else:
                    co_rule = 4
            if co_rule in [2, 4] and self.poem_pingze > 0:
                co_rule -= 1
            if co_rule in [1, 3] and self.poem_pingze < 0:
                co_rule += 1
            return co_rule if self.first_yayun else (co_rule + 1) % 4
        match_time += 1
        return self._first_poem(matched_lists, sen_num, match_time)

    def _seperate_poem(self) -> tuple[list[str], int]:
        """
        将诗歌切分为数个句子。
        Returns:
            返回两个值：
                拆分的句子列表
                句数
        """
        proceed_poem = self.poem
        poem_str_list = []
        sen_num = 0
        while len(proceed_poem) > 0:
            if len(proceed_poem) % 7 == 0 and self.set_len != 5:
                poem_str_list.append(proceed_poem[2:7])
                proceed_poem = proceed_poem[7:]
                sen_num += 1
            else:
                poem_str_list.append(proceed_poem[0:5])
                proceed_poem = proceed_poem[5:]
                sen_num += 1
        return poem_str_list, sen_num

    def main_first(self) -> int:
        """
        最终的判断诗歌首句格式的代码
        Returns:
            句子匹配的对应规则代码
        """
        poem_lists, sentence_num = self._seperate_poem()
        num_lists = []
        for sentence in poem_lists:
            check_poem_str = self._sen_to_poem_str(sentence)
            poem_list = self._match_combinations(check_poem_str)
            num_lists.append(poem_list)
        matched_method = self._first_poem(num_lists, sentence_num)
        return matched_method if self.set_len == 5 else matched_method + 4
