#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""直接测试 qwen3.6-27b 模型"""

import sys
import os

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError as e:
    print(f"无法导入 OpenAI: {e}", file=sys.stderr)
    HAS_OPENAI = False


def test_qwen_direct():
    if not HAS_OPENAI:
        print("❌ 错误: 无法导入 OpenAI")
        return
    
    print("=" * 80)
    print("【直接测试 qwen3.6-27b 模型】")
    print("=" * 80)
    
    try:
        # 直接创建 OpenAI 客户端
        client = OpenAI(
            api_key="litellmkey",
            base_url="http://100.100.1.1:4000/v1"
        )
        print("✅ OpenAI 客户端初始化成功")
        
        # 测试简单请求
        print("\n正在发送测试请求...")
        response = client.chat.completions.create(
            model="qwen3.6-27b",
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍一下你自己。"}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        print(f"\n✅ 模型响应成功！")
        print(f"响应内容:\n{response.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_qwen_direct()