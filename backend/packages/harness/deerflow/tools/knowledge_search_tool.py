"""Knowledge base search tool for roleplay scenarios.

Dynamically loads knowledge from markdown and text files in the knowledge_base directory.
"""

from __future__ import annotations

import os
from typing import Any, List, Dict

from langchain.tools import tool

from deerflow.tools.types import Runtime


# 知识库目录路径
# 从 deerflow/tools/knowledge_search_tool.py 向上4级到 backend 目录
KNOWLEDGE_BASE_DIR = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "..", "..", "skills", "public", "knowledge_search", "knowledge_base"
)

# 缓存加载的知识库内容
_knowledge_cache = None


def _load_knowledge_base() -> List[Dict[str, Any]]:
    """Load knowledge base from files in the knowledge_base directory."""
    global _knowledge_cache
    if _knowledge_cache is not None:
        return _knowledge_cache
    
    knowledge_base = []
    
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        # 如果目录不存在，返回空列表，并创建目录
        os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
        _knowledge_cache = knowledge_base
        return knowledge_base
    
    # 遍历目录中的所有文件
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        
        if os.path.isfile(filepath):
            file_ext = filename.lower().split('.')[-1]
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 根据文件类型解析内容
                if file_ext == 'md':
                    doc = _parse_markdown(filename, content)
                elif file_ext == 'txt':
                    doc = _parse_text(filename, content)
                else:
                    doc = {
                        "id": filename,
                        "title": filename,
                        "category": "other",
                        "content": content,
                        "raw_content": content
                    }
                
                knowledge_base.append(doc)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    _knowledge_cache = knowledge_base
    return knowledge_base


def _parse_markdown(filename: str, content: str) -> Dict[str, Any]:
    """Parse markdown file content into structured knowledge."""
    lines = content.split('\n')
    title = filename.replace('.md', '')
    category = 'general'
    sections = {}
    current_section = None
    current_section_content = []
    
    for line in lines:
        # 提取标题
        if line.startswith('# '):
            title = line[2:].strip()
        elif line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_section_content).strip()
            current_section = line[3:].strip()
            current_section_content = []
        elif current_section:
            current_section_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_section_content).strip()
    
    return {
        "id": filename,
        "title": title,
        "category": category,
        "sections": sections,
        "content": content,
        "raw_content": content
    }


def _parse_text(filename: str, content: str) -> Dict[str, Any]:
    """Parse text file content into structured knowledge."""
    title = filename.replace('.txt', '')
    lines = content.split('\n')
    
    return {
        "id": filename,
        "title": title,
        "category": 'sales',
        "content": content,
        "raw_content": content,
        "lines": [line.strip() for line in lines if line.strip()]
    }


def _search_knowledge(query: str) -> List[Dict[str, Any]]:
    """Search knowledge base for relevant content."""
    knowledge_base = _load_knowledge_base()
    results = []
    
    query_lower = query.lower()
    
    for doc in knowledge_base:
        # 检查标题是否匹配
        if query_lower in doc['title'].lower():
            doc['match_score'] = 1.0
            results.append(doc)
            continue
        
        # 检查内容是否匹配
        content_lower = doc['content'].lower()
        if query_lower in content_lower:
            # 计算匹配分数
            score = content_lower.count(query_lower) * 0.1
            if query_lower in doc['title'].lower():
                score += 0.5
            doc['match_score'] = min(score, 1.0)
            results.append(doc)
    
    # 按匹配分数排序
    results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    return results


@tool("knowledge_search", return_direct=False)
def knowledge_search_tool(query: str) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: The search query string. Can be a product name, scenario name, or question.
    
    Returns:
        A formatted string containing the search results with relevant knowledge.
    """
    results = _search_knowledge(query)
    
    if not results:
        return f"未找到与 '{query}' 相关的知识库内容。"
    
    response_parts = [f"找到 {len(results)} 条与 '{query}' 相关的知识："]
    
    for i, result in enumerate(results, 1):
        response_parts.append(f"\n--- [{i}] {result['title']} ---")
        
        if 'sections' in result:
            for section_name, section_content in result['sections'].items():
                response_parts.append(f"\n**{section_name}**")
                response_parts.append(section_content[:500] + '...' if len(section_content) > 500 else section_content)
        elif 'lines' in result:
            for line in result['lines'][:10]:
                response_parts.append(f"- {line}")
        else:
            content_preview = result['content'][:500] + '...' if len(result['content']) > 500 else result['content']
            response_parts.append(content_preview)
    
    return '\n'.join(response_parts)


@tool("list_knowledge_topics", return_direct=False)
def list_knowledge_topics() -> str:
    """
    List all available topics in the knowledge base.
    
    Returns:
        A formatted string listing all available knowledge topics.
    """
    knowledge_base = _load_knowledge_base()
    
    if not knowledge_base:
        return "知识库为空，请在 knowledge_base 目录添加 .md 或 .txt 文件。"
    
    response_parts = ["知识库中包含以下主题："]
    
    for doc in knowledge_base:
        category = doc.get('category', '未分类')
        response_parts.append(f"- **{doc['title']}** (分类: {category})")
    
    return '\n'.join(response_parts)


@tool("clear_knowledge_cache", return_direct=False)
def clear_knowledge_cache() -> str:
    """
    Clear the knowledge base cache to reload files.
    
    Returns:
        Confirmation message.
    """
    global _knowledge_cache
    _knowledge_cache = None
    return "知识库缓存已清除，下次搜索将重新加载文件。"
