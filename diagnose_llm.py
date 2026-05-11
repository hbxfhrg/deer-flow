#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""诊断大模型调用问题"""

import sys
import time
import json

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    print("❌ 无法导入 OpenAI", file=sys.stderr)
    HAS_OPENAI = False


def test_connection():
    """测试网络连接"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('100.100.1.1', 4000))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"连接测试失败: {e}", file=sys.stderr)
        return False


def test_model_list():
    """测试获取模型列表"""
    try:
        client = OpenAI(api_key="sk-lm-l2F1KwzT:4GHgM5on0Aedy2AFmok7", base_url="http://192.168.199.182:4000/v1")
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        return model_ids
    except Exception as e:
        print(f"获取模型列表失败: {e}", file=sys.stderr)
        return None


def test_simple_prompt():
    """测试简单prompt"""
    try:
        client = OpenAI(api_key="sk-lm-l2F1KwzT:4GHgM5on0Aedy2AFmok7", base_url="http://192.168.199.182:4000/v1")
        
        print("📝 发送简单请求...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="qwen3.6-27b",
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=10,
            temperature=0.1,
            timeout=60
        )
        
        end_time = time.time()
        print(f"⏱️ 响应时间: {end_time - start_time:.2f} 秒")
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ 请求失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("【大模型诊断测试】")
    print("=" * 80)
    
    # 测试1: 网络连接
    print("\n测试1: 网络连接")
    print("-" * 80)
    if test_connection():
        print("✅ 网络连接正常")
    else:
        print("❌ 网络连接失败")
        return
    
    # 测试2: 获取模型列表
    print("\n测试2: 获取模型列表")
    print("-" * 80)
    models = test_model_list()
    if models:
        print(f"✅ 可用模型: {', '.join(models)}")
    else:
        print("❌ 无法获取模型列表")
        return
    
    # 测试3: 简单请求
    print("\n测试3: 简单请求测试")
    print("-" * 80)
    response = test_simple_prompt()
    if response:
        print(f"✅ 响应成功: {response}")
    else:
        print("❌ 请求失败")
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    main()