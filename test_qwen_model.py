#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 qwen3.6-27b 模型响应"""

import sys

try:
    from deerflow.client import DeerFlowClient
    HAS_DEERFLOW = True
except ImportError as e:
    print(f"无法导入 DeerFlowClient: {e}", file=sys.stderr)
    HAS_DEERFLOW = False


def test_qwen_model():
    if not HAS_DEERFLOW:
        print("❌ 错误: 无法导入 DeerFlowClient")
        return
    
    print("=" * 80)
    print("【测试 qwen3.6-27b 模型响应】")
    print("=" * 80)
    
    try:
        # 初始化客户端
        client = DeerFlowClient(
            agent_name="text-extraction-agent",
            thinking_enabled=False
        )
        print("✅ DeerFlowClient 初始化成功")
        
        # 测试简单请求
        print("\n正在发送测试请求...")
        response = client.chat("你好，请用一句话介绍一下你自己。")
        
        print(f"\n✅ 模型响应成功！")
        print(f"响应长度: {len(response)} 字符")
        print(f"响应内容:\n{response}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_qwen_model()