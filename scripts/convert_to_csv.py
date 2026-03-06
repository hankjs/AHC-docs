#!/usr/bin/env python3
"""
将山海经目录下所有 MD 文件转换为一个 CSV 文件。
CSV 列：卷名, 序号, 原文, 译文, 注释
字段内换行使用字面量 \n 代替。
"""

import re
import os
import glob


def escape_field(s):
    """将真实换行替换为字面量 \\n，然后按 CSV 规范引用。"""
    s = s.replace('\n', '\\n')
    if ',' in s or '"' in s or '\\n' in s:
        s = '"' + s.replace('"', '""') + '"'
    return s


def parse_md(filepath):
    """解析单个 MD 文件，返回行列表。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取卷名，如 "卷一 南山经"
    title_match = re.search(r'# 《山海经》\s*(.+)', content)
    if not title_match:
        return []  # 跳过没有标准标题的文件（如导读）
    juan_name = title_match.group(1).strip()

    rows = []

    # 提取题解
    tiji_match = re.search(r'## 题解\s+【题解】\s*\n(.*?)(?=\n---)', content, re.DOTALL)
    tiji = tiji_match.group(1).strip() if tiji_match else ''
    if tiji:
        rows.append((juan_name, '题解', '', tiji, ''))

    # 按 ### 【XX】 分割词条
    sections = re.split(r'### 【(\d+)】', content)
    # sections[0] 是第一个词条之前的内容，之后交替：序号, 正文

    for i in range(1, len(sections), 2):
        num = sections[i].strip()  # 保留原始全角/半角序号
        body = sections[i + 1]

        # 提取原文
        yw_match = re.search(
            r'\*\*【原文】\*\*\s*\n\n(.*?)(?=\n\n\*\*【译文】\*\*)',
            body, re.DOTALL
        )
        yuanwen = yw_match.group(1).strip() if yw_match else ''
        # 去掉原文中的 [N] 注释标记
        yuanwen = re.sub(r'\s*\[\d+\]\s*', '', yuanwen)

        # 提取译文
        yw_match = re.search(
            r'\*\*【译文】\*\*\s*\n\n(.*?)(?=\n\n\*\*【注释】\*\*)',
            body, re.DOTALL
        )
        yiwen = yw_match.group(1).strip() if yw_match else ''

        # 提取注释
        zs_match = re.search(
            r'\*\*【注释】\*\*\s*\n\n(.*?)(?=\n\n---|$)',
            body, re.DOTALL
        )
        zhushi = zs_match.group(1).strip() if zs_match else ''
        # 去掉注释中的 [N] 编号前缀
        zhushi = re.sub(r'^\[\d+\]\s*', '', zhushi, flags=re.MULTILINE)

        rows.append((juan_name, num, yuanwen, yiwen, zhushi))

    return rows


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_files = sorted(glob.glob(os.path.join(script_dir, '*.md')))

    output_path = os.path.join(script_dir, '山海经.csv')

    all_rows = []
    for md_file in md_files:
        rows = parse_md(md_file)
        if rows:
            basename = os.path.basename(md_file)
            print(f'  {basename}: {len(rows)} 条')
            all_rows.extend(rows)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('卷名,序号,原文,译文,注释\n')
        for row in all_rows:
            f.write(','.join(escape_field(field) for field in row) + '\n')

    print(f'\n完成！共 {len(all_rows)} 条，输出到: {output_path}')


if __name__ == '__main__':
    main()
