"""前往搜韵网提取词牌内容的爬虫程序。"""


import re
import time
import requests
import os
import random

folder_path = r"/"


def single_to_text(single_html):
    cleaned_text = re.sub(r'<.*?>', '', single_html)
    cleaned_text = cleaned_text.replace('&nbsp;', '　')
    lines = [line.strip() for line in cleaned_text.splitlines() if line.strip()]
    final_text = "\n".join(lines)
    return final_text


def html_to_single_text(web_html, cipai):
    pattern = rf'<a[^>]+href=\'/QueryCiTune.aspx\?id={cipai}#formatIndex_{cipai}_\d+[^>]*>(.*?)</div>'
    matches = re.findall(pattern, web_html, re.DOTALL)
    match_cipai = re.match(r'^([^<]+)', matches[0]).group(1)
    for match in matches:
        text = single_to_text(match.strip())
        file_path = os.path.join(folder_path, rf"ci_list\cipai_{cipai}.txt")
        with open(file_path, "a+", encoding="utf-8") as file:
            file.write(text + '\n\n')
        print(text, end='\n\n')
    file_path = os.path.join(folder_path, r"ci_list\ci_index.txt")
    with open(file_path, "a+", encoding="utf-8") as file:
        file.write(str(cipai) + '\t' + match_cipai + '\n')
    print(f"词牌 {str(match_cipai)} 的内容已成功写入")


def web_to_html(cipai):
    url = f"https://sou-yun.cn/QueryCiTune.aspx?id={cipai}"
    response = requests.get(url)
    time.sleep(random.randint(3, 9))
    if response.status_code == 200:
        html_content = response.text
        start_index = html_content.find("钦谱")
        end_index = html_content.find("龙谱")  # 不要龙谱
        if end_index != -1:
            extracted_text = html_content[start_index:end_index + len("龙谱")]
        else:
            extracted_text = html_content[start_index:]
        return extracted_text
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return None
