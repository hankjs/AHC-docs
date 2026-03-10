import csv
import json
import os

DATA_DIR = "data"


def read_csv(filepath, delimiter="\t"):
    """读取CSV文件，自动检测分隔符"""
    with open(filepath, "r", encoding="utf-8") as f:
        # 先读一行判断分隔符
        first_line = f.readline()
        if "\t" in first_line:
            delimiter = "\t"
        else:
            delimiter = ","
        f.seek(0)
        reader = csv.DictReader(f, delimiter=delimiter)
        return [row for row in reader]


def convert_shanhaijing():
    """转换山海经：原文 + 词条，词条通过id关联原文"""
    sources = read_csv("山海经/原文.csv")
    entries = read_csv("山海经/词条.csv")

    # 构建原文字典，按id索引
    source_map = {}
    for s in sources:
        source_map[s["id"]] = s

    # 为每个词条附加关联的原文句子
    for entry in entries:
        sentence_id = entry.get("所属句子", "")
        if sentence_id and sentence_id in source_map:
            entry["原文句子"] = source_map[sentence_id]["句子"]

    result = {
        "名称": "山海经",
        "原文": sources,
        "词条": entries,
    }

    with open(os.path.join(DATA_DIR, "山海经.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"山海经: {len(sources)} 条原文, {len(entries)} 条词条")


def convert_baicaojing():
    """转换百草经"""
    rows = read_csv("百草经.csv")

    result = {
        "名称": "百草经",
        "条目": rows,
    }

    with open(os.path.join(DATA_DIR, "百草经.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"百草经: {len(rows)} 条记录")


if __name__ == "__main__":
    convert_shanhaijing()
    convert_baicaojing()
    print("转换完成，文件已保存到 data/ 目录")
