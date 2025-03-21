"""将数字转换为汉字。"""


def num_to_cn(num):
    chinese_nums = {0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
                    5: '五', 6: '六', 7: '七', 8: '八', 9: '九'}

    chinese_units = ['', '十', '百', '千']
    chinese_big_units = ['', '万', '亿', '兆', '京', '垓', '秭', '穰', '沟', '涧', '正', '载', '极']
    num_str = str(num)[::-1]
    length = len(num_str)
    result = ''
    for i in range(length):
        digit = int(num_str[i])
        if i % 4 == 0:
            result = chinese_big_units[i // 4] + result
        if digit != 0:
            result = chinese_nums[digit] + chinese_units[i % 4] + result
        elif i % 4 != 0 and result and result[0] != '零':  # 非最高位且结果不为空且结果的首位不为零时，加零
            result = chinese_nums[digit] + result
        elif i == 0 and length == 1:  # 处理数字 0
            result = chinese_nums[digit]

    if result[0:2] == '一十':  # 处理 "一十" 的情况
        result = result[1:]

    return result
