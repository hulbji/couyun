"""诗歌校验模块内容，可以校验五言或七言的绝句或律诗或排律，可以校验孤雁入群的特殊格式。支持拗救。支持三韵。"""
import re
import math
from collections import defaultdict

from couyun.rhythm.pingshui_rhythm import rhythm_name, rhythm_name_trad, rhythm_correspond  # 平水韵模块
import couyun.rhythm.new_rhythm as nw
from couyun.common.common import hanzi_rhythm, hanzi_to_pingze, hanzi_to_yun, result_check
from couyun.common.num_to_cn import num_to_cn
from couyun.shi.shi_first import ShiFirst  # 判断首句格式


class ShiRhythm:
    def __init__(self, yun_shu, poem, poem_comma, is_trad):
        self.lyu_ju_rule_dict = {
            1: ['11221', '21121', '11121'],  # 平起押韵
            2: ['01122', '11212'],  # 平起不押韵
            3: ['02211'],  # 仄起押韵
            4: ['02012', '02022'],  # 仄起不押韵（含拗句）
            5: ['0211221', '0221121', '0211121'],  # 仄起押韵
            6: ['0201122', '0211212'],  # 仄起不押韵
            7: ['0102211'],  # 平起押韵
            8: ['0102012', '0102022']  # 平起不押韵（含拗句）
        }  # 一定要将拗句放在后检验

        self.sh = ['〇', '●', '◎', '�']
        self.yun_shu = yun_shu
        self.poem = poem
        self.poem_comma = poem_comma
        self.is_trad = is_trad

    @staticmethod
    def _infer_sen_len(poem: str, has_comma: bool) -> int:
        """根据是否含逗号、总长，推断句长 5 或 7"""
        if has_comma:
            return 5 if len(poem) % 5 == 0 else 7
        return 5 if len(poem) % 5 == 0 else 7

    def _infer_poem_type(self, total_lines: int) -> str:
        """总行数 -> 诗体中文名"""
        if total_lines == 4:
            return '絕句' if self.is_trad else '绝句'
        if total_lines == 8:
            return '律詩' if self.is_trad else '律诗'
        return '排律'

    @staticmethod
    def _rhythm_to_pingze(rhythm: int, yun_shu: int) -> int:
        """韵部 -> 平仄标记"""
        if yun_shu == 1:
            return 1 if rhythm < 31 else -1
        return 1 if rhythm > 0 else -1

    @staticmethod
    def _most_frequent_rhythm(nested_list: list[list[int]], lis=False) -> int | list:
        """
            统计以数字表示的韵字韵部列表中各个元素的出现频率，并找出出现次数最多的元素。
            Args:
                nested_list: 韵部列表
                lis: 是否返回为列表
            Returns:
                诗所押的韵的数字表示（如果可能出现多个，即全为多音字，那么返回第一个）
            """
        freq = defaultdict(int)
        for sublist in nested_list:
            for num in sublist:
                if num != 107:
                    freq[num] += 1
        if not freq.values():
            return [107] if lis else 107
        max_count = max(freq.values())
        most_num = [num for num, count in freq.items() if count == max_count]
        return most_num if lis else most_num[0]

    def _first_hard(self, first_hanzi: str, other_hanzis: str) -> list | bool:
        """
            分析首句是否为韵字。
            Args:
                first_hanzi: 第一句末汉字
                other_hanzis: 其余所有韵脚汉字
            Returns:
                返回共同韵部的列表，如果没有共同韵部，返回 False。
            """
        if self.yun_shu == 1:
            first_list = hanzi_rhythm(first_hanzi, self.is_trad)  # 平水
            other_list = [hanzi_rhythm(other_hanzi, self.is_trad) for other_hanzi in other_hanzis]
        else:  # 新韵通韵
            yun_shu = nw.xin_yun if self.yun_shu == 2 else nw.tong_yun
            first_list = nw.convert_yun(nw.get_new_yun(first_hanzi), yun_shu)
            other_list = [nw.convert_yun(nw.get_new_yun(other_hanzi), yun_shu) for other_hanzi in other_hanzis]
        all_unknown = True
        for _ in other_list:
            if _ != [107]:
                all_unknown = False
                break
        if all_unknown:
            return first_list
        duplicates = set(first_list) & set(self._most_frequent_rhythm(other_list, lis=True))
        if self.yun_shu == 1 and not duplicates:  # 使用平水韵时首句检测词林，首句可能押邻韵
            first_ci = hanzi_rhythm(first_hanzi, self.is_trad, ci_lin=True)
            second_ci = hanzi_rhythm(other_hanzis[0],self.is_trad, ci_lin=True)
            duplicates = set(first_ci) & set(second_ci)
        if duplicates:
            return list(duplicates)
        return False

    def _poetry_yun_jiao(self, set_num: int = None) -> tuple[str, list | bool, str, str]:
        """
            提取一首诗中所有的韵字。
            Args:
                set_num: 对于70字倍数的排律，需要指定其一句的字数。
            Returns:
                返回四个值：
                    韵字字符串
                    第一句末汉字与其余韵句末汉字共同的韵列表，如果没有共同韵部，返回 False
                    第一句末汉字
                    第二句末汉字
            """
        poem_length = len(self.poem)
        indices = []
        if poem_length % 10 == 0 and set_num != 7:
            indices = list(range(10, poem_length + 1, 10))
        elif poem_length % 14 == 0:
            indices = list(range(14, poem_length + 1, 14))
        extracted = [self.poem[hanzi_yun_jiao - 1] for hanzi_yun_jiao in indices]
        other_hanzis = ''
        pos = poem_length
        if poem_length % 5 == 0 and set_num != 7:
            first_hanzi = self.poem[4]
            while pos > 8:
                other_hanzis += self.poem[pos - 1]
                pos -= 10
        else:
            first_hanzi = self.poem[6]
            while pos > 12:
                other_hanzis += self.poem[pos - 1]
                pos -= 14  # 或许可以简化这段代码
        first_yayun = self._first_hard(first_hanzi, other_hanzis)
        if first_yayun:
            extracted.insert(0, first_hanzi)
        return ''.join(extracted), first_yayun, first_hanzi, other_hanzis

    def _lyu_ju(self, sentence: str, rule: int, poem_pingze: int,
                input_flag: int = 0) -> tuple[list[bool], int, str, str]:
        """
            判断一个句子是不是律句，包括拗句。
            Args:
                sentence: 诗的单个句子
                rule: 句子匹配的对应规则代码
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
            self.lyu_ju_rule_dict[1] = ['11221', '21121', '11121', '21221']  # 仄韵无孤平
            self.lyu_ju_rule_dict[4] = ['02012']
            self.lyu_ju_rule_dict[8] = ['0102012']  # 仄韵无“中仄中仄仄”拗句，因为没法对句救
        else:
            self.lyu_ju_rule_dict[1] = ['11221', '21121', '11121']
            self.lyu_ju_rule_dict[4] = ['02012', '02022']
            self.lyu_ju_rule_dict[8] = ['0102012', '0102022']
        if input_flag == 2:
            patterns = self.lyu_ju_rule_dict[rule][-2:]
        else:
            patterns = self.lyu_ju_rule_dict[rule]

        sentence_pattern = ''.join(hanzi_to_pingze(char, self.yun_shu, self.is_trad) for char in sentence)

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
        hint_word += f'{hanzi_rule}'

        ao_word = ''
        if matched_rule in ['02022', '0102022']:  # 拗救需提示
            input_flag = 2
            ao_word += '“中仄中仄仄”拗句，為對句相救。' if self.is_trad else "“中仄中仄仄”拗句。为对句相救。"
        elif matched_rule in ['0211212', '11212']:
            input_flag = 1
            ao_word += "“平平仄平仄”拗句，為本句自救。" if self.is_trad else "“平平仄平仄”拗句，为本句自救。"
        else:
            input_flag = 0
        return match_list, input_flag, hint_word, ao_word

    def _check_real_first(self, first: list | bool, second: int, first_sen: str, sen_type: int) -> tuple[int, int]:
        """
            检测可能出现的特殊情况：首句不押韵但是第一句末字平仄与第二句末字同，此时修整第一句格式，判断为押韵但是此处用韵有误。
            Args:
                first: 第一个判断标准。即两字共同的韵列表，若无则为 False
                second: 第二个判断标准，如果为 1，则两字均为平，如果为 -1，则两字均为仄，如果为 0，则表示平仄不同
                first_sen: 诗的第一句内容
                sen_type: 句子匹配的对应规则代码
            Returns:
                返回两个值：
                    修正后的 sen_type
                    修正后的 second
            """
        last1 = hanzi_to_pingze(first_sen[-1], self.yun_shu, self.is_trad)
        last3 = hanzi_to_pingze(first_sen[-3], self.yun_shu, self.is_trad)
        if last1 not in ['0', '3']:
            return sen_type, second
        change_dict = {1: 2, 3: 4, 4: 3, 2: 1, 5: 6, 6: 5, 7: 8, 8: 7}
        if not first and second:  # 在第一句末是多音字情况下，那就一定不押韵
            if last1 == '0':
                return change_dict[sen_type], 0
            else:  # 如果第一句末是生僻字，默认与第一句倒数第三个字平仄相反
                if last3 == '1' and second == 1:
                    return change_dict[sen_type], 0
                elif last3 == '2' and second == -1:
                    return change_dict[sen_type], 0
        if first and second:  # 押不押韵得看格式以及倒数第三个字
            if sen_type in [3, 7] and last3 == '1':
                return change_dict[sen_type], 0
            if sen_type in [2, 6] and last3 == '2':
                return change_dict[sen_type], 0
        return sen_type, second

    @staticmethod
    def _which_sentence(first_sen_type: int, how_many: int, first_yayun: int, poem_pingze: int) -> list[int]:
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

    def _yun_jiao_show(self, zi: str, poem_rhythm_num: int, is_first_sentence: bool) -> str:
        """
            展示韵脚。
            Args:
                zi: 韵脚汉字
                poem_rhythm_num: 诗所押的韵的数字表示
                is_first_sentence: 是否为首句
            Returns:
                韵脚的展示结果
            """
        yun_jiao_content = ''
        zi_list = []
        yun = '韻' if self.is_trad else '韵'
        lin = '鄰' if self.is_trad else '邻'
        if self.yun_shu == 1:
            zi_rhythm = hanzi_rhythm(zi, self.is_trad)
            zi_rhythm.sort()
            using_name = rhythm_name_trad if self.is_trad else rhythm_name
            for _ in zi_rhythm:
                zi_list.append(''.join(using_name)[_ - 1])
        else:
            if self.yun_shu == 2:
                zi_rhythm = nw.convert_yun(nw.get_new_yun(zi), nw.xin_yun)
            else:
                zi_rhythm = nw.convert_yun(nw.get_new_yun(zi), nw.tong_yun)
            if zi_rhythm != [107]:
                if self.yun_shu == 2:
                    using_xin = nw.xin_hanzi_trad if self.is_trad else nw.xin_hanzi
                    for _ in zi_rhythm:
                        zi_list.append(''.join(using_xin)[int(math.fabs(_)) - 1])
                else:
                    using_tong = nw.tong_hanzi_trad if self.is_trad else nw.tong_hanzi
                    for _ in zi_rhythm:
                        zi_list.append(''.join(using_tong)[int(math.fabs(_)) - 1])
        if_ya_yun = True if poem_rhythm_num in zi_rhythm else False
        if not if_ya_yun and is_first_sentence and poem_rhythm_num <= 30 and self.yun_shu == 1:  # 首句用邻韵
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
                yun_jiao_content += f'{"、".join(zi_list)}{yun} ' + f'不押{yun} '
            else:
                yun_jiao_content += f'{"、".join(zi_list)}{yun} ' + f'用{lin}韵 押{yun} '
        else:
            yun_jiao_content += f'{"、".join(zi_list)}{yun} ' + f'{"" if if_ya_yun else "不"}押{yun} '
        if '？' in yun_jiao_content or yun_jiao_content == f'{yun} 不押{yun} ':
            yun_jiao_content = f'不知{yun}部'  # 生僻字处理模块
        return yun_jiao_content

    def _sentence_show(self, show_sentence: str, sen_ge_lyu: list[bool]) -> str:
        """
            展示律句的平仄情况。
            Args:
                show_sentence: 展示的句子
                sen_ge_lyu: 表示该字平仄正确与否的列表
            Returns:
                实际展示格律的字符串，用“〇、中、错”表示
            """
        sp_zi = []
        ge_lju_show = ''
        for char in show_sentence:
            ping_ze = hanzi_to_pingze(char, self.yun_shu, self.is_trad)
            sp_zi.append('duo') if ping_ze == '0' else sp_zi.append('no') if ping_ze != '3' else sp_zi.append('pi')

        for i, is_valid in enumerate(sen_ge_lyu):
            if is_valid:
                ge_lju_show += self.sh[2] if sp_zi[i] == 'duo' else self.sh[0] if sp_zi[i] != 'pi' else self.sh[3]
            else:
                ge_lju_show += self.sh[1] if sp_zi[i] != 'pi' else self.sh[3]
        return ge_lju_show

    def _special_two_pingze(self, hanzi1: str, hanzi2: str, poem_pingze: int) -> int:
        """
            根据第一句末字与第二句末字，诗的平仄得到第二个判断标准。
            Args:
                hanzi1: 第一句末汉字
                hanzi2: 第二句末汉字
                poem_pingze: 全诗的押韵平仄，1平 -1仄
            Returns:
                第二个判断标准（两者平仄是否相同）
            """
        ping_ze1 = hanzi_to_pingze(hanzi1, self.yun_shu, self.is_trad)
        if ping_ze1 == '3':
            ping_ze1 = '0'
        ping_ze2 = hanzi_to_pingze(hanzi2, self.yun_shu, self.is_trad)
        if ping_ze2 == '3':
            ping_ze2 = '0'
        if ping_ze1 + ping_ze2 in ['12', '21']:
            return 0  # 不一致
        if '1' in ping_ze1 + ping_ze2 and poem_pingze == 1:
            return 1  # 一致且为平
        if '2' in ping_ze1 + ping_ze2 and poem_pingze == -1:
            return -1  # 一致且为仄
        if ping_ze1 + ping_ze2 == '00':
            return 1 if poem_pingze == 1 else -1
        return 0

    def _is_all_duo_yin(self, yun_jiao_content: str) -> bool:
        """
            判断韵脚字是不是全部是多音字。
            Args:
                yun_jiao_content: 韵脚汉字的字符串
            Returns:
                是否全部为多音字
            """
        for i in yun_jiao_content:
            ping_ze = hanzi_to_pingze(i, self.yun_shu, self.is_trad)
            if ping_ze != '0':
                return False
        return True

    def _check_sentence_lengths(self):
        """
            将文本按照标点符号分割，计算所有片段的长度如果所有片段长度一致，返回该长度；否则返回 None
            Returns:
                所有片段长度一致时返回该长度，否则返回 None
            """
        punctuation_pattern = r'[.!?;:,，。？！；：、]'
        segments = re.split(punctuation_pattern, self.poem_comma)
        non_empty_segments = [segment.strip() for segment in segments if segment.strip()]
        return len(non_empty_segments[0])

    @staticmethod
    def _fix_f_rhythm(f_rhythm, this_rhythm):
        if not f_rhythm:
            return None
        inter = set(f_rhythm) & {this_rhythm}
        return next(iter(inter)) if inter else f_rhythm[0]

    def _build_report(self, maybe_len, main_rhythm, f_rhythm,
                      f_hanzi, s_hanzi, pingze):
        """为单平仄方向生成完整报告"""
        sen_len = maybe_len or self._infer_sen_len(self.poem, self.poem_comma != self.poem)
        total_lines = len(self.poem) // sen_len
        poem_type = self._infer_poem_type(total_lines)

        report = f'{num_to_cn(sen_len)}言{poem_type}\n'

        s_rhythm = self._special_two_pingze(f_hanzi, s_hanzi, pingze)
        first_checker = ShiFirst(self.poem, self.yun_shu, s_rhythm, pingze, sen_len, self.is_trad)
        first_type, s_rhythm = self._check_real_first(f_rhythm, s_rhythm,
                                                      self.poem[:sen_len],
                                                      first_checker.main_first())
        rule_list = self._which_sentence(first_type, total_lines, s_rhythm, pingze)

        # 逐句扫描
        yun_positions = list(range(2, total_lines + 1, 2))
        if s_rhythm:
            yun_positions.append(1)

        hint_buf = sen_buf = ge_buf = ao_buf = ''
        sen_mode = 0  # 默认设置为正常句式
        lian = "聯" if self.is_trad else '联'
        for idx, rule in enumerate(rule_list):
            sentence = self.poem[sen_len * idx: sen_len * (idx + 1)]
            ge_lju, sen_mode, hint, ao = self._lyu_ju(sentence, rule, pingze, sen_mode)
            hint_buf += hint + '\u3000'
            sen_buf += sentence + '\u3000'
            ao_buf += (f'\n本{lian}{"上" if idx % 2 == 0 else "下"}句' + ao) if ao else ''
            ge_buf += self._sentence_show(sentence, ge_lju) + '\u3000'

            # 逢押韵句
            if idx + 1 in yun_positions:
                yun_info = self._yun_jiao_show(sentence[-1], main_rhythm, idx == 0)
                ge_buf = self._mark_yun(ge_buf, yun_info)
                report += f'\n{hint_buf}\n{sen_buf}{yun_info}\n{ge_buf}{ao_buf}\n'
                hint_buf = sen_buf = ge_buf = ao_buf = ''

        return report

    @staticmethod
    def _mark_yun(ge_buf: str, yun_info: str) -> str:
        """在句尾标记押韵或不押韵"""
        if '不押韵' in yun_info:
            return ge_buf[:-2] + '■'
        if '不' not in yun_info:
            return ge_buf[:-2] + '□'
        return ge_buf

    @staticmethod
    def _merge_results(results: list[str]) -> str:
        """多候选结果合并策略，这里简单取最后一个非空"""
        best = ''
        for r in results:
            best = result_check(best, r)
        return best

    def main_shi(self) -> str | int:
        """
        诗歌格律校验主入口
        Returns:
            校验文本 或 错误码 1/2
        """
        # 1. 快速失败：句长不合法
        if self.poem_comma != self.poem:
            sen_len = self._check_sentence_lengths()
            if sen_len not in (5, 7):
                return 1
            candidates = [sen_len]
        else:
            candidates = [5, 7] if len(self.poem) >= 70 and len(self.poem) % 70 == 0 else [None]

        # 2. 对每种候选句长做校验
        results = []
        for maybe_len in candidates:
            yun_jiaos, f_rhythm, f_hanzi, s_hanzi = self._poetry_yun_jiao(maybe_len)
            rhythms = [hanzi_to_yun(y, self.yun_shu, self.is_trad) for y in yun_jiaos]

            # 2.1 未知韵部过多
            if all(r == [107] or not r for r in rhythms):
                return 2

            main_rhythm = self._most_frequent_rhythm(rhythms)
            f_rhythm = self._fix_f_rhythm(f_rhythm, main_rhythm)

            # 2.2 平仄标记
            pingze = self._rhythm_to_pingze(main_rhythm, self.yun_shu)
            if self._is_all_duo_yin(yun_jiaos):
                pingze = 0
            pingze_list = [1, -1] if pingze == 0 else [pingze]

            # 2.3 对每种平仄方向生成报告
            for pz in pingze_list:
                results.append(self._build_report(maybe_len, main_rhythm, f_rhythm,
                                                  f_hanzi, s_hanzi, pz))

        return self._merge_results(results).lstrip()
