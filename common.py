from pingshui_rhythm import hanzi_rhythm
import new_rhythm as nw
import os

current_dir = os.path.dirname(os.path.abspath(__file__))


def show_all_rhythm(single_hanzi):
    """给定一个汉字，返回其平水、词林、新韵、通韵韵部。"""
    result = ''
    result += hanzi_rhythm(single_hanzi, showit=True)
    result += '\n中华新韵'
    result += nw.show_yun(single_hanzi, nw.xin_yun, nw.xin_hanzi) + '\n'
    result += '\n中华通韵'
    result += nw.show_yun(single_hanzi, nw.tong_yun, nw.tong_hanzi) + '\n'
    return result


def hanzi_to_yun(hanzis, yun_shu, ci_lin=False):
    """将汉字对应为韵书中韵部。"""
    yun_shu = int(yun_shu)
    rhythm_lists = []
    for hanzi in hanzis:
        if yun_shu == 1:
            if ci_lin:
                rhythm_lists.append(hanzi_rhythm(hanzi, ci_lin=True))
            else:
                rhythm_lists.append(hanzi_rhythm(hanzi))
        elif yun_shu == 2:
            rhythm_lists.append(nw.convert_yun(nw.get_new_yun(hanzi), nw.xin_yun))
        else:
            rhythm_lists.append(nw.convert_yun(nw.get_new_yun(hanzi), nw.tong_yun))
    return rhythm_lists
