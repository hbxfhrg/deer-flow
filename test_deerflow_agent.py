#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整工作流测试 - 通过 DeerFlowClient 调用 Agent"""

import sys
import json
import os

# 添加 deerflow 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'packages', 'harness'))

try:
    from deerflow.client import DeerFlowClient
    HAS_DEERFLOW = True
except ImportError as e:
    print(f"无法导入 DeerFlowClient: {e}", file=sys.stderr)
    HAS_DEERFLOW = False


def load_sales_text(filepath):
    """加载销售对话文本"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # 提取实际对话内容（去除prompt部分）
            if '以下为分析文本' in content:
                return content.split('以下为分析文本')[1].strip()
            return content
    return ""


def main():
    print("=" * 80)
    print("【完整工作流测试】通过 DeerFlowClient 调用 Agent")
    print("=" * 80)
    
    if not HAS_DEERFLOW:
        print("❌ 错误: 无法导入 DeerFlowClient，请检查环境配置")
        return
    
    # 步骤1: 加载销售对话文本
    print("\n步骤1: 加载销售对话文本")
    print("-" * 80)
    sales_text = load_sales_text("提取文本.txt")
    if not sales_text:
        print("❌ 错误: 无法加载销售对话文本")
        return
    print(f"文本长度: {len(sales_text)} 字符")
    print(f"预览:\n{sales_text[:200]}...")
    
    # 步骤2: 初始化 DeerFlowClient
    print("\n步骤2: 初始化 DeerFlowClient")
    print("-" * 80)
    try:
        client = DeerFlowClient(
            agent_name="text-extraction-agent",
            thinking_enabled=False
        )
        print("✅ DeerFlowClient 初始化成功")
    except Exception as e:
        print(f"❌ DeerFlowClient 初始化失败: {e}")
        return
    
    # 步骤3: 调用 Agent 执行完整工作流
    print("\n步骤3: 调用 Agent 执行完整工作流")
    print("-" * 80)
    print("正在调用 LLM 提取 + Skill 后处理...")
    
    try:
        # 构建请求
        prompt = f"""请分析以下销售对话文本，提取21个维度信息：

【销售对话】
{sales_text}

请返回包含 detailed_extraction 和 summary_tags 的 JSON 格式结果。
"""
        
        # 调用 Agent
        response = client.chat(prompt)
        print("✅ Agent 调用成功")
        
        # 解析结果
        print("\n步骤4: 解析结果")
        print("-" * 80)
        
        # 提取 JSON
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            json_str = response
        
        print(f"JSON字符串长度: {len(json_str)}")
        print(f"JSON预览:\n{json_str[:500]}...")
        
        result = json.loads(json_str)
        print("✅ 结果解析成功")
        print(f"结果类型: {type(result)}")
        print(f"结果键: {result.keys() if isinstance(result, dict) else '不是字典'}")
        
        # 步骤5: 输出详细提取结果
        print("\n步骤5: 详细提取结果")
        print("-" * 80)
        print(f"字段说明: value(维度值) | remarks(命中原因) | original_utterances(客户原话)")
        print("-" * 80)
        
        if 'detailed_extraction' in result:
            matched_count = sum(1 for item in result['detailed_extraction'] if item.get('is_match'))
            print(f"提取维度数: {len(result['detailed_extraction'])}")
            print(f"已匹配: {matched_count} | 未提及: {len(result['detailed_extraction']) - matched_count}")
            
            print("\n详细信息:")
            for item in result['detailed_extraction']:
                status = "OK" if item.get('is_match') else "--"
                print(f"{status} {item['dimension']}: {item['value']}")
        
        # 步骤6: 输出会话总结标签
        print("\n步骤6: 会话总结标签")
        print("-" * 80)
        if 'summary_tags' in result:
            for tag_name, tag_items in result['summary_tags'].items():
                if tag_items and tag_items[0].get('is_match'):
                    print(f"## {tag_name}: {tag_items[0]['value']}")
                else:
                    print(f"## {tag_name}: （无匹配信息）")
        
        # 步骤7: 保存结果
        output_file = "deerflow_extraction_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")
        
        # 步骤8: 显示完整JSON（部分）
        print("\n步骤7: JSON格式输出（部分）")
        print("-" * 80)
        output_json = json.dumps(result, ensure_ascii=False, indent=2)
        print(output_json[:3000] + "..." if len(output_json) > 3000 else output_json)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"原始响应:\n{response}")
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("工作流测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
