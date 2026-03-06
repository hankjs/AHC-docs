#!/usr/bin/env python3
"""爬取《山海经》全文，按章节保存为 Markdown 文件。"""

import os
import re
import time
import urllib.request

BASE_URL = "https://www.quanxue.cn/ct_baijia/shanhai/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "山海经")

CHAPTERS = [
    ("shanhai01.html", "00_导读"),
    ("shanhai02.html", "01_南山经"),
    ("shanhai03.html", "02_西山经"),
    ("shanhai04.html", "03_北山经"),
    ("shanhai05.html", "04_东山经"),
    ("shanhai06.html", "05_中山经"),
    ("shanhai07.html", "06_海外南经"),
    ("shanhai08.html", "07_海外西经"),
    ("shanhai09.html", "08_海外北经"),
    ("shanhai10.html", "09_海外东经"),
    ("shanhai11.html", "10_海内南经"),
    ("shanhai12.html", "11_海内西经"),
    ("shanhai13.html", "12_海内北经"),
    ("shanhai14.html", "13_海内东经"),
    ("shanhai15.html", "14_大荒东经"),
    ("shanhai16.html", "15_大荒南经"),
    ("shanhai17.html", "16_大荒西经"),
    ("shanhai18.html", "17_大荒北经"),
    ("shanhai19.html", "18_海内经"),
]


def fetch_page(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(html):
    """去除 HTML 标签，保留文本。"""
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    return text


def parse_chapter(html):
    """用正则解析章节页面，返回 (title, zhushi_parts, sections)。"""
    # 提取标题
    m = re.search(r'<h1>(.*?)</h1>', html, re.DOTALL)
    title = strip_tags(m.group(1)) if m else ""

    # 提取题解（class="zhushi" 的 p 标签）
    zhushi_parts = []
    for m in re.finditer(r'<p\s+class="zhushi">(.*?)</p>', html, re.DOTALL):
        text = strip_tags(m.group(1))
        if text:
            zhushi_parts.append(text)

    # 提取段落编号：从 b_center div 中找【０１】这样的标记
    # 提取原文：div.jingwen
    # 提取注释：div.comment (id=commentN)
    # 提取译文：div.yiwen (id=yiwenN)

    # 找所有段落编号
    section_titles = re.findall(r'<span\s+class="button width6em">(\s*【[^】]+】\s*)</span>', html)
    section_titles = [t.strip() for t in section_titles]

    # 找所有原文
    jingwen_list = re.findall(r'<div\s+class="jingwen">(.*?)</div>', html, re.DOTALL)
    jingwen_list = [strip_tags(t) for t in jingwen_list]

    # 找所有注释
    comment_list = re.findall(r'<div\s+id="comment\d+"\s+class="comment">(.*?)</div>', html, re.DOTALL)
    comment_list = [strip_tags(t).lstrip('【注释】').strip() for t in comment_list]

    # 找所有译文
    yiwen_list = re.findall(r'<div\s+id="yiwen\d+"\s+class="yiwen">(.*?)</div>', html, re.DOTALL)
    yiwen_list = [strip_tags(t).lstrip('【译文】').strip() for t in yiwen_list]

    # 组装 sections
    n = max(len(jingwen_list), len(comment_list), len(yiwen_list))
    sections = []
    for i in range(n):
        sections.append({
            "title": section_titles[i] if i < len(section_titles) else "",
            "jingwen": jingwen_list[i] if i < len(jingwen_list) else "",
            "comment": comment_list[i] if i < len(comment_list) else "",
            "yiwen": yiwen_list[i] if i < len(yiwen_list) else "",
        })

    return title, zhushi_parts, sections


def format_markdown(title, zhushi_parts, sections):
    lines = []
    if title:
        lines.append(f"# {title}\n")

    if zhushi_parts:
        lines.append("## 题解\n")
        for part in zhushi_parts:
            lines.append(part)
            lines.append("")

    for section in sections:
        lines.append("---\n")
        if section["title"]:
            lines.append(f"### {section['title']}\n")

        if section["jingwen"]:
            lines.append("**【原文】**\n")
            lines.append(section["jingwen"])
            lines.append("")

        if section["yiwen"]:
            lines.append("**【译文】**\n")
            lines.append(section["yiwen"])
            lines.append("")

        if section["comment"]:
            lines.append("**【注释】**\n")
            lines.append(section["comment"])
            lines.append("")

    return "\n".join(lines)


def process_chapter(filename, output_name):
    url = BASE_URL + filename
    print(f"正在爬取: {output_name} ({url})")
    html = fetch_page(url)

    title, zhushi_parts, sections = parse_chapter(html)
    content = format_markdown(title, zhushi_parts, sections)

    output_path = os.path.join(OUTPUT_DIR, f"{output_name}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  -> 已保存: {output_path} ({len(sections)} 段)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename, output_name in CHAPTERS:
        process_chapter(filename, output_name)
        time.sleep(0.5)
    print(f"\n完成！共 {len(CHAPTERS)} 个章节已保存到 '{OUTPUT_DIR}/' 目录。")


if __name__ == "__main__":
    main()
