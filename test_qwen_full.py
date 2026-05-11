#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整工作流测试 - 使用真实的 qwen3.6-27b 模型"""

import sys
import json
import os
import re
import time

sys.path.insert(0, 'skills/public/text-extraction')

from text_extractor import SalesTextPostProcessor, ConfigLoader


def load_sales_text(filepath):
    """加载销售对话文本"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if '以下为分析文本' in content:
                return content.split('以下为分析文本')[1].strip()
            return content
    return ""


def extract_with_llm(text, dimensions_config):
    """使用 LLM 提取维度信息"""
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key="sk-lm-I2F1KwzT:4GHgM5on0Aedy2AFmok7",
            base_url="http://100.100.1.2:1234/v1"
        )

        # 构建维度配置描述
        dim_descriptions = []
        for dim in dimensions_config:
            dim_id = dim['id']
            dim_name = dim['dimension']
            options = dim.get('options', dim.get('values', []))

            opts_str = ', '.join(options) if options else '开放式'
            dim_descriptions.append(f"{dim_id}. {dim_name}: {opts_str}")

        dim_config_str = '\n'.join(dim_descriptions)

        prompt = f"""请从以下销售对话中提取21个维度的信息：

【销售对话】
{text[:3000]}

【维度配置】
{dim_config_str}

【输出格式】
每个维度一行，格式：维度ID|维度名|值|客户原话

【规则】
1. 值必须在配置的取值范围内选择
2. 如果无法匹配，返回"未提及"
3. 客户原话必须是原始对话内容

请开始提取：
"""

        print(f"📝 发送请求，prompt长度: {len(prompt)}")
        start_time = time.time()

        response = client.chat.completions.create(
            model="qwen3.6-27b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1,
            timeout=300
        )

        end_time = time.time()
        print(f"⏱️ 响应时间: {end_time - start_time:.2f} 秒")

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ LLM调用失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def parse_llm_response(response, dimensions_config):
    """解析LLM响应"""
    extraction_map = {}
    lines = response.strip().split('\n')

    dim_id_to_config = {dim['id']: dim for dim in dimensions_config}
    dim_name_to_config = {dim['dimension']: dim for dim in dimensions_config}

    for line in lines:
        if not line or '---' in line:
            continue

        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                first_part = parts[0]
                second_part = parts[1]
                third_part = parts[2]
                fourth_part = parts[3] if len(parts) > 3 else ""

                dim_id = None
                dim_name = second_part

                # 尝试从第一部分提取 ID
                dim_id_match = re.match(r'^(\d+)', first_part)
                if dim_id_match:
                    dim_id = dim_id_match.group(1)
                    # 从第二部分提取维度名
                    name_match = re.match(r'^\d+\.?\s*(.+)', second_part)
                    if name_match:
                        dim_name = name_match.group(1)

                value = third_part
                original = fourth_part if fourth_part and fourth_part != '未提及' else ""

                if dim_name and value:
                    # 通过维度名查找配置
                    dim_config = dim_name_to_config.get(dim_name, {})
                    if not dim_config and dim_id:
                        dim_config = dim_id_to_config.get(dim_id, {})

                    options = dim_config.get('options', dim_config.get('values', []))
                    is_open = options == ['开放式'] or options == ['开放式文本'] or not options
                    is_match = value != '未提及' and (is_open or value in options)

                    extraction_map[dim_name] = {
                        'value': value,
                        'remarks': '已识别' + dim_name if is_match else '对话中未提及' + dim_name,
                        'original_utterances': original if original else '',
                        'is_match': is_match
                    }

    return extraction_map


def main():
    print("=" * 80)
    print("【完整工作流测试】使用 qwen3.6-27b (真实模型)")
    print("=" * 80)

    # 步骤1: 加载配置
    print("\n步骤1: 加载配置")
    print("-" * 80)
    config = ConfigLoader.load_config()
    dimensions_config = config['extraction']['required_dimensions']
    print(f"✅ 加载了 {len(dimensions_config)} 个维度配置")

    # 步骤2: 加载销售对话文本
    print("\n步骤2: 加载销售对话文本")
    print("-" * 80)
    sales_text = load_sales_text("提取文本.txt")
    if not sales_text:
        print("❌ 错误: 无法加载销售对话文本")
        return
    print(f"✅ 文本长度: {len(sales_text)} 字符")

    # 步骤3: 使用 LLM 提取
    print("\n步骤3: 使用 qwen3.6-27b 提取维度信息")
    print("-" * 80)
    llm_response = extract_with_llm(sales_text, dimensions_config)
    if not llm_response:
        print("❌ LLM调用失败")
        return

    print("✅ LLM提取完成")
    print(f"响应长度: {len(llm_response)}")
    print(f"\nLLM响应内容:\n{llm_response}")

    # 步骤4: 解析 LLM 响应
    print("\n步骤4: 解析 LLM 响应")
    print("-" * 80)
    extraction_map = parse_llm_response(llm_response, dimensions_config)
    print(f"✅ 解析出 {len(extraction_map)} 个维度")

    # 打印解析结果
    for name, item in extraction_map.items():
        print(f"  {name}: {item['value']} (is_match={item['is_match']})")

    # 步骤5: 转换为标准格式
    print("\n步骤5: 转换为标准格式")
    print("-" * 80)
    detailed_extraction = []
    for dim in dimensions_config:
        dim_name = dim['dimension']
        if dim_name in extraction_map:
            item = extraction_map[dim_name]
        else:
            item = {
                'value': '未提及',
                'remarks': '对话中未提及' + dim_name,
                'original_utterances': '',
                'is_match': False
            }
        detailed_extraction.append({
            'id': dim['id'],
            'dimension': dim_name,
            'value': item['value'],
            'remarks': item['remarks'],
            'original_utterances': item['original_utterances'],
            'is_match': item['is_match']
        })

    # 步骤6: 使用 Skill 进行后处理
    print("\n步骤6: 使用 Skill 进行后处理")
    print("-" * 80)
    processor = SalesTextPostProcessor()

    llm_result = {
        'detailed_extraction': detailed_extraction
    }

    result = processor.process(llm_result)
    print("✅ Skill后处理完成")

    # 步骤7: 输出结果
    print("\n步骤7: 提取结果")
    print("-" * 80)
    matched_count = sum(1 for item in result['detailed_extraction'] if item.get('is_match'))
    print(f"提取维度数: {len(result['detailed_extraction'])}")
    print(f"已匹配: {matched_count} | 未提及: {len(result['detailed_extraction']) - matched_count}")

    print("\n详细信息:")
    for item in result['detailed_extraction']:
        status = "✅" if item.get('is_match') else "❌"
        orig = item.get('original_utterances', '')[:50]
        print(f"{status} {item['dimension']}: {item['value']} | 原话: {orig}")

    # 步骤8: 会话总结
    print("\n步骤8: 会话总结标签")
    print("-" * 80)
    if 'summary_tags' in result:
        for tag_name, tag_items in result['summary_tags'].items():
            if tag_items and tag_items[0].get('is_match'):
                print(f"## {tag_name}: {tag_items[0]['value']}")
            else:
                print(f"## {tag_name}: （无匹配信息）")

    # 步骤9: 保存结果
    output_file = "qwen_extraction_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存到: {output_file}")

    print("\n" + "=" * 80)
    print("完整工作流测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()