from text_extractor import SalesTextPostProcessor
import json

# 根据"提取文本.txt"中的销售对话，模拟LLM提取结果
# 对话内容分析：
# - 客户试驾至境E7
# - 客户有2个儿子，关注防晕车
# - 客户对比过蓝骏出租车（晕车）
# - 客户晕车，对电车不晕
# - 关注智驾、续航、隔音、座椅材质
# - 员工介绍插混车型，优惠9000
# - 客户试驾体验良好
llm_result = {
    "detailed_extraction": [
        {
            "id": "1669",
            "dimension": "意向车型",
            "is_match": True,
            "value": "至境E7",
            "remarks": "客户试驾至境E7",
            "original_utterances": "员工：至境E7试驾. 客户：开始"
        },
        {
            "id": "1672",
            "dimension": "预算区间",
            "is_match": False,
            "value": "未提及",
            "remarks": "对话中未提及具体预算",
            "original_utterances": ""
        },
        {
            "id": "1675",
            "dimension": "客户类型",
            "is_match": True,
            "value": "首次到店",
            "remarks": "客户首次试驾",
            "original_utterances": "员工：还有人来吗？客户：全带全家都在"
        },
        {
            "id": "1680",
            "dimension": "用途",
            "is_match": True,
            "value": "家用",
            "remarks": "客户有2个儿子，关注家用大六座SUV",
            "original_utterances": "客户：没有我觉得我儿子我两个儿子用车了没"
        },
        {
            "id": "1683",
            "dimension": "对比车型",
            "is_match": True,
            "value": "蓝骏出租车",
            "remarks": "客户提及之前坐蓝骏出租车晕车",
            "original_utterances": "客户：我摩本来就开了，我也晕车，蓝骏的出租车我真坐坐不住"
        },
        {
            "id": "1685",
            "dimension": "决策人",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及决策人",
            "original_utterances": ""
        },
        {
            "id": "1687",
            "dimension": "体验动作",
            "is_match": True,
            "value": "试乘试驾",
            "remarks": "客户完成试驾体验",
            "original_utterances": "客户：试驾。没，他是宁"
        },
        {
            "id": "1716",
            "dimension": "身份",
            "is_match": False,
            "value": "未提及",
            "remarks": "未明确提及身份",
            "original_utterances": ""
        },
        {
            "id": "1717",
            "dimension": "购车阶段",
            "is_match": True,
            "value": "了解阶段",
            "remarks": "客户首次试驾了解阶段",
            "original_utterances": "员工：至境E7试驾. 客户：开始"
        },
        {
            "id": "1718",
            "dimension": "意向配置",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及具体配置意向",
            "original_utterances": ""
        },
        {
            "id": "1719",
            "dimension": "意向动力",
            "is_match": True,
            "value": "插混",
            "remarks": "员工介绍插混车型，客户体验了插混模式",
            "original_utterances": "员工：这个车它为啥就我就真龙插混去"
        },
        {
            "id": "1720",
            "dimension": "意向外观/内饰",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及颜色偏好",
            "original_utterances": ""
        },
        {
            "id": "1721",
            "dimension": "关注点",
            "is_match": True,
            "value": "防晕",
            "remarks": "客户关注电车防晕功能",
            "original_utterances": "客户：就说这个是防晕的对"
        },
        {
            "id": "1721",
            "dimension": "关注点",
            "is_match": True,
            "value": "配置",
            "remarks": "客户关注智驾配置",
            "original_utterances": "员工：这个车的顶配的话，智驾这安吗"
        },
        {
            "id": "1722",
            "dimension": "痛点",
            "is_match": False,
            "value": "未提及",
            "remarks": "未明确提及痛点",
            "original_utterances": ""
        },
        {
            "id": "1723",
            "dimension": "购车方式",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及贷款或全款",
            "original_utterances": ""
        },
        {
            "id": "1724",
            "dimension": "置换意向",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及置换",
            "original_utterances": ""
        },
        {
            "id": "1725",
            "dimension": "金融意向",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及金融方案",
            "original_utterances": ""
        },
        {
            "id": "1727",
            "dimension": "顾虑点/关注点",
            "is_match": False,
            "value": "未提及",
            "remarks": "未明确提及顾虑",
            "original_utterances": ""
        },
        {
            "id": "1728",
            "dimension": "购车时间",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及购车时间",
            "original_utterances": ""
        },
        {
            "id": "1729",
            "dimension": "决策障碍",
            "is_match": False,
            "value": "未提及",
            "remarks": "未提及决策障碍",
            "original_utterances": ""
        },
        {
            "id": "1730",
            "dimension": "客户态度",
            "is_match": True,
            "value": "积极",
            "remarks": "客户态度积极，体验良好",
            "original_utterances": "客户：你俩配合三个不晕吧，晕吧，行，是比"
        }
    ]
}

# 创建后处理器
processor = SalesTextPostProcessor()

# 处理LLM提取结果
result = processor.process(json.dumps(llm_result))

# 输出结果
print("=" * 70)
print("【销售对话文本提取测试】")
print("=" * 70)

# 打印提取结果统计
matched = sum(1 for d in result['detailed_extraction'] if d['is_match'])
unmatched = len(result['detailed_extraction']) - matched

print(f"\n📊 提取统计：共 {len(result['detailed_extraction'])} 个维度")
print(f"   ✅ 已匹配: {matched} 个")
print(f"   ❌ 未提及: {unmatched} 个")

# 打印详细结果
print("\n" + "-" * 70)
print("📋 详细提取结果：")
print("-" * 70)

for dim in result['detailed_extraction']:
    status = "✅" if dim['is_match'] else "❌"
    value = dim['value'] if dim['value'] else "(空)"
    remarks = dim.get('remarks', '') if dim.get('remarks') else ""
    print(f"{status} [{dim['id']}] {dim['dimension']}: {value}")
    if remarks and dim['is_match']:
        print(f"   📝 {remarks}")

# 打印摘要标签
print("\n" + "-" * 70)
print("🏷️  摘要标签：")
print("-" * 70)

for tag_type, tags in result['summary_tags'].items():
    if tags and len(tags) > 0 and tags[0].get('value'):
        print(f"\n【{tag_type}】")
        for tag in tags:
            print(f"   {tag['value']}")
            if tag.get('original_utterances'):
                print(f"   📌 原文: {tag['original_utterances']}")

# 输出完整JSON
print("\n" + "=" * 70)
print("【完整JSON输出】")
print("=" * 70)
print(json.dumps(result, indent=2, ensure_ascii=False))
