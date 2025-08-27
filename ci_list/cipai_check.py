import json
import os
from collections import Counter

for idx in range(817):
    file_path = f'cipai_{idx}.json'
    if not os.path.isfile(file_path):
        continue

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f'[错误] {file_path} JSON 解析失败：{e}')
            continue

    for item_idx, item in enumerate(data):
        rhyme_pos = item.get('rhyme_pos')      # list
        yun_class = item.get('yun_classify')   # dict，value 可能是 list 或单值

        if rhyme_pos is None or yun_class is None:
            print(f'[错误] {file_path} 第 {item_idx} 项 rhyme_pos 或 yun_classify 缺失')
            continue

        # 展平 yun_class 的所有 value 并取绝对值
        yun_values = []
        for v in yun_class.values():
            if isinstance(v, list):
                yun_values.extend(abs(x) for x in v)
            else:
                yun_values.append(abs(v))

        # rhyme_pos 也统一取绝对值（防止本身含负数）
        rhyme_pos_abs = [abs(x) for x in rhyme_pos]

        # 忽略顺序与重复，用 Counter 比较
        if Counter(rhyme_pos_abs) != Counter(yun_values):
            print(f'[错误] {file_path} 第 {item_idx} 项 rhyme_pos 与 yun_classify 值不匹配\n'
                  f'  rhyme_pos 绝对值: {rhyme_pos_abs}\n'
                  f'  yun_classify 展平绝对值: {yun_values}')