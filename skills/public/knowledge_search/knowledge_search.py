#!/usr/bin/env python3
"""
知识库搜索工具 - 使用文件存储的企业内部知识库
支持关键词搜索、模糊匹配、结果排序

使用方式：
1. 在 knowledge_base 目录下放置知识库文档（支持 .txt, .md, .json）
2. 通过 query 参数搜索知识库
3. 返回匹配的文档摘要和来源信息
"""

import json
import os
import re
import fnmatch

class KnowledgeSearch:
    """知识库搜索类"""
    
    def __init__(self, knowledge_base_path=None):
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_base()
        self._ensure_knowledge_base_exists()
    
    def _get_default_knowledge_base(self):
        """获取默认知识库路径"""
        return os.path.join(os.path.dirname(__file__), 'knowledge_base')
    
    def _ensure_knowledge_base_exists(self):
        """确保知识库目录存在"""
        os.makedirs(self.knowledge_base_path, exist_ok=True)
    
    def _load_document(self, file_path):
        """加载文档内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"加载文档失败 {file_path}: {e}", file=__import__('sys').stderr)
            return None
    
    def _extract_title(self, content, filename):
        """从内容中提取标题"""
        # 尝试从 Markdown 标题提取
        lines = content.split('\n')[:10]
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        
        # 尝试从 JSON 提取
        if filename.endswith('.json'):
            try:
                data = json.loads(content)
                return data.get('title', data.get('name', ''))
            except:
                pass
        
        # 返回文件名（不含扩展名）
        return os.path.splitext(os.path.basename(filename))[0]
    
    def _search_in_file(self, file_path, keywords, case_sensitive=False):
        """在单个文件中搜索"""
        content = self._load_document(file_path)
        if not content:
            return None
        
        filename = os.path.basename(file_path)
        
        # 计算匹配分数
        score = 0
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for keyword in keywords:
            # 统计关键词出现次数
            count = len(re.findall(re.escape(keyword), content, flags))
            score += count * 10
            
            # 查找上下文
            pattern = re.compile(rf'(.{{0,50}}){re.escape(keyword)}(.{{0,50}})', flags)
            for match in pattern.finditer(content):
                context = f"{match.group(1)}{keyword}{match.group(2)}"
                context = context.replace('\n', ' ').replace('\r', '')
                matches.append(context.strip())
        
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
        """
        搜索知识库
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            case_sensitive: 是否大小写敏感
            
        Returns:
            JSON格式的搜索结果
        """
        results = []
        
        # 解析关键词
        keywords = [k.strip() for k in query.split() if k.strip()]
        if not keywords:
            return json.dumps({
                "query": query,
                "total_results": 0,
                "results": [],
                "message": "请提供搜索关键词"
            }, ensure_ascii=False)
        
        # 遍历知识库目录
        for root, dirs, files in os.walk(self.knowledge_base_path):
            for filename in files:
                # 支持的文件类型
                if not fnmatch.fnmatch(filename, '*.txt') and \
                   not fnmatch.fnmatch(filename, '*.md') and \
                   not fnmatch.fnmatch(filename, '*.json'):
                    continue
                
                file_path = os.path.join(root, filename)
                result = self._search_in_file(file_path, keywords, case_sensitive)
                
                if result:
                    results.append(result)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 限制结果数量
        results = results[:max_results]
        
        return json.dumps({
            "query": query,
            "total_results": len(results),
            "results": results,
            "message": f"找到 {len(results)} 条匹配结果"
        }, ensure_ascii=False, indent=2)


def main():
    """命令行入口"""
    import sys
    
    # 获取查询参数
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        print("请输入搜索关键词：")
        query = sys.stdin.read().strip()
    
    # 创建搜索实例
    searcher = KnowledgeSearch()
    
    # 执行搜索
    result = searcher.search(query)
    print(result)


if __name__ == "__main__":
    main()
