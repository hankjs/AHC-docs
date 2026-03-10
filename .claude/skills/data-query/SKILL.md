---
name: data-query
description: >
  古籍数据查询工具。当需要查询山海经、百草经（神农本草经）等古籍数据时使用此技能。
  通过命令行脚本查询数据，不要直接读取 JSON 文件。
  当用户提到山海经的山、水、兽、草、木等词条，或百草经/本草经的药物信息，
  或需要搜索、过滤、统计古籍数据时，都应使用此技能。
---

# 古籍数据查询工具

查询 `data/` 目录下的古籍 JSON 数据时，使用 `scripts/query.py` 脚本，不要直接读取 JSON 文件。

## 目录结构

```
.claude/skills/data-query/
├── SKILL.md
├── data/              ← JSON 数据文件
│   ├── 山海经.json
│   ├── 百草经.json
│   └── 数据结构说明.md
└── scripts/
    └── query.py       ← 查询脚本（自动定位同级 data/ 目录）
```

## 可用命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `datasets` | 列出所有数据集 | `python query.py datasets` |
| `schema <数据集>` | 查看数据结构和字段 | `python query.py schema 山海经` |
| `stats <数据集>` | 统计信息（记录数、类别分布等） | `python query.py stats 山海经` |
| `search <数据集> <关键词>` | 全文搜索 | `python query.py search 山海经 龙` |
| `get <数据集> <id>` | 按ID精确获取 | `python query.py get 山海经 01-01-3` |
| `filter <数据集> <字段> <值>` | 按字段过滤 | `python query.py filter 山海经 类别 兽` |
| `list <数据集> [集合]` | 分页浏览 | `python query.py list 百草经 --limit 5` |
| `related <数据集> <id>` | 查找关联记录 | `python query.py related 山海经 01-01-3` |

## 常用选项

- `--limit N` — 限制返回条数（search 默认20，filter 默认50，list 默认10）
- `--offset N` — 跳过前N条（用于分页）
- `--collection 集合名` — 指定在哪个集合中过滤（如 `词条` 或 `原文`）

## 典型查询场景

**了解有哪些数据：**
```bash
python query.py datasets
python query.py schema 山海经
python query.py stats 山海经
```

**搜索特定内容：**
```bash
# 搜索包含"龙"的所有记录
python query.py search 山海经 龙

# 查找所有"兽"类词条
python query.py filter 山海经 类别 兽 --collection 词条

# 查找南山经的所有原文
python query.py filter 山海经 所属经文 南山经 --collection 原文
```

**查看关联关系（山海经专用）：**
```bash
# 查看某个词条及其关联的原文、父级、子级
python query.py related 山海经 01-01-2

# 查看某句原文及引用它的所有词条
python query.py related 山海经 01-source-01-3
```

**查询百草经药物：**
```bash
python query.py search 百草经 明目
python query.py filter 百草经 气味 甘
```

## 数据集说明

- **山海经** — 包含"原文"（句子级）和"词条"（实体级）两个集合，词条通过 `所属句子` 关联原文
- **百草经** — 包含"条目"集合，每条记录一味药物（名称、气味、主治、附方等）
