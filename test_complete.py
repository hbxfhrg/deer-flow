#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整工作流测试 - 使用模拟数据"""

import sys
import json
sys.path.insert(0, 'skills/public/text-extraction')

from text_extractor import SalesTextPostProcessor

# 模拟 LLM 提取结果（完整的21个维度）
mock_llm_result = {
    "detailed_extraction": [
        {"id": "1669", "dimension": "意向车型", "is_match": True, "value": "至境E7", "remarks": "客户明确提及意向车型为至境E7", "original_utterances": "员工：至境E7试驾. 客户：开始。"},
        {"id": "1672", "dimension": "预算区间", "is_match": False, "value": "未提及", "remarks": "对话中未提及预算区间", "original_utterances": ""},
        {"id": "1675", "dimension": "客户类型", "is_match": True, "value": "首次到店", "remarks": "客户首次到店体验", "original_utterances": "客户：开始。"},
        {"id": "1680", "dimension": "用途", "is_match": True, "value": "家用", "remarks": "客户提及家庭使用需求", "original_utterances": "员工：境帕特子的话，那肯定你这个你正常就家庭用的大部座SUV大会对刹车汽车化上车汽车版表现前版比较好。"},
        {"id": "1683", "dimension": "对比车型", "is_match": False, "value": "未提及", "remarks": "对话中未提及对比车型", "original_utterances": ""},
        {"id": "1685", "dimension": "决策人", "is_match": True, "value": "本人", "remarks": "客户表示自己做主", "original_utterances": "客户：没有我觉得我儿子我两个儿子用车了没。"},
        {"id": "1687", "dimension": "体验动作", "is_match": True, "value": "试乘试驾", "remarks": "客户已完成试驾体验", "original_utterances": "员工：至境E7试驾. 客户：开始。客户：试驾。"},
        {"id": "1716", "dimension": "身份", "is_match": True, "value": "客户", "remarks": "客户身份明确", "original_utterances": "员工：你好，别克。"},
        {"id": "1717", "dimension": "购车阶段", "is_match": True, "value": "试驾评估期", "remarks": "客户正在试驾评估", "original_utterances": "客户：试驾。"},
        {"id": "1718", "dimension": "意向配置", "is_match": True, "value": "全车座椅通风", "remarks": "客户关注座椅通风功能", "original_utterances": "员工：你好，别克。打开全车座椅通风。"},
        {"id": "1719", "dimension": "意向动力", "is_match": True, "value": "插混", "remarks": "客户关注插混动力", "original_utterances": "员工：因为咱们电跟没电加速线的差0.1到0.2秒，说白了就是你人是开不出来这种几0.7秒的差别的，你只有拿机器测。"},
        {"id": "1720", "dimension": "意向外观/内饰", "is_match": False, "value": "未提及", "remarks": "对话中未提及外观内饰偏好", "original_utterances": ""},
        {"id": "1721", "dimension": "关注点", "is_match": True, "value": "空间", "remarks": "客户关注空间", "original_utterances": "员工：境帕特子的话，那肯定你这个你正常就家庭用的大部座SUV大会对刹车汽车化上车汽车版表现前版比较好。"},
        {"id": "1721", "dimension": "关注点", "is_match": True, "value": "配置", "remarks": "客户关注配置", "original_utterances": "员工：你好，别克。打开全车座椅通风。员工：你那个你好，别克。打开后仓智慧屏。"},
        {"id": "1722", "dimension": "痛点", "is_match": True, "value": "晕车", "remarks": "客户提及晕车问题", "original_utterances": "客户：我摩本来就开了，我也晕车，蓝骏的出租车我真坐坐不住。"},
        {"id": "1723", "dimension": "购车方式", "is_match": False, "value": "未提及", "remarks": "对话中未提及购车方式", "original_utterances": ""},
        {"id": "1724", "dimension": "置换意向", "is_match": False, "value": "未提及", "remarks": "对话中未提及置换意向", "original_utterances": ""},
        {"id": "1725", "dimension": "金融意向", "is_match": True, "value": "有", "remarks": "客户关注金融方案", "original_utterances": "员工：如果我如享500的话，一享现。"},
        {"id": "1727", "dimension": "顾虑点/关注点", "is_match": False, "value": "未提及", "remarks": "对话中未提及顾虑点", "original_utterances": ""},
        {"id": "1728", "dimension": "购车时间", "is_match": True, "value": "近1-3天", "remarks": "客户近期计划购车", "original_utterances": "员工：早小前一天，最后一天。"},
        {"id": "1730", "dimension": "客户态度", "is_match": True, "value": "积极", "remarks": "客户态度积极", "original_utterances": "客户：开始。客户：试驾。客户：行，是比。"}
    ]
}

def main():
    print("=" * 80)
    print("【完整工作流测试】销售对话文本提取")
    print("=" * 80)

    # 步骤1: 显示模拟的LLM提取结果
    print("\n步骤1: LLM提取结果（模拟）")
    print("-" * 80)
    print(f"提取维度数: {len(mock_llm_result['detailed_extraction'])}")
    matched_count = sum(1 for item in mock_llm_result['detailed_extraction'] if item['is_match'])
    print(f"已匹配: {matched_count} | 未提及: {len(mock_llm_result['detailed_extraction']) - matched_count}")
    
    # 显示完整的LLM提取结果（包括原话）
    print("\n详细提取结果（含原话）:")
    print("-" * 80)
    print(f"{'维度':<12} {'值':<12} {'命中原因':<20} {'客户原话'}")
    print("-" * 80)
    for item in mock_llm_result['detailed_extraction']:
        status = "OK" if item['is_match'] else "--"
        print(f"{status} {item['dimension']:<10} {item['value']:<12} {item['remarks']:<20} {item['original_utterances']}")

    # 步骤2: 使用 Skill 进行后处理
    print("\n步骤2: Skill后处理")
    print("-" * 80)
    processor = SalesTextPostProcessor()
    result = processor.process(mock_llm_result)

    # 步骤3: 输出详细提取结果
    print("\n步骤3: 详细提取结果")
    print("-" * 80)
    print(f"字段说明: value(维度值) | remarks(命中原因) | original_utterances(客户原话)")
    print("-" * 80)
    
    for item in result['detailed_extraction']:
        status = "OK" if item['is_match'] else "--"
        print(f"{status} {item['dimension']}: {item['value']}")

    # 步骤4: 输出会话总结标签
    print("\n步骤4: 会话总结标签（无原话）")
    print("-" * 80)
    for tag_name, tag_items in result['summary_tags'].items():
        if tag_items and tag_items[0]['is_match']:
            print(f"## {tag_name}: {tag_items[0]['value']}")
        else:
            print(f"## {tag_name}: （无匹配信息）")

    # 步骤5: 输出JSON格式结果
    print("\n步骤5: JSON格式输出")
    print("-" * 80)
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    print(output_json[:2000] + "..." if len(output_json) > 2000 else output_json)

    # 保存结果
    output_file = "extraction_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")

    print("\n" + "=" * 80)
    print("✅ 完整工作流测试完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()