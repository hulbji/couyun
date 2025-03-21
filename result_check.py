import re
from num_to_cn import num_to_cn

cn_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}


def result_check(post_result, temp_result):
    if post_result == '':
        return temp_result
    post_count, post_yayun_count, post_yayun_type = count_zero_and_zhong(post_result)
    temp_count, temp_yayun_count, temp_yayun_type = count_zero_and_zhong(temp_result)
    if temp_count > post_count:
        return temp_result
    if temp_count == post_count:
        if post_yayun_count > temp_yayun_count:
            return post_result
        if post_yayun_count == temp_yayun_count:
            if temp_yayun_type > post_yayun_type:
                return post_result
            return temp_result
        return temp_result
    return post_result


def count_zero_and_zhong(string):
    matches = re.findall(r'第([一二三四五六七八九十])组韵', string)
    if matches:
        yun_nums = [cn_nums[cn_num] for cn_num in matches]
        yun_types = max(yun_nums)
    else:
        yun_types = 1
    total_count = yayun_count = 0
    lines = string.split('\n')
    for line in lines:
        if '〇' in line:
            total_count += line.count('〇') + line.count('中')
        if '不押韵' in line:
            total_count -= 1
        if '押韵' in line:
            yayun_count += 1
    return total_count, yayun_count, yun_types
