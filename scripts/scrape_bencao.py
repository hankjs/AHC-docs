#!/usr/bin/env python3
"""爬取《神农本草经》全文，按章节保存为 Markdown 文件。
每味药提取：名称、气味、主治、别名、生长。"""

import os
import re
import time
import urllib.request

BASE_URL = "https://www.quanxue.cn/ct_zhongyi/bencao/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "神农本草经")

CHAPTERS = [
    ("bencao01.html", "01_总论"),
    ("bencao02.html", "02_玉石部(上品)"),
    ("bencao03.html", "03_玉石部(中品)"),
    ("bencao04.html", "04_玉石部(下品)"),
    ("bencao05.html", "05_草部(上品)"),
    ("bencao06.html", "06_草部(中品)"),
    ("bencao07.html", "07_草部(下品)"),
    ("bencao08.html", "08_木部(上品)"),
    ("bencao09.html", "09_木部(中品)"),
    ("bencao10.html", "10_木部(下品)"),
    ("bencao11.html", "11_虫兽部(上品)"),
    ("bencao12.html", "12_虫兽部(中品)"),
    ("bencao13.html", "13_虫兽部(下品)"),
    ("bencao14.html", "14_果菜部"),
    ("bencao15.html", "15_米谷部"),
]


def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                print(f"  重试 ({attempt + 1}/{retries}): {e}")
                time.sleep(2)
            else:
                raise


def strip_tags(html):
    text = re.sub(r'<br\s*/?>', '、', html)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', '', text)
    text = re.sub(r'&amp;', '&', text)
    text = text.strip()
    return text


def parse_page(html):
    """解析页面，返回 (title, drugs)。"""
    # 标题
    m = re.search(r'<h1>(.*?)</h1>', html, re.DOTALL)
    title = strip_tags(m.group(1)).replace('、', '') if m else ""

    # 副标题
    m = re.search(r'<div class="vice">(.*?)</div>', html, re.DOTALL)
    if m:
        title += " " + strip_tags(m.group(1)).replace('、', '')

    # 检查是否有表格（总论页可能没有）
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    if not tables:
        # 总论：提取正文内容
        return title, [], html

    drugs = []
    for table_html in tables:
        rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) >= 6:
                no = strip_tags(cells[0]).replace('、', '')
                if no == "No" or not no:
                    continue
                drug = {
                    "名称": strip_tags(cells[1]).replace('、', '/'),
                    "气味": strip_tags(cells[2]).replace('、', ''),
                    "主治": strip_tags(cells[3]).replace('、', '，'),
                    "别名": strip_tags(cells[4]).replace('、', '/'),
                    "生长": strip_tags(cells[5]).replace('、', ''),
                }
                drugs.append(drug)

    return title, drugs, None


def parse_zonglun(html):
    """解析总论页面的纯文本内容。"""
    # 提取 page_global 内的文本段落
    m = re.search(r"<div id='page_global'>(.*?)<script>", html, re.DOTALL)
    if not m:
        return ""
    content = m.group(1)
    # 去 h1
    content = re.sub(r'<h1>.*?</h1>', '', content, flags=re.DOTALL)
    content = re.sub(r'<hr\s*/?>', '', content)
    # 段落转换
    content = re.sub(r'<p[^>]*>', '\n', content)
    content = re.sub(r'</p>', '\n', content)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'&nbsp;', ' ', content)
    # 清理多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def format_markdown(title, drugs, raw_html=None):
    lines = []
    if title:
        lines.append(f"# {title}\n")

    if not drugs and raw_html:
        # 总论页
        text = parse_zonglun(raw_html)
        lines.append(text)
        return "\n".join(lines)

    for drug in drugs:
        lines.append(f"## {drug['名称']}\n")

        if drug["气味"]:
            lines.append(f"**气味**：{drug['气味']}\n")

        if drug["主治"]:
            lines.append("**主治**\n")
            lines.append(drug["主治"])
            lines.append("")

        if drug["别名"]:
            lines.append(f"**别名**：{drug['别名']}\n")

        if drug["生长"]:
            lines.append(f"**生长**：{drug['生长']}\n")

        lines.append("---\n")

    return "\n".join(lines)


def process_chapter(filename, output_name):
    url = BASE_URL + filename
    print(f"正在爬取: {output_name} ({url})")
    html = fetch_page(url)

    title, drugs, raw_html = parse_page(html)
    content = format_markdown(title, drugs, raw_html)

    output_path = os.path.join(OUTPUT_DIR, f"{output_name}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  -> 已保存: {output_path} ({len(drugs)} 味药)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename, output_name in CHAPTERS:
        process_chapter(filename, output_name)
        time.sleep(0.5)
    print(f"\n完成！共 {len(CHAPTERS)} 个章节已保存到 '{OUTPUT_DIR}/' 目录。")


if __name__ == "__main__":
    main()
