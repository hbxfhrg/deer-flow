"""知识库搜索工具 - DeerFlow Tool"""

import json
import os
import re
import fnmatch

from langchain.tools import tool


class KnowledgeSearch:
    """知识库搜索类"""

    def __init__(self, knowledge_base_path=None):
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_base()
        os.makedirs(self.knowledge_base_path, exist_ok=True)

    def _get_default_knowledge_base(self):
        # 指向 skills/public/knowledge_search/knowledge_base/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        return os.path.join(base_dir, 'skills', 'public', 'knowledge_search', 'knowledge_base')

    def _load_document(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def _extract_title(self, content, filename):
        lines = content.split('\n')[:10]
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        if filename.endswith('.json'):
            try:
                data = json.loads(content)
                return data.get('title', data.get('name', ''))
            except:
                pass
        return os.path.splitext(os.path.basename(filename))[0]

    def _search_in_file(self, file_path, keywords, case_sensitive=False):
        content = self._load_document(file_path)
        if not content:
            return None

        filename = os.path.basename(file_path)
        score = 0
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE

        for keyword in keywords:
            count = len(re.findall(re.escape(keyword), content, flags))
            score += count * 10
            pattern = re.compile(rf'(.{{0,50}}){re.escape(keyword)}(.{{0,50}})', flags)
            for match in pattern.finditer(content):
                context = f"{match.group(1)}{keyword}{match.group(2)}"
                matches.append(context.replace('\n', ' ').strip())

        if score == 0:
            return None

        return {
            'title': self._extract_title(content, filename),
            'filename': filename,
            'content': content[:500] + '...' if len(content) > 500 else content,
            'matches': matches[:5],
            'score': score,
            'source': f"knowledge_base/{filename}"
        }

    def search(self, query, max_results=10, case_sensitive=False):
        keywords = [k.strip() for k in query.split() if k.strip()]
        if not keywords:
            return json.dumps({
                "query": query,
                "total_results": 0,
                "results": [],
                "message": "请提供搜索关键词"
            }, ensure_ascii=False)

        results = []
        for root, _, files in os.walk(self.knowledge_base_path):
            for filename in files:
                if not fnmatch.fnmatch(filename, '*.txt') and \
                   not fnmatch.fnmatch(filename, '*.md') and \
                   not fnmatch.fnmatch(filename, '*.json'):
                    continue
                file_path = os.path.join(root, filename)
                result = self._search_in_file(file_path, keywords, case_sensitive)
                if result:
                    results.append(result)

        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:max_results]

        return json.dumps({
            "query": query,
            "total_results": len(results),
            "results": results,
            "message": f"找到 {len(results)} 条匹配结果"
        }, ensure_ascii=False, indent=2)


# 全局单例
_searcher = None

def _get_searcher():
    global _searcher
    if _searcher is None:
        _searcher = KnowledgeSearch()
    return _searcher


@tool("knowledge_search", parse_docstring=True)
def knowledge_search(query: str, max_results: int = 10) -> str:
    """在企业内部知识库中搜索相关信息。

    当用户询问产品知识、公司政策、技术文档等内容时使用此工具。
    返回与查询关键词最相关的文档摘要和来源。

    Args:
        query: 搜索关键词，可以是多个词（用空格分隔）
        max_results: 最大返回结果数量，默认10条
    """
    return _get_searcher().search(query, max_results=max_results)
