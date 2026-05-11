#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整工作流测试 - 使用模拟数据验证逻辑"""

import sys
import json
import os

sys.path.insert(0, 'skills/public/text-extraction')

from text_extractor import SalesTextPostProcessor, ConfigLoader


def main():
    print("=" * 80)
    print("【完整工作流测试】使用模拟数据验证逻辑")
    print("=" * 80)
    
    # 步骤1: 加载配置
    print("\n步骤1: 加载配置")
    print("-" * 80)
    config = ConfigLoader.load_config()
    dimensions_config = config['extraction']['required_dimensions']
    print(f"✅ 加载了 {len(dimensions_config)} 个维度配置")
    
    # 步骤2: 创建模拟的LLM提取结果
    print("\n步骤2: 创建模拟的LLM提取结果")
    print("-" * 80)
    
    mock_extraction = [
        {"id": "1669", "dimension": "意向车型", "value": "至境E7", "remarks": "客户明确提及意向车型为至境E7", "original_utterances": "员工：至境E7试驾. 客户：开始。客户：试驾。", "is_match": True},
        {"id": "1672", "dimension": "预算区间", "value": "未提及", "remarks": "对话中未提及预算区间", "original_utterances": "", "is_match": False},
        {"id": "1675", "dimension": "客户类型", "value": "首次到店", "remarks": "客户首次到店体验", "original_utterances": "员工：您好，欢迎光临别克4S店。客户：你好，我想看看车。", "is_match": True},
        {"id": "1680", "dimension": "用途", "value": "家用", "remarks": "客户提及家庭使用需求", "original_utterances": "客户：我主要是家用，有两个孩子。", "is_match": True},
        {"id": "1683", "dimension": "对比车型", "value": "未提及", "remarks": "对话中未提及对比车型", "original_utterances": "", "is_match": False},
        {"id": "1685", "dimension": "决策人", "value": "本人", "remarks": "客户表示自己做主", "original_utterances": "客户：我自己决定就行。", "is_match": True},
        {"id": "1687", "dimension": "体验动作", "value": "试乘试驾", "remarks": "客户已完成试驾体验", "original_utterances": "员工：至境E7试驾. 客户：开始。客户：试驾。", "is_match": True},
        {"id": "1716", "dimension": "身份", "value": "客户", "remarks": "客户身份明确", "original_utterances": "客户：我想了解一下这款车。", "is_match": True},
        {"id": "1717", "dimension": "购车阶段", "value": "试驾评估期", "remarks": "客户正在试驾评估", "original_utterances": "员工：您觉得试驾感受怎么样？客户：还不错。", "is_match": True},
        {"id": "1718", "dimension": "意向配置", "value": "全车座椅通风", "remarks": "客户关注座椅通风功能", "original_utterances": "员工：你好，别克。打开全车座椅通风。", "is_match": True},
        {"id": "1719", "dimension": "意向动力", "value": "插混", "remarks": "客户关注插混动力", "original_utterances": "客户：这款车是插电混动的吗？员工：是的，支持快充。", "is_match": True},
        {"id": "1720", "dimension": "意向外观/内饰", "value": "未提及", "remarks": "对话中未提及意向外观/内饰", "original_utterances": "", "is_match": False},
        {"id": "1721", "dimension": "关注点", "value": "空间、配置", "remarks": "客户关注空间和配置", "original_utterances": "客户：空间够大吗？配置怎么样？", "is_match": True},
        {"id": "1722", "dimension": "痛点", "value": "晕车", "remarks": "客户提及晕车问题", "original_utterances": "客户：我有点晕车，这车平稳吗？", "is_match": True},
        {"id": "1723", "dimension": "购车方式", "value": "未提及", "remarks": "对话中未提及购车方式", "original_utterances": "", "is_match": False},
        {"id": "1724", "dimension": "置换意向", "value": "未提及", "remarks": "对话中未提及置换意向", "original_utterances": "", "is_match": False},
        {"id": "1725", "dimension": "金融意向", "value": "有", "remarks": "客户关注金融方案", "original_utterances": "客户：有什么金融优惠吗？", "is_match": True},
        {"id": "1727", "dimension": "顾虑点/关注点", "value": "未提及", "remarks": "对话中未提及顾虑点/关注点", "original_utterances": "", "is_match": False},
        {"id": "1728", "dimension": "购车时间", "value": "近1-3天", "remarks": "客户近期计划购车", "original_utterances": "客户：我想尽快提车，这两天能定下来吗？", "is_match": True},
        {"id": "1729", "dimension": "决策障碍", "value": "未提及", "remarks": "对话中未提及决策障碍", "original_utterances": "", "is_match": False},
        {"id": "1730", "dimension": "客户态度", "value": "积极", "remarks": "客户态度积极", "original_utterances": "客户：这款车我挺满意的，再谈谈价格。", "is_match": True}
    ]
    
    print(f"✅ 创建了 {len(mock_extraction)} 个维度的模拟数据")
    
    # 步骤3: 使用 Skill 进行后处理
    print("\n步骤3: 使用 Skill 进行后处理")
    print("-" * 80)
    processor = SalesTextPostProcessor()
    
    llm_result = {
        'detailed_extraction': mock_extraction
    }
    
    print("输入数据预览:")
    for item in llm_result['detailed_extraction'][:5]:
        print(f"  {item['dimension']}: {item['value']} (is_match={item['is_match']})")
    
    result = processor.process(llm_result)
    print("✅ Skill后处理完成")
    
    # 步骤4: 输出结果
    print("\n步骤4: 提取结果")
    print("-" * 80)
    matched_count = sum(1 for item in result['detailed_extraction'] if item.get('is_match'))
    print(f"提取维度数: {len(result['detailed_extraction'])}")
    print(f"已匹配: {matched_count} | 未提及: {len(result['detailed_extraction']) - matched_count}")
    
    print("\n详细信息:")
    for item in result['detailed_extraction']:
        status = "✅" if item.get('is_match') else "❌"
        orig = item.get('original_utterances', '')[:50]
        print(f"{status} {item['dimension']}: {item['value']} | 原话预览: {orig}")
    
    # 步骤5: 会话总结标签
    print("\n步骤5: 会话总结标签")
    print("-" * 80)
    if 'summary_tags' in result:
        for tag_name, tag_items in result['summary_tags'].items():
            if tag_items and tag_items[0].get('is_match'):
                print(f"## {tag_name}: {tag_items[0]['value']}")
            else:
                print(f"## {tag_name}: （无匹配信息）")
    
    # 步骤6: 保存结果
    output_file = "mock_extraction_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存到: {output_file}")
    
    print("\n" + "=" * 80)
    print("完整工作流测试完成！")
    print("注意: 此测试使用模拟数据，真实大模型调用需要后端服务正常运行")
    print("=" * 80)


if __name__ == "__main__":
    main()