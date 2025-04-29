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


def cipai_confirm(ci_input: str, ci_comma: str, cipai_forms: list[list]) -> bool:
    for single_form in cipai_forms:
        single_sample_ci = single_form[0]
        if len(ci_input) != len(single_sample_ci.replace('\u3000', '')):
            continue
        cipai_form = find_punctuation_positions(single_sample_ci)
        input_form = find_punctuation_positions(ci_comma)
        right = len(set(input_form).intersection(cipai_form))
        right_rate = right / min(len(input_form), len(cipai_form))
        if right_rate > 0.7:
            return True
    return False
