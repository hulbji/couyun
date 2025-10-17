"""词校验模块内容，支持三韵。"""

from couyun.ci.ci_search import ci_type_extraction, search_ci, ci_idx
from couyun.ci.cipai_word_counts import qin_num, long_num
from couyun.common.common import hanzi_to_pingze, result_check, hanzi_to_yun
import couyun.rhythm.new_rhythm as nw
from collections import Counter
from couyun.common.num_to_cn import num_to_cn


class YunData:
    def __init__(self, pos: int, hanzi: str, yun_num: list[int]):
        self.pos = pos
        self.hanzi = hanzi
        self.yun_num = yun_num
        self.xie_yun = False
        self.group = None
        self.is_yayun = False


class YunDataProcessor:
    def __init__(self, yun_jiao_pos: list[int], yun_list: list[str], yun_jiao_class: dict,
                 yun_num_list: list[list[int]]):
        self.yun_data = [
            YunData(pos, hanzi, yun_num)
            for pos, hanzi, yun_num in zip(yun_jiao_pos, yun_list, yun_num_list)
        ]
        self.yun_jiao_class = yun_jiao_class
        self.xie_yun_map = {}
        self.group_map = {}
        self.group_most_common = {}

        for group, positions in yun_jiao_class.items():
            for p in positions:
                absolute_p = abs(p)
                self.xie_yun_map[absolute_p] = p < 0
                self.group_map[absolute_p] = group

    def process(self):
        for yun in self.yun_data:
            yun.xie_yun = self.xie_yun_map.get(yun.pos, False)
            yun.group = self.group_map.get(yun.pos, None)

        group_min_pos = {}
        for yun in self.yun_data:
            if yun.group is not None:
                group_min_pos[yun.group] = min(
                    group_min_pos.get(yun.group, yun.pos), yun.pos)

        sorted_groups = sorted(group_min_pos.items(), key=lambda x: x[1])
        new_group_map = {group: idx + 1 for idx, (group, _) in enumerate(sorted_groups)}

        for yun in self.yun_data:
            if yun.group is not None:
                yun.group = new_group_map[yun.group]

        for group_name in set(yun.group for yun in self.yun_data):
            elements = []
            for yun in self.yun_data:
                if yun.group == group_name:
                    yun_num = yun.yun_num
                    if yun.xie_yun:
                        yun_num = [-num for num in yun_num]
                    elements.extend(yun_num)
            if elements:
                counter = Counter(elements)
                most_common_element = counter.most_common(1)[0][0]
                self.group_most_common[group_name] = most_common_element
            else:
                self.group_most_common[group_name] = None

        for yun in self.yun_data:
            most_common = self.group_most_common.get(yun.group)
            if most_common is not None:
                yun_num = yun.yun_num
                if yun.xie_yun:
                    yun_num = [-num for num in yun_num]
                if most_common in yun_num:
                    yun.is_yayun = True

        result = []
        for yun in self.yun_data:
            result.append({
                'pos': yun.pos,
                'hanzi': yun.hanzi,
                'yun_num': yun.yun_num,
                'xie_yun': yun.xie_yun,
                'group': yun.group,
                'is_yayun': yun.is_yayun,
            })
        # print(result)
        return result


def _yun_data_process(yun_jiao_pos: list[int], yun_list: list[str], yun_jiao_class: dict,
                      yun_num_list: list[list[int]]):
    processor = YunDataProcessor(yun_jiao_pos, yun_list, yun_jiao_class, yun_num_list)
    return processor.process()


