#!/usr/bin/env python3
"""
将神农本草经和本草纲目目录下的 MD 文件转换为 CSV 文件。
CSV 列：id,名称,别名(释名),气味,主治,附方,生长,考释
"""

import re
import os
import sys
import glob
import argparse


def escape_field(s):
    """将真实换行替换为字面量 \\n，然后按 CSV 规范引用。"""
    s = s.replace('\n', '\\n')
    if ',' in s or '"' in s or '\\n' in s:
        s = '"' + s.replace('"', '""') + '"'
    return s


def parse_entries(content):
    """按 ## 药名 + --- 分割条目，返回 [(药名, {字段: 值}), ...]"""
    entries = []
    # 按 ## 分割
    sections = re.split(r'\n## ', content)
    for section in sections[1:]:  # 跳过第一段（标题前内容）
        lines = section.strip()
        if not lines:
            continue
        # 药名是第一行
        name_line = lines.split('\n', 1)[0].strip()
        body = lines.split('\n', 1)[1] if '\n' in lines else ''

        # 提取所有 **字段名** 及其内容
        fields = {}
        # 匹配 **字段名** 后面的内容，直到下一个 **字段名** 或 --- 或文末
        parts = re.split(r'\*\*(\S+?)\*\*', body)
        # parts: [前文, 字段名1, 内容1, 字段名2, 内容2, ...]
        for i in range(1, len(parts), 2):
            field_name = parts[i]
            raw_value = parts[i + 1] if i + 1 < len(parts) else ''
            # 去掉内容中尾部的 --- 分隔符
            raw_value = re.split(r'\n---', raw_value)[0]
            # 去掉字段名后可能紧跟的冒号/：
            raw_value = re.sub(r'^[：:]\s*', '', raw_value.strip())
            fields[field_name] = raw_value.strip()

        entries.append((name_line, fields))
    return entries


BOOKS = [
    {
        'name': '神农本草经',
        'dir': '神农本草经',
        'skip': ['01_总论.md'],
        'field_map': {
            '别名(释名)': '别名',
            '气味': '气味',
            '主治': '主治',
            '附方': None,
            '生长': '生长',
            '考释': None,
        },
    },
    {
        'name': '本草纲目',
        'dir': '本草纲目',
        'skip': [],
        'field_map': {
            '别名(释名)': '释名',
            '气味': '气味',
            '主治': '主治',
            '附方': '附方',
            '生长': None,
            '考释': '考释',
        },
    },
]

CSV_HEADER = 'id,名称,别名(释名),气味,主治,附方,生长,考释'
CSV_FIELDS = ['别名(释名)', '气味', '主治', '附方', '生长', '考释']


def process_book(book_cfg, base_dir, file_filter=None):
    """处理一本书，返回行列表 [(名称, 别名, 气味, 主治, 附方, 生长), ...]"""
    book_dir = os.path.join(base_dir, book_cfg['dir'])
    if file_filter:
        md_files = [f for f in file_filter if os.path.abspath(f).startswith(os.path.abspath(book_dir))]
    else:
        md_files = sorted(glob.glob(os.path.join(book_dir, '*.md')))

    rows = []
    for md_file in md_files:
        basename = os.path.basename(md_file)
        if basename in book_cfg['skip']:
            continue
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        entries = parse_entries(content)
        if entries:
            print(f'  {basename}: {len(entries)} 条')
        for name, fields in entries:
            row = [name]
            for csv_field in CSV_FIELDS:
                src_field = book_cfg['field_map'][csv_field]
                row.append(fields.get(src_field, '') if src_field else '')
            rows.append(tuple(row))
    return rows


def main():
    parser = argparse.ArgumentParser(description='将本草类 MD 文件转换为 CSV')
    parser.add_argument('--file', action='append', dest='files', help='只转换指定文件（可多次指定）')
    args = parser.parse_args()

    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

    global_id = 0
    all_rows = []
    for book_cfg in BOOKS:
        print(f'\n处理《{book_cfg["name"]}》...')
        rows = process_book(book_cfg, base_dir, args.files)
        if not rows:
            print('  无条目')
            continue

        output_path = os.path.join(base_dir, book_cfg['dir'], f'{book_cfg["name"]}.csv')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(CSV_HEADER + '\n')
            for row in rows:
                global_id += 1
                f.write(str(global_id) + ',' + ','.join(escape_field(field) for field in row) + '\n')
        all_rows.extend(rows)
        print(f'  共 {len(rows)} 条，输出到: {output_path}')

    # 合并输出百草经.csv
    merged_path = os.path.join(base_dir, '百草经.csv')
    with open(merged_path, 'w', encoding='utf-8') as f:
        f.write(CSV_HEADER + '\n')
        for i, row in enumerate(all_rows, 1):
            f.write(str(i) + ',' + ','.join(escape_field(field) for field in row) + '\n')
    print(f'\n合并输出: {merged_path}')
    print(f'完成！总计 {len(all_rows)} 条')


if __name__ == '__main__':
    main()
