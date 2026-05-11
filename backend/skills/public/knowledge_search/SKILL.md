---
name: knowledge_search
display_name: 知识库搜索
description: 在企业内部知识库中搜索相关信息，支持关键词匹配和结果排序。
version: 1.0.0
author: admin
email: admin@example.com
url: https://example.com

type: python
entrypoint: knowledge_search.py

input_schema:
  type: object
  properties:
    query:
      type: string
      title: 搜索关键词
      description: 要搜索的关键词或问题
      default: ""
    max_results:
      type: integer
      title: 最大结果数
      description: 返回的最大结果数量
      default: 10
      minimum: 1
      maximum: 50

output_schema:
  type: object
  properties:
    query:
      type: string
      description: 用户输入的搜索关键词
    total_results:
      type: integer
      description: 匹配到的结果总数
    results:
      type: array
      items:
        type: object
        properties:
          title:
            type: string
            description: 文档标题
          filename:
            type: string
            description: 文件名
          content:
            type: string
            description: 文档内容摘要
          matches:
            type: array
            items:
              type: string
            description: 关键词匹配的上下文片段
          score:
            type: integer
            description: 匹配分数（越高越相关）
          source:
            type: string
            description: 来源说明
    message:
      type: string
      description: 执行结果说明

requirements: []

tags:
  - 知识库
  - 搜索
  - RAG
  - 文档检索
---

## 使用说明

### 功能描述
本技能提供企业内部知识库的全文搜索功能，支持：
- 关键词模糊匹配
- 多文件类型支持（.txt, .md, .json）
- 结果按相关性排序
- 返回匹配上下文

### 输入参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| query | string | "" | 搜索关键词 |
| max_results | integer | 10 | 最大返回结果数 |

### 输出示例

```json
{
  "query": "至境E7 续航",
  "total_results": 2,
  "results": [
    {
      "title": "至境E7 产品知识手册",
      "filename": "产品知识.md",
      "content": "至境E7是一款中型豪华插电混动SUV...",
      "matches": ["综合续航超过1000公里，纯电续航200公里"],
      "score": 20,
      "source": "知识库/产品知识.md"
    }
  ],
  "message": "找到 2 条匹配结果"
}
```

### 知识库文件格式

支持的文件格式：
- `.txt` - 纯文本文件
- `.md` - Markdown文件（自动提取标题）
- `.json` - JSON文件（自动提取title/name字段）

### 扩展知识库

将文档放入 `knowledge_base` 目录即可自动被索引和搜索。
