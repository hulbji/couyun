import re

# =========================
# 1. 显式定义“符号”的 Unicode 区间（白名单）
# =========================
SYMBOL_PATTERN = re.compile(
    r"["
    r"\u2000-\u206F"   # General Punctuation
    r"\u3000-\u303F"   # CJK 标点
    r"\uFF00-\uFFEF"   # 全角符号
    r"\u2600-\u26FF"   # 杂项符号
    r"\u2700-\u27BF"   # Dingbats
    r"\u2460-\u2473"   # ①-⑳ 带圈数字
    r"\u2776-\u277F"   # ❶-❿ 带圈数字（黑底）
    r"\u2474-\u2487"   # ⑴-⒇ 带括号数字
    r"!\"#$%&'()*+,-./:;<=>?@[\\\]^_`{|}~"
    r"\r\t\v\f"      # 控制字符
    r" \u3000"         # 半角空格 + 全角空格
    r"]"
)

# =========================
# 2. 显式成对符号（只删除符号本身，不删中间内容）
# =========================
PAIRED_SYMBOLS = [
    ("“", "”"), ("‘", "’"), ("\"", "\""), ("'", "'"),
    ("(", ")"), ("[", "]"), ("{", "}"),
    ("<", ">"), ("《", "》"), ("【", "】"), ("（", "）")
]


def remove_any_brackets_content(text: str) -> str:
    """
    删除任意类型括号及其内部内容（支持中英文、混用、非规范嵌套）
    只要遇到左括号就进入“丢弃模式”，直到遇到任意右括号为止
    """
    text = text.replace("\n", "。")
    left_brackets = set("([{（【<")
    right_brackets = set(")]}）】>")

    result = []
    in_bracket = False

    for ch in text:
        if ch in left_brackets:
            in_bracket = True
            continue

        if ch in right_brackets:
            in_bracket = False
            continue

        if not in_bracket:
            result.append(ch)

    return "".join(result)


def is_symbol(ch: str) -> bool:
    """判断字符是否属于“符号白名单”"""
    return SYMBOL_PATTERN.match(ch) is not None


def process_text(text: str):

    text = remove_any_brackets_content(text)

    temp_text = text
    for left, right in PAIRED_SYMBOLS:
        temp_text = temp_text.replace(left, "").replace(right, "")

    result_chars = []
    symbol_positions = []

    prev_was_symbol = False
    non_symbol_count = 0  # 已经出现的非符号字符数量

    for ch in temp_text:
        if is_symbol(ch):
            if not prev_was_symbol:
                result_chars.append(ch)
                # 记录符号前出现的非符号字符编号
                # 如果符号在开头，-1 表示前面没有非符号字符
                symbol_positions.append(non_symbol_count - 1)
                prev_was_symbol = True
            # 连续符号，跳过
        else:
            result_chars.append(ch)
            non_symbol_count += 1
            prev_was_symbol = False

    final_chars = [ch for ch in result_chars if not is_symbol(ch)]
    f_text = "".join(final_chars)

    return f_text, symbol_positions
