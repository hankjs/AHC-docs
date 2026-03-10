#!/usr/bin/env python3
"""
古籍数据查询工具 - 提供类数据库查询接口，无需直接读取JSON文件。

用法:
    python query.py <command> [options]

命令:
    datasets                    列出所有可用数据集
    schema <dataset>            查看数据集结构
    search <dataset> <keyword>  全文搜索关键词
    get <dataset> <id>          按ID获取记录
    filter <dataset> <field> <value>  按字段过滤
    list <dataset> [collection] 列出记录（支持分页）
    related <dataset> <id>      查找关联记录
    stats <dataset>             数据集统计信息
"""

import json
import sys
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_dataset(name):
    """加载数据集"""
    # 支持带或不带.json后缀
    if not name.endswith(".json"):
        name += ".json"
    filepath = DATA_DIR / name
    if not filepath.exists():
        # 尝试模糊匹配
        candidates = list(DATA_DIR.glob("*.json"))
        for c in candidates:
            if name.replace(".json", "") in c.stem:
                filepath = c
                break
        else:
            print(f"错误: 找不到数据集 '{name}'")
            print(f"可用数据集: {', '.join(c.stem for c in candidates)}")
            sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_datasets():
    """列出所有可用数据集"""
    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        print("没有找到数据集")
        return
    print(f"数据目录: {DATA_DIR}")
    print(f"共 {len(files)} 个数据集:\n")
    for f in files:
        data = load_dataset(f.stem)
        name = data.get("名称", f.stem)
        collections = [k for k in data.keys() if k != "名称"]
        counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
        print(f"  {name} ({f.name})")
        for k, v in counts.items():
            print(f"    - {k}: {v} 条记录")
    print()


def cmd_schema(dataset_name):
    """查看数据集结构"""
    data = load_dataset(dataset_name)
    print(f"数据集: {data.get('名称', dataset_name)}\n")
    for key, value in data.items():
        if key == "名称":
            continue
        if isinstance(value, list) and len(value) > 0:
            print(f"集合: {key} ({len(value)} 条记录)")
            sample = value[0]
            print(f"  字段:")
            for field, val in sample.items():
                val_preview = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
                print(f"    - {field}: {type(val).__name__} (例: \"{val_preview}\")")
            print()


def cmd_get(dataset_name, record_id):
    """按ID获取记录"""
    data = load_dataset(dataset_name)
    for key, value in data.items():
        if not isinstance(value, list):
            continue
        for item in value:
            if item.get("id") == record_id:
                print(f"集合: {key}")
                print(json.dumps(item, ensure_ascii=False, indent=2))
                return
    print(f"未找到 ID={record_id} 的记录")


def cmd_search(dataset_name, keyword, limit=20):
    """全文搜索"""
    data = load_dataset(dataset_name)
    results = []
    for key, value in data.items():
        if not isinstance(value, list):
            continue
        for item in value:
            for field, val in item.items():
                if isinstance(val, str) and keyword in val:
                    results.append({"集合": key, "记录": item})
                    break
    print(f"搜索 \"{keyword}\" 在 {data.get('名称', dataset_name)} 中找到 {len(results)} 条结果")
    if len(results) > limit:
        print(f"(仅显示前 {limit} 条，使用 --limit N 显示更多)\n")
    for r in results[:limit]:
        print(f"[{r['集合']}] {json.dumps(r['记录'], ensure_ascii=False)}")
    print()


def cmd_filter(dataset_name, field, value, collection=None, limit=50):
    """按字段值过滤"""
    data = load_dataset(dataset_name)
    results = []
    for key, items in data.items():
        if not isinstance(items, list):
            continue
        if collection and key != collection:
            continue
        for item in items:
            item_val = item.get(field, "")
            if isinstance(item_val, str) and value in item_val:
                results.append({"集合": key, "记录": item})
    print(f"过滤 {field}=\"{value}\" 找到 {len(results)} 条结果")
    if len(results) > limit:
        print(f"(仅显示前 {limit} 条)\n")
    for r in results[:limit]:
        print(f"[{r['集合']}] {json.dumps(r['记录'], ensure_ascii=False)}")
    print()


def cmd_list(dataset_name, collection=None, offset=0, limit=10):
    """列出记录（分页）"""
    data = load_dataset(dataset_name)
    for key, value in data.items():
        if not isinstance(value, list):
            continue
        if collection and key != collection:
            continue
        total = len(value)
        page = value[offset:offset + limit]
        print(f"集合: {key} (共 {total} 条，显示第 {offset + 1}-{min(offset + limit, total)} 条)\n")
        for item in page:
            print(json.dumps(item, ensure_ascii=False))
        print()