class CiRhythm:
    def __init__(self, yun_shu: int, ci_pai_name: str, ci_content: str, ci_comma: str,
                 give_type: str, ci_pu: int, is_trad: bool):
        self.yun_shu = yun_shu
        self.ci_pai_name = ci_pai_name
        self.ci_content = ci_content
        self.ci_comma = ci_comma
        self.give_type = give_type
        self.ci_pu = ci_pu
        self.show_mark = ['◎', '●', '〇', '�']
        self.is_trad = is_trad

    def _ci_yun_list_to_hanzi_yun(self, yun_list: list[int]):
        """
        将数字表示的韵部转换为汉字表示的韵部
        Args:
            yun_list: 单个字的韵数字代码列表
        Returns:
            汉字表示的韵部
        """
        yun_shu = int(self.yun_shu)
        if yun_shu == 1:
            hanzi_yun_list = []
            for i in yun_list:
                if i < 0:
                    i = -i
                    ping_ze = '仄'
                else:
                    if i > 14:
                        ping_ze = '入聲' if self.is_trad else '入声'
                    else:
                        ping_ze = '平'
                hanzi_yun_list.append(num_to_cn(i) + '部' + ping_ze)
            return '、'.join(hanzi_yun_list)
        elif yun_shu == 2:
            using_xin = nw.xin_hanzi_trad if self.is_trad else nw.xin_hanzi
            return nw.show_yun(yun_list, nw.xin_yun, using_xin)
        using_tong = nw.tong_hanzi_trad if self.is_trad else nw.tong_hanzi
        return nw.show_yun(yun_list, nw.tong_yun, using_tong)

    @staticmethod
    def _yun_right_list(ci_seperate_lis: list[str], ci_content_right: list[bool | str]):
        """
        根据分割好的词列表以及布尔平仄正误列表得到分割好的字符串平仄正误列表
        Args:
            ci_seperate_lis: 分割好的词列表
            ci_content_right: 布尔平仄正误列表
        Returns:
            分割好的字符串平仄正误列表
        """
        conversion = {True: '〇', 'duo': '◎', False: '●', 'pi': '？'}
        result_list = []
        ptr = 0

        for poem in ci_seperate_lis:
            non_space_chars = poem.replace('\u3000', '')
            non_space_count = len(non_space_chars)
            sub_right = ci_content_right[ptr:ptr + non_space_count]
            converted = []
            j = 0
            for char in poem:
                if char == '\u3000':
                    converted.append('\u3000')
                else:
                    converted_char = conversion.get(sub_right[j], sub_right[j])
                    converted.append(converted_char)
                    j += 1
            ptr += non_space_count
            result_list.append(''.join(converted))
        return result_list

    def _ping_ze_right(self, cipai: str) -> list[str | bool]:
        """
        检验一首词是否符合一个词牌特定格式的平仄。
        Args:
            cipai: 删去标识词句读韵等的词的格律
        Returns:
            平仄正误的列表 True对 False错 "duo"多音字无法判断
        """
        yun_shu = int(self.yun_shu)
        result = []
        for hanzi_num in range(len(self.ci_content)):
            ping_ze = hanzi_to_pingze(self.ci_content[hanzi_num], yun_shu, self.is_trad)
            if ping_ze == '0':
                result.append('duo')
            elif ping_ze == '3':
                result.append('pi')
            elif ping_ze == '1':
                result.append(True) if cipai[hanzi_num] in '平中' else result.append(False)
            else:
                result.append(True) if cipai[hanzi_num] in "仄中" else result.append(False)
        return result

    def _replace_user_ci_text(self, ci_cut_list: list[str]) -> list[str]:
        """
        根据输入的词内容与分割好的例词列表分割词内容。
        Args:
            ci_cut_list: 分割好的例词列表
        Returns:
            输入的词分割好的例词列表
        """
        merged_ci = ''.join(ci_cut_list)
        my_hanzi = list(self.ci_content)
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

    def _show_ci(self, ge_lyu_final: list, text_final: list, yun_final: list, your_lyu_final: list) -> str:
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
        _map = str.maketrans("换叠读举儿韵", "換疊讀舉兒韻")
        for _ in range(len(ge_lyu_final)):
            original_single_ge_lyu = ge_lyu_final[_]
            if self.is_trad:
                original_single_ge_lyu = original_single_ge_lyu.translate(_map)
            result += original_single_ge_lyu + '\n'
            result += text_final[_] + '\u3000'
            result += yun_final[_] + '\n'
            if "不押韵" in yun_final[_] or '不押韻' in yun_final[_]:
                result += your_lyu_final[_][:-1] + '■' + '\n\n'
            if "不" not in yun_final[_]:
                if your_lyu_final[_][-1] == '●':
                    result += your_lyu_final[_][:-1] + '■' + '\n\n'
                else:
                    result += your_lyu_final[_][:-1] + '□' + '\n\n'
            if "不知韵部" in yun_final[_] or '不知韻部' in yun_final[_]:
                result += your_lyu_final[_] + '\n\n'
        return result.rstrip() + '\n'

    @staticmethod
    def _find_punctuation_positions(text: str) -> list[int]:
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

    def _cipai_confirm(self, sg_cipai_forms: list[dict]) -> list:
        right_list = []
        zi_conunt = len(self.ci_content)
        form_count = 0
        for single_form in sg_cipai_forms:
            single_sample_ci = '\u3000'.join(single_form['ci_sep'])
            if zi_conunt != len(single_form['ge_lyu_str']):
                form_count += 1
                continue
            cipai_form = self._find_punctuation_positions(single_sample_ci)
            input_form = self._find_punctuation_positions(self.ci_comma)
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

    def _collect_candidate_ci_nums(self) -> list[str] | int:
        """返回要试的词牌编号列表；无法继续时直接返回错误码 int。"""
        if self.ci_pai_name:  # 用户给了词牌名
            ci_num = search_ci(self.ci_pai_name, self.ci_pu)
            if ci_num not in ['err1', 'err2']:
                return [ci_num]
            if ci_num == 'err1':
                return 0
            return 4
        # 按字数反查
        length = len(self.ci_content)
        check_num = qin_num if self.ci_pu == 1 else long_num
        if length not in check_num:
            return 3
        cand = [n for n in check_num[length] if self._cipai_confirm(ci_type_extraction(n, self.ci_pu))]
        return cand or 3

    def _build_single_ci_report(self, ci_num: str) -> str | int:
        """为单个词牌生成最优格式报告。"""
        type_list = ci_type_extraction(ci_num, self.ci_pu)
        ok_types = self._cipai_confirm(type_list)
        if not ok_types:
            return 1
        use_types, warn = self._filter_given_type(ok_types)
        if warn == 'error':
            return 2
        best = ''
        for fmt_id in use_types:
            report = self._one_format_report(ci_num, type_list, fmt_id)
            best = result_check(best, report)

        # 2. 拼装词牌名 + 降级提示（若有）
        if not self.ci_pai_name:
            best = ci_idx['ci_num']['names_trad'][0] + '\n' + best
        if warn:
            if self.is_trad:
                warn_word = "給定格式與實際相差過大或沒有此格式，將另行匹配。\n"
            else:
                warn_word = "给定格式与实际相差过大或没有此格式，将另行匹配。\n"
            best = warn_word + best
        return best

    def _filter_given_type(self, ok_types: list[int]) -> tuple[list[int], bool | str]:
        """
        返回 (真正要跑的格式号列表, 是否需要给出降级提示)
        用户没给、给错都给全列表；给对了就给单例。
        """
        gt = self.give_type
        if not gt:
            return ok_types, False
        if not gt.isdecimal() or int(gt) == 0:
            return [], 'error'
        idx = int(gt) - 1
        if idx in ok_types:
            return [idx], False  # 用户给对了
        return ok_types, True

    def _normalize_given_type(self, ok_types: list[int]) -> list[int] | int:
        """把用户输入的 give_type 转成合格格式号列表；无法匹配返回 -1。"""
        gt = self.give_type
        if not gt:
            return ok_types
        if gt.isnumeric():
            idx = int(gt) - 1
            return [idx] if idx in ok_types else -1
        return -1

    def _one_format_report(self, ci_num: str, type_list: list, fmt_id: int) -> str:
        """生成「格 x」的完整校验文本。"""
        fmt = type_list[fmt_id]
        remain = fmt['ge_lyu_str']
        yun_pos = fmt['rhyme_pos']
        yun_class = fmt['yun_classify']
        real_lis = fmt['ci_sep']
        cut_lis = fmt['ge_lyu_sep']

        my_text = self._replace_user_ci_text(real_lis)
        yun_nums = [hanzi_to_yun(self.ci_content[i], self.yun_shu, self.is_trad, ci_lin=True)
                    for i in yun_pos]
        yun_show = _yun_data_process(yun_pos, [self.ci_content[i] for i in yun_pos],
                                     yun_class, yun_nums)
        yun_info = [self._fmt_yun_info(s) for s in yun_show]

        pingze_right = self._ping_ze_right(remain)
        yun_final = self._yun_right_list(real_lis, pingze_right)

        report = f'你的格式为 格{num_to_cn(fmt_id + 1)}\n\n'
        report += self._show_ci(cut_lis, my_text, yun_info, yun_final)

        # 水龙吟格二十四特殊处理
        if fmt_id == 23 and int(ci_num) == 658:
            report += (f'\n仄句\n{self.ci_content[-1]}\n'
                       f'{self.show_mark[int(hanzi_to_pingze(self.ci_content[-1], self.yun_shu, self.is_trad))]}\n')
        return report

    def _fmt_yun_info(self, d: dict) -> str:
        """把单个韵脚字典变成人类可读串。"""
        hanzi_yun = self._ci_yun_list_to_hanzi_yun(d['yun_num'])
        # group = f"第{d['group']}组韵"  如果这里报错就看看韵表
        group = f'第{num_to_cn(d["group"])}組韻' if self.is_trad else f"第{num_to_cn(d['group'])}组韵"
        yayun = '' if d['is_yayun'] else '不'
        info = f'{hanzi_yun} {group} {yayun}押韻' if self.is_trad else f'{hanzi_yun} {group} {yayun}押韵'
        if '零' in info or len(info) == 9:
            return '不知韻部' if self.is_trad else '不知韵部'
        return info

    def main_ci(self) -> str | int:
        """
        校验词牌的最终入口
        Returns:
            校验文本 | 错误码 0/1/2/3
        """
        # 1. 确定要试的词牌编号列表
        ci_nums = self._collect_candidate_ci_nums()
        if isinstance(ci_nums, int):  # 0 或 3
            return ci_nums

        # 2. 对每个词牌、每个合格格式生成报告，再 pairwise 选最优
        best = ''
        for ci_num in ci_nums:
            report = self._build_single_ci_report(ci_num)
            best = result_check(best, report)
        return best
