#!/usr/bin/env python3
"""爬取《本草纲目》全文，按页保存为 Markdown 文件。
每个药材提取：释名、气味、主治、附方、考释。"""

import os
import re
import time
import urllib.request

BASE_URL = "https://www.quanxue.cn/ct_zhongyi/gangmu/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "本草纲目")

TOTAL_PAGES = 185

# 分类映射：页码范围 -> 部名
CATEGORIES = [
    (1, 6, "水部"),
    (7, 8, "火部"),
    (9, 16, "土部"),
    (17, 20, "金部"),
    (21, 35, "石部"),
    (36, 91, "草部"),
    (92, 103, "谷部"),
    (104, 116, "菜部"),
    (117, 129, "果部"),
    (130, 149, "木部"),
    (150, 158, "虫部"),
    (159, 164, "鳞部"),
    (165, 167, "介部"),
    (168, 171, "禽部"),
    (172, 183, "兽部"),
    (184, 185, "人部"),
]


def get_category(page_num):
    for start, end, name in CATEGORIES:
        if start <= page_num <= end:
            sub_num = page_num - start + 1
            return name, sub_num
    return "未分类", page_num


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
    """去除 HTML 标签，保留文本。"""
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', '', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = text.strip()
    return text


def parse_page(html):
    """解析页面，返回 (title, drugs)。
    drugs 是 [{name, 释名, 气味, 主治, 附方}, ...]
    """
    # 提取页面标题
    m = re.search(r'<h1>(.*?)</h1>', html, re.DOTALL)
    title = strip_tags(m.group(1)) if m else ""

    # 提取每个药材表格
    drugs = []
    # 每个药材是一个 <table>，用 <caption> 标识药名
    tables = re.findall(
        r'<table[^>]*>(.*?)</table>',
        html, re.DOTALL
    )

    for table_html in tables:
        drug = {"name": "", "释名": "", "气味": "", "主治": "", "附方": "", "考释": ""}

        # 药名
        cap = re.search(r'<caption>(.*?)</caption>', table_html, re.DOTALL)
        if cap:
            drug["name"] = strip_tags(cap.group(1))

        # 提取各行
        rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) >= 2:
                key = strip_tags(cells[0]).strip()
                val = strip_tags(cells[1]).strip()
                if key in drug:
                    drug[key] = val

        if drug["name"]:
            drugs.append(drug)

    return title, drugs


def format_markdown(title, drugs):
    lines = []
    if title:
        lines.append(f"# {title}\n")

    for drug in drugs:
        lines.append(f"## {drug['name']}\n")

        if drug["释名"]:
            lines.append("**释名**\n")
            lines.append(drug["释名"])
            lines.append("")

        if drug["气味"]:
            lines.append("**气味**\n")
            lines.append(drug["气味"])
            lines.append("")

        if drug["主治"]:
            lines.append("**主治**\n")
            lines.append(drug["主治"])
            lines.append("")

        if drug["附方"]:
            lines.append("**附方**\n")
            lines.append(drug["附方"])
            lines.append("")

        if drug["考释"]:
            lines.append("**考释**\n")
            lines.append(drug["考释"])
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)


def process_page(page_num):
    url = f"{BASE_URL}gangmu{page_num:02d}.html"
    if page_num >= 100:
        url = f"{BASE_URL}gangmu{page_num}.html"

    category, sub_num = get_category(page_num)
    output_name = f"{page_num:03d}_{category}({sub_num:02d})"

    print(f"正在爬取: {output_name} ({url})")
    html = fetch_page(url)

    title, drugs = parse_page(html)
    content = format_markdown(title, drugs)

    output_path = os.path.join(OUTPUT_DIR, f"{output_name}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  -> 已保存: {output_path} ({len(drugs)} 味药)")
    return len(drugs)


def main():
    import sys
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total_drugs = 0
    for i in range(start, TOTAL_PAGES + 1):
        total_drugs += process_page(i)
        time.sleep(0.3)
    print(f"\n完成！共 {TOTAL_PAGES - start + 1} 页，{total_drugs} 味药已保存到 '{OUTPUT_DIR}/' 目录。")


if __name__ == "__main__":
    main()
