def find_punctuation_positions(text: str) -> list[int]:
    comma_syms = {',', '.', '?', '!', ':', "，", "。", "？", "！", "、", "：", '\u3000'}
    position = []
    correct = 1
    is_comma = False
    for idx, ch in enumerate(text):
        if ch in comma_syms:
            if not is_comma:
                position.append(idx - correct)
            correct += 1
            is_comma = True
        else:
            is_comma = False
    return position


def cipai_confirm(ci_input: str, ci_comma: str, sg_cipai_forms: list[dict]) -> list:
    right_list = []
    form_count = 0
    for single_form in sg_cipai_forms:
        single_sample_ci = '\u3000'.join(single_form['ci_sep'])
        if len(ci_input) != len(single_form['ge_lyu_str']):
            form_count += 1
            continue
        cipai_form = find_punctuation_positions(single_sample_ci)
        input_form = find_punctuation_positions(ci_comma)
        right = len(set(input_form).intersection(cipai_form))
        right_rate = right / len(set(input_form) | set(cipai_form))
        if right_rate > 0.7:
            right_list.append(form_count)
        form_count += 1
    return right_list
