# 山海经数据爬取

从 [全学网](https://www.quanxue.cn/ct_baijia/shanhaiindex.html) 爬取《山海经》全文（含原文、译文、注释），保存为 Markdown 文件。

## 目录结构

```
.
├── README.md
├── scripts/
│   └── scrape.py        # 爬取脚本
└── 山海经/
    ├── 00_导读.md
    ├── 01_南山经.md
    ├── 02_西山经.md
    ├── 03_北山经.md
    ├── 04_东山经.md
    ├── 05_中山经.md
    ├── 06_海外南经.md
    ├── 07_海外西经.md
    ├── 08_海外北经.md
    ├── 09_海外东经.md
    ├── 10_海内南经.md
    ├── 11_海内西经.md
    ├── 12_海内北经.md
    ├── 13_海内东经.md
    ├── 14_大荒东经.md
    ├── 15_大荒南经.md
    ├── 16_大荒西经.md
    ├── 17_大荒北经.md
    └── 18_海内经.md
```

## 使用方法

```bash
python3 scripts/scrape.py
```

脚本会自动创建 `山海经/` 目录并将 19 个章节保存为 Markdown 文件。

## 文件格式

每个章节文件按段落组织，每段包含：

- **【原文】** — 古文原文
- **【译文】** — 白话文翻译
- **【注释】** — 生僻字注音及词义解释

数据来源：https://www.quanxue.cn/ct_baijia/shanhaiindex.html
