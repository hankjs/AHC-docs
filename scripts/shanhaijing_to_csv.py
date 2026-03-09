#!/usr/bin/env python3
"""将 山海经/*-解析版.json 转换为 原文.csv 和 词条.csv"""

import json
import csv
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "山海经"

# 只处理 01 文件，确认后再扩展
FILES = sorted(BASE_DIR.glob("*-解析版.json"))
# FILES = [BASE_DIR / "01_南山经-解析版.json"]


def parse_file(filepath):
    """解析单个 JSON 文件，返回原文行和词条行"""
    fname = filepath.stem  # e.g. "01_南山经-解析版"
    file_id = fname.split("_")[0]  # e.g. "01"
    jing_name = fname.split("_")[1].replace("-解析版", "")  # e.g. "南山经"

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_rows = []
    entry_rows = []

    for item in data:
        if "原文" in item:
            # 原文段落
            source_id = item["id"]  # e.g. "source-01"
            paragraph_id = f"{file_id}-{source_id}"
            for idx, sentence in enumerate(item["原文"]):
                source_rows.append({
                    "id": f"{paragraph_id}-{idx + 1}",
                    "段落id": paragraph_id,
                    "所属经文": jing_name,
                    "句子": sentence,
                })
        elif "名字" in item:
            # 词条
            entry_id = f"{file_id}-{item['id']}"
            归属 = f"{file_id}-{item['归属']}" if item.get("归属") else ""

            # 解析描述 → 所属段落 + 所属句子
            desc = item.get("描述", "")
            if isinstance(desc, list):
                refs = desc
            else:
                refs = [desc] if desc else []

            paragraph_ids = []
            sentence_ids = []
            for ref in refs:
                # ref like "source-08-2"
                m = re.match(r"(source-\d+)-(\d+)", ref)
                if m:
                    src_part = m.group(1)  # "source-08"
                    sent_idx = int(m.group(2))  # 0-based
                    paragraph_ids.append(f"{file_id}-{src_part}")
                    sentence_ids.append(f"{file_id}-{src_part}-{sent_idx + 1}")

            entry_rows.append({
                "id": entry_id,
                "名字": item["名字"],
                "类别": item["类别"],
                "归属": 归属,
                "所属段落": ";".join(dict.fromkeys(paragraph_ids)),
                "所属句子": ";".join(sentence_ids),
            })

    return source_rows, entry_rows


def main():
    all_sources = []
    all_entries = []

    for fp in FILES:
        sources, entries = parse_file(fp)
        all_sources.extend(sources)
        all_entries.extend(entries)
        print(f"  {fp.name}: {len(sources)} 句, {len(entries)} 词条")

    # 写原文CSV
    src_csv = BASE_DIR / "原文.csv"
    with open(src_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "段落id", "所属经文", "句子"])
        w.writeheader()
        w.writerows(all_sources)
    print(f"\n原文.csv: {len(all_sources)} 行 → {src_csv}")

    # 写词条CSV
    ent_csv = BASE_DIR / "词条.csv"
    with open(ent_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "名字", "类别", "归属", "所属段落", "所属句子"])
        w.writeheader()
        w.writerows(all_entries)
    print(f"词条.csv: {len(all_entries)} 行 → {ent_csv}")


if __name__ == "__main__":
    main()
