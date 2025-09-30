# -*- coding: utf-8 -*-
import json
from opencc import OpenCC   # pip install opencc-python-reimplemented

# 1. 读入原文件
with open('ci_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 2. 初始化转换器
converter = OpenCC('s2t')   # 简体 → 繁体

# 3. 遍历每个词牌字典，新增 names_trad
for item in data:
    item['names_trad'] = [converter.convert(name) for name in item['names']]

# 4. 写回文件（覆盖保存）
with open('ci_index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print('done，已新增 names_trad 字段并保存。')