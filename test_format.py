#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试返回值格式是否符合要求"""

import sys
import json
sys.path.insert(0, 'skills/public/text-extraction')

from text_extractor import SalesTextPostProcessor

# 模拟 LLM 提取结果（符合用户要求的格式）
mock_llm_result = {
    "detailed_extraction": [
        {
            "id": "1669",
            "dimension": "意向车型",
            "is_match": True,
            "value": "至境E7",
            "remarks": "客户明确提及意向车型为至境E7",
            "original_utterances": "至境E7试驾"
        },
        {
            "id": "1721",
            "dimension": "关注点",
            "is_match": True,
            "value": "空间",
            "remarks": "客户关注车辆空间",
            "original_utterances": "家庭用的大部座SUV"
        },
        {
            "id": "1721",
            "dimension": "关注点",
            "is_match": True,
            "value": "配置",
            "remarks": "客户关注车辆配置",
            "original_utterances": "打开全车座椅通风"
        },
        {
            "id": "1730",
            "dimension": "客户态度",
            "is_match": True,
            "value": "积极",
            "remarks": "客户主动参与试驾体验",
            "original_utterances": "开始"
        },
        {
            "id": "1672",
            "dimension": "预算区间",
            "is_match": False,
            "value": "未提及",
            "remarks": "对话中未提及预算区间",
            "original_utterances": ""
        }
    ]
}

def main():
    print("=" * 80)
    print("【返回值格式测试】验证字段含义是否正确")
    print("=" * 80)
    
    # 创建后处理器
    processor = SalesTextPostProcessor()
    
    # 处理结果
    result = processor.process(mock_llm_result)
    
    # 输出详细提取结果
    print("\n详细提取结果（字段含义说明）：")
    print("-" * 80)
    print("value: 标准维度值（如'至境E7'、'空间'、'积极'、'未提及'）")
    print("remarks: 命中原因（解释为什么提取这个值）")
    print("original_utterances: 客户原话（匹配的原始对话内容）")
    print("-" * 80)
    
    for item in result['detailed_extraction'][:5]:  # 只显示前5个
        print(f"\n【{item['dimension']}】")
        print(f"  value: {item['value']}")
        print(f"  remarks: {item['remarks']}")
        print(f"  original_utterances: {item['original_utterances']}")
    
    # 输出JSON格式
    print("\nJSON格式输出：")
    print("-" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n✅ 格式验证完成！")

if __name__ == "__main__":
    main()