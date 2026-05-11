#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 LiteLLM 模型推理"""

import sys
import time

try:
    from openai import OpenAI
except ImportError:
    print("❌ 无法导入 OpenAI", file=sys.stderr)
    sys.exit(1)


def main():
    print("=" * 80)
    print("【测试 LiteLLM 模型推理】")
    print("=" * 80)
    
    try:
        # 创建客户端
        client = OpenAI(
            api_key="litellmkey",
            base_url="http://100.100.1.1:4000/v1"
        )
        
        print("✅ 客户端初始化成功")
        
        # 测试1: 获取模型列表
        print("\n测试1: 获取模型列表")
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        print(f"✅ 可用模型: {', '.join(model_ids)}")
        
        # 测试2: 简单推理请求
        print("\n测试2: 简单推理请求")
        print("发送请求...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="qwen3.6-27b",
            messages=[
                {"role": "user", "content": "你好"}
            ],
            max_tokens=50,
            temperature=0.1,
            timeout=120
        )
        
        end_time = time.time()
        
        print(f"✅ 响应成功！耗时: {end_time - start_time:.2f} 秒")
        print(f"响应内容: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()