def cmd_related(dataset_name, record_id):
    """查找关联记录（山海经专用：词条↔原文关联）"""
    data = load_dataset(dataset_name)

    # 查找该ID的记录
    found_in = None
    found_record = None
    for key, value in data.items():
        if not isinstance(value, list):
            continue
        for item in value:
            if item.get("id") == record_id:
                found_in = key
                found_record = item
                break

    if not found_record:
        print(f"未找到 ID={record_id}")
        return

    print(f"记录 [{found_in}]: {json.dumps(found_record, ensure_ascii=False, indent=2)}\n")

    # 查找关联
    if found_in == "原文":
        # 找引用此原文的词条
        print("--- 关联词条 ---")
        entries = data.get("词条", [])
        related = [e for e in entries if e.get("所属句子") == record_id or e.get("所属段落") == record_id]
        for e in related:
            print(json.dumps(e, ensure_ascii=False))

    elif found_in == "词条":
        # 找关联的原文
        sentence_id = found_record.get("所属句子", "")
        paragraph_id = found_record.get("所属段落", "")
        sources = data.get("原文", [])

        if sentence_id:
            print("--- 关联原文(句子) ---")
            for s in sources:
                if s.get("id") == sentence_id:
                    print(json.dumps(s, ensure_ascii=False, indent=2))
                    break

        # 找同段落的其他原文
        if paragraph_id:
            print(f"\n--- 同段落原文 (段落id={paragraph_id}) ---")
            for s in sources:
                if s.get("段落id") == paragraph_id:
                    print(json.dumps(s, ensure_ascii=False))

        # 找归属下的子词条
        parent_id = found_record.get("归属", "")
        if parent_id:
            print(f"\n--- 父级词条 (归属={parent_id}) ---")
            entries = data.get("词条", [])
            for e in entries:
                if e.get("id") == parent_id:
                    print(json.dumps(e, ensure_ascii=False, indent=2))
                    break

        # 找子词条
        entries = data.get("词条", [])
        children = [e for e in entries if e.get("归属") == record_id]
        if children:
            print(f"\n--- 子级词条 ({len(children)} 条) ---")
            for e in children:
                print(json.dumps(e, ensure_ascii=False))

    print()


def cmd_stats(dataset_name):
    """数据集统计"""
    data = load_dataset(dataset_name)
    print(f"数据集: {data.get('名称', dataset_name)}\n")
    for key, value in data.items():
        if not isinstance(value, list):
            continue
        print(f"集合: {key}")
        print(f"  总记录数: {len(value)}")
        if not value:
            continue
        # 统计各字段的非空率
        fields = value[0].keys()
        for field in fields:
            non_empty = sum(1 for item in value if item.get(field))
            print(f"  {field}: {non_empty}/{len(value)} 非空 ({non_empty * 100 // len(value)}%)")

        # 对有"类别"字段的集合做分类统计
        if "类别" in value[0]:
            categories = {}
            for item in value:
                cat = item.get("类别", "(空)")
                categories[cat] = categories.get(cat, 0) + 1
            print(f"  类别分布:")
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                print(f"    {cat}: {count}")

        # 对有"所属经文"字段的集合做分类统计
        if "所属经文" in value[0]:
            sections = {}
            for item in value:
                sec = item.get("所属经文", "(空)")
                sections[sec] = sections.get(sec, 0) + 1
            print(f"  经文分布:")
            for sec, count in sorted(sections.items(), key=lambda x: -x[1]):
                print(f"    {sec}: {count}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "datasets":
        cmd_datasets()
    elif cmd == "schema":
        if len(sys.argv) < 3:
            print("用法: query.py schema <dataset>")
            sys.exit(1)
        cmd_schema(sys.argv[2])
    elif cmd == "get":
        if len(sys.argv) < 4:
            print("用法: query.py get <dataset> <id>")
            sys.exit(1)
        cmd_get(sys.argv[2], sys.argv[3])
    elif cmd == "search":
        if len(sys.argv) < 4:
            print("用法: query.py search <dataset> <keyword> [--limit N]")
            sys.exit(1)
        limit = 20
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        cmd_search(sys.argv[2], sys.argv[3], limit)
    elif cmd == "filter":
        if len(sys.argv) < 5:
            print("用法: query.py filter <dataset> <field> <value> [--collection C] [--limit N]")
            sys.exit(1)
        collection = None
        limit = 50
        if "--collection" in sys.argv:
            idx = sys.argv.index("--collection")
            collection = sys.argv[idx + 1]
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        cmd_filter(sys.argv[2], sys.argv[3], sys.argv[4], collection, limit)
    elif cmd == "list":
        if len(sys.argv) < 3:
            print("用法: query.py list <dataset> [collection] [--offset N] [--limit N]")
            sys.exit(1)
        collection = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
        offset = 0
        limit = 10
        if "--offset" in sys.argv:
            idx = sys.argv.index("--offset")
            offset = int(sys.argv[idx + 1])
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        cmd_list(sys.argv[2], collection, offset, limit)
    elif cmd == "related":
        if len(sys.argv) < 4:
            print("用法: query.py related <dataset> <id>")
            sys.exit(1)
        cmd_related(sys.argv[2], sys.argv[3])
    elif cmd == "stats":
        if len(sys.argv) < 3:
            print("用法: query.py stats <dataset>")
            sys.exit(1)
        cmd_stats(sys.argv[2])
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
