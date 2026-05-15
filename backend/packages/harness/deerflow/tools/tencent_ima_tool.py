"""腾讯 IMA 知识库接入工具 - DeerFlow Tool

API 文档: https://ima.qq.com/openapi/wiki/v1/
"""

import json
import os

import aiohttp
from langchain.tools import tool

# IMA OpenAPI 基础路径
IMA_BASE_PATH = "/openapi/wiki/v1"


def _get_ima_config():
    """从配置中获取 IMA 配置"""
    try:
        from deerflow.config import get_app_config
        tool_config = get_app_config().get_tool_config("tencent_ima")
        if tool_config:
            return {
                "enabled": True,
                "api_url": getattr(tool_config, 'api_url', 'https://ima.qq.com'),
                "client_id": getattr(tool_config, 'client_id', ''),
                "api_key": getattr(tool_config, 'api_key', ''),
                "knowledge_base_id": getattr(tool_config, 'knowledge_base_id', ''),
            }
    except Exception:
        pass
    return {"enabled": False, "api_url": "", "client_id": "", "api_key": "", "knowledge_base_id": ""}


class TencentIMAKnowledgeBase:
    """腾讯 IMA 知识库客户端"""

    def __init__(self, api_url=None, client_id=None, api_key=None, knowledge_base_id=None):
        ima_config = _get_ima_config()

        self.api_url = (api_url or
                        os.environ.get('IMA_OPENAPI_BASE_URL') or
                        ima_config.get('api_url', 'https://ima.qq.com')).rstrip('/')
        self.client_id = (client_id or
                          os.environ.get('IMA_OPENAPI_CLIENTID') or
                          ima_config.get('client_id', ''))
        self.api_key = (api_key or
                        os.environ.get('IMA_OPENAPI_APIKEY') or
                        ima_config.get('api_key', ''))
        self.knowledge_base_id = (knowledge_base_id or
                                  os.environ.get('IMA_KNOWLEDGE_BASE_ID') or
                                  ima_config.get('knowledge_base_id', ''))

        if not self.client_id or not self.api_key:
            raise ValueError(
                "IMA_OPENAPI_CLIENTID and IMA_OPENAPI_APIKEY are required. "
                "Set via environment variable or config.yaml"
            )

    def _headers(self) -> dict:
        """构建请求头（使用正确的 IMA header 格式）"""
        return {
            'Content-Type': 'application/json',
            'ima-openapi-clientid': self.client_id,
            'ima-openapi-apikey': self.api_key,
        }

    async def search(self, query: str, max_results: int = 10) -> str:
        """搜索腾讯 IMA 知识库内容"""
        if not self.knowledge_base_id:
            return json.dumps({
                "query": query,
                "total_results": 0,
                "results": [],
                "message": "未配置 knowledge_base_id，请在 config.yaml 中设置或通过环境变量 IMA_KNOWLEDGE_BASE_ID 传入"
            }, ensure_ascii=False)

        payload = {
            "knowledge_base_id": self.knowledge_base_id,
            "query": query,
            "limit": max_results,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}{IMA_BASE_PATH}/search_knowledge",
                    headers=self._headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_results(query, data)
                    else:
                        error_text = await response.text()
                        return json.dumps({
                            "query": query,
                            "total_results": 0,
                            "results": [],
                            "message": f"API 请求失败: {response.status} - {error_text}"
                        }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "query": query,
                "total_results": 0,
                "results": [],
                "message": f"请求异常: {str(e)}"
            }, ensure_ascii=False)

    async def list_knowledge_bases(self, limit: int = 50) -> str:
        """获取可添加的知识库列表，返回名称与ID对照表"""
        payload = {
            "limit": limit,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}{IMA_BASE_PATH}/get_addable_knowledge_base_list",
                    headers=self._headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_knowledge_base_list(data)
                    else:
                        error_text = await response.text()
                        return json.dumps({
                            "message": f"API 请求失败: {response.status} - {error_text}"
                        }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "message": f"请求异常: {str(e)}"
            }, ensure_ascii=False)

    def _format_knowledge_base_list(self, data) -> str:
        """格式化知识库列表为名称-ID对照表"""
        result_lines = []
        id_map = {}

        if data.get('code') == 0 and data.get('data'):
            items = data['data'].get('items', data['data'].get('knowledge_list', []))
            for i, item in enumerate(items, 1):
                kb_id = item.get('knowledge_base_id', item.get('media_id', ''))
                name = item.get('knowledge_base_name', item.get('title', '未知'))
                desc = item.get('description', '')
                id_map[str(i)] = kb_id
                line = f"  {i}. {name}\n     ID: {kb_id}"
                if desc:
                    line += f"\n     描述: {desc}"
                result_lines.append(line)
        else:
            msg = data.get('msg', '未知错误')
            return json.dumps({
                "message": f"获取失败 (code={data.get('code')}): {msg}"
            }, ensure_ascii=False)

        if not result_lines:
            return "未找到任何知识库。"

        header = "=== IMA 知识库列表 (名称-ID对照表) ===\n"
        header += "请将对应的 knowledge_base_id 填入 config.yaml 的 tencent_ima 配置中\n\n"
        footer = f"\n共 {len(result_lines)} 个知识库"

        return header + "\n".join(result_lines) + footer

    def _format_results(self, query, data):
        """格式化返回结果"""
        results = []

        # IMA API 返回格式: {"code": 0, "msg": "...", "data": {...}}
        if data.get('code') == 0 and data.get('data'):
            items = data['data'].get('items', data['data'].get('knowledge_list', []))
            for item in items:
                results.append({
                    'title': item.get('title', '未知标题'),
                    'content': (item.get('highlight_content') or
                                item.get('snippet') or
                                item.get('content', ''))[:500],
                    'media_id': item.get('media_id', ''),
                    'source': 'IMA知识库',
                })

        msg = data.get('msg', '')
        if data.get('code') != 0:
            msg = f"API 错误 (code={data.get('code')}): {msg}"

        return json.dumps({
            "query": query,
            "total_results": len(results),
            "results": results,
            "message": msg or f"找到 {len(results)} 条匹配结果"
        }, ensure_ascii=False, indent=2)


# 全局单例
_ima_client = None


def _get_ima_client():
    global _ima_client
    if _ima_client is None:
        _ima_client = TencentIMAKnowledgeBase()
    return _ima_client


@tool("tencent_ima_search", parse_docstring=True)
async def tencent_ima_search(query: str, max_results: int = 10) -> str:
    """在腾讯 IMA 知识库中搜索相关信息。

    当用户询问产品知识、公司政策、技术文档等内容时使用此工具。
    返回与查询关键词最相关的文档摘要和来源。

    Args:
        query: 搜索关键词，可以是多个词（用空格分隔）
        max_results: 最大返回结果数量，默认10条
    """
    return await _get_ima_client().search(query, max_results=max_results)