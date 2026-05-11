#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 http://100.100.1.2:1234/v1 模型服务"""

import sys
import time

try:
    from openai import OpenAI
except ImportError:
    print("❌ 无法导入 OpenAI", file=sys.stderr)
    sys.exit(1)


def main():
    print("=" * 80)
    print("【测试 100.100.1.2:1234 模型服务】")
    print("=" * 80)

    try:
        # 创建客户端
        client = OpenAI(
            api_key="sk-lm-I2F1KwzT:4GHgM5on0Aedy2AFmok7",
            base_url="http://100.100.1.2:1234/v1"
        )

        print("✅ 客户端初始化成功")
        print(f"URL: http://100.100.1.2:1234/v1")

        # 测试1: 获取模型列表
        print("\n测试1: 获取模型列表")
        start = time.time()
        models = client.models.list()
        end = time.time()
        model_ids = [m.id for m in models.data]
        print(f"✅ 可用模型: {', '.join(model_ids)}")
        print(f"⏱️ 耗时: {end - start:.2f} 秒")

        # 测试2: 简单推理请求
        print("\n测试2: 简单推理请求 (qwen3.6-27b)")
        print("发送请求...")
        start = time.time()

        response = client.chat.completions.create(
            model="qwen3.6-27b",
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍一下你自己。"}
            ],
            max_tokens=100,
            temperature=0.1,
            timeout=180
        )

        end = time.time()

        print(f"✅ 响应成功！耗时: {end - start:.2f} 秒")
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