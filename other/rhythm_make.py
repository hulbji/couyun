import re


def remove_spaces_and_brackets(text):
    # 移除空格和中括号及其内的汉字
    cleaned_text = re.sub(r'\s|\[[^\[\]]*]', '', text)
    return cleaned_text


def add_newline_every_num_chars(string, num):
    # 如果字符串长度小于等于120，直接返回原字符串
    if len(string) <= num:
        return string
    return '\n'.join([string[i:i+num] for i in range(0, len(string), num)])


input_text = ''''''
result = remove_spaces_and_brackets(input_text)
result = add_newline_every_num_chars(result, 65)
print(result)
