"""测试完整工作流 - 使用真实销售对话文本"""
import sys
import json
import os

# 添加 skills 路径（text-extraction 目录）
sys.path.insert(0, r"d:\deer-flow\skills\public\text-extraction")

from text_extractor import SalesTextPostProcessor

# 直接使用 OpenAI API 调用 LiteLLM
from openai import OpenAI

class LiteLLMClient:
    """直接调用 LiteLLM API"""
    def __init__(self):
        self.client = OpenAI(
            api_key="litellmkey",
            base_url="http://100.100.1.1:4000/v1"
        )
    
    def chat(self, prompt, model="glm-4.6v-flash", max_tokens=4096):
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content

def extract_in_chunks(client, text, chunk_size=1500):
    """分段提取长文本 - 简化版本"""
    results = []
    text_length = len(text)
    start = 0
    chunk_num = 0
    
    print(f"文本长度: {text_length} 字符")
    
    while start < text_length:
        chunk_num += 1
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        
        print(f"处理片段 {chunk_num}: {start+1}-{end} 字符")
        
        # 调用LLM提取
        result = extract_single_chunk(client, chunk, chunk_num)
        if result:
            results.append(result)
        
        # 移动到下一段（跳过已处理的部分）
        start = end
    
    # 合并结果
    return merge_results(results)

def extract_single_chunk(client, chunk, chunk_num):
    """提取单个文本片段 - 简化prompt减少token"""
    prompt = f"""提取销售对话关键信息，输出格式：维度名|值|原文

对话：
{chunk}

维度：意向车型,预算区间,客户类型,用途,对比车型,决策人,体验动作,身份,购车阶段,意向配置,意向动力,意向外观/内饰,关注点,痛点,购车方式,置换意向,金融意向,顾虑点,购车时间,决策障碍,客户态度

未提及填：维度名|未提及|
"""
    
    try:
        response = client.chat(prompt)
        # 添加调试输出
        print(f"片段 {chunk_num} LLM响应:")
        print(f"{response[:500]}...")
        return parse_simple_format(response)
    except Exception as e:
        print(f"提取片段 {chunk_num} 失败: {str(e)[:100]}")
        return None

def parse_simple_format(response):
    """解析简单格式的输出"""
    extraction_map = {}
    lines = response.strip().split('\n')
    
    for line in lines:
        # 跳过空行和格式说明行
        if not line or '维度名' in line or '---' in line:
            continue
        
        # 按 | 分割
        parts = line.split('|')
        if len(parts) >= 2:
            dimension = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            original = parts[2].strip() if len(parts) > 2 else ""
            
            if dimension and value:
                # 根据用户要求设置字段
                is_match = value != '未提及'
                extraction_map[dimension] = {
                    'value': value,  # 保持原始值，包括"未提及"
                    'remarks': '已识别' + dimension if is_match else '对话中未提及' + dimension,  # 命中原因
                    'original_utterances': original if original else '',  # 客户原话
                    'is_match': is_match
                }
    
    return extraction_map

def merge_results(results):
    """合并多个片段的提取结果"""
    merged = {}
    
    for result in results:
        for dimension, data in result.items():
            if dimension not in merged:
                merged[dimension] = data.copy()
            else:
                # 如果已有数据且当前数据也是匹配的，合并原文依据
                if data.get('is_match'):
                    existing = merged[dimension]
                    # 合并值（保持标准格式）
                    if existing.get('value') and existing['value'] != '未提及':
                        if data.get('value') and data['value'] != '未提及' and existing['value'] != data['value']:
                            existing['value'] = existing['value'] + '; ' + data['value']
                    elif data.get('value') and data['value'] != '未提及':
                        existing['value'] = data['value']
                    # 合并原文依据
                    if existing.get('original_utterances'):
                        if data.get('original_utterances'):
                            existing['original_utterances'] = existing['original_utterances'] + '; ' + data['original_utterances']
                    else:
                        existing['original_utterances'] = data.get('original_utterances', '')
                    # 更新命中状态
                    existing['is_match'] = True
                    existing['remarks'] = '已识别' + dimension
    
    return merged

def convert_to_standard_format(extraction_map):
    """转换为标准JSON格式"""
    dimension_id_map = {
        '意向车型': '1669',
        '预算区间': '1672',
        '客户类型': '1675',
        '用途': '1680',
        '对比车型': '1683',
        '决策人': '1685',
        '体验动作': '1687',
        '身份': '1716',
        '购车阶段': '1717',
        '意向配置': '1718',
        '意向动力': '1719',
        '意向外观/内饰': '1720',
        '关注点': '1721',
        '痛点': '1722',
        '购车方式': '1723',
        '置换意向': '1724',
        '金融意向': '1725',
        '顾虑点/关注点': '1727',
        '购车时间': '1728',
        '决策障碍': '1729',
        '客户态度': '1730'
    }
    
    detailed_extraction = []
    
    for dimension, dim_id in dimension_id_map.items():
        data = extraction_map.get(dimension, {})
        is_match = data.get('is_match', False)
        value = data.get('value', '') if is_match else '未提及'
        remarks = data.get('remarks', '') if is_match else f"对话中未提及{dimension}"
        original_utterances = data.get('original_utterances', '')
        
        detailed_extraction.append({
            'id': dim_id,
            'dimension': dimension,
            'is_match': is_match,
            'value': value,           # 标准维度值
            'remarks': remarks,       # 命中原因（来自提取结果）
            'original_utterances': original_utterances  # 客户原话
        })
    
    return {'detailed_extraction': detailed_extraction}
sales_conversation = """
员工：那我开客边，明天做副驾人前面，那我开客户经9。员工：至境E7试驾. 客户：开始。员工：还有人吗？可以请，有吗？全带全家都在，后面都北金毛后面都在线。有人吗，零打个电话。舞蹈。员工：你好，别克。打开全车座椅通风。员工：早小前一天，最后一天。做完什么什么做车呢？项版版PL。如果我如享500的话，一享现。员工：像这车的话，它就出现形车的一个限名称，就是你在加热车的。线发动过车，你这他赛的点。员工：再一个就是在试驾的时候，就是一个。200乘价格较千的情况下，里面也是一万多。员工：他拿了一个。员工：导航到白银。第一个我们设。员工：现在亚车联网上。员工：说明这个行车比较车。员工：检车的尺寸。设就设新加。员工：车行是指向标本的。员工：车架构如果加构的话。因为现在L2的话，目前是L22外加莱拉的话，没没手机要打我们之强，没有哪个厂家敢测出下一天测。442那是外国的，中国的fs照样才是了手。目前还在内动车上，没有完全错。员工：稍微一点的。20座。员工：发。舱。到大学会要求老师希望失别的。员工：华P的话已经华为没啥区别了，但是华为的话成为了车上选装智驾体验的作为目光。万车六项所的话，你们下车启动再。员工：现在我就先用个充电模式来感受一下这车加速隔音器。现在就先用的充电，就大概踩个一万的油门，感受一下这个加速。你这么加速，你既听不见电池的车叫声，你也听见。是，就现在就130感住的，而且这个路是比较粗糙的状况，应该感受一下它外面的风噪太噪，所以说就没有，因为这个是单车资源的车置，跟前排用的超松端，这个车就是全车的四块都是双层的。而且你看这个大客，它就直接就两，你看这二级上去一下就会做了，威是倒车来或者晃起。假如这个是充电，然后咱就从三台车电，这个车它为啥就我就真龙插混去。因为咱们电跟没电加速线的差0.1到0.2秒，说白了就是你人是开不出来这种几0.7秒的差别的，你只有拿机器测。你才能测出来。员工：现在这个电动车就全车满座，然后是一个双层。你如果这用深门浅就发布机声音，可以说你最近见。如果是其他厂加热插孔的话，你需要支穿规滤的输出的话，发动机的声音直接一爆发出来就可以一个设置电池叫轰鸣声。这个的话你前跑几百家，我再踩油还是有尊备感。然后苏也没有说是电车的能量车金融版，人家有能量回收吗？电车最有能量回收，但是你看我这么连的，踩几脚车最终有违感。但是那时是把人犹豫的种感觉。如果是一般的电车，踩脚做一寸松，二是就行了。员工：然后这个车应该是威朗拉萨雷，我下基本上让海小数字越来越享受。员工：境帕特子的话，那肯定你这个你正常就家庭用的大部座SUV大会对刹车汽车化上车汽车版表现前版比较好。我这正常驾驶裸车交通规则。现在就是电动模式，而且这个车你上曾经绍这些anc主要降噪。它像这个价位里牌很少有车停做在AC别克的话，它是供车三十多元，但是其他车不知道，反正就这种刹车的话，肯定不是这好。而且别克的操控性一直在他家格里面蛮不错。员工：而且这车的刹车跟油门都比较线性，就是你踩多少来多少，有没有那些虚位。员工：你那个你好，别克。打开后仓智慧屏。没有我觉得我儿子我两个儿子用车了没。就说这个是防晕的对，这个反正我感觉是电车里面质感最好的这个你就算你看你这么猛槛，但是我觉得你开的时候蒙踩的时候还是人用势。我摩本来就开了，我也晕车，蓝骏的出租车我真坐坐不住。我这个我感觉反正我感觉是没有你这个意思，他反正一点能量回收那种感觉都没有，而且这个是可以调的。现在就是做泰能调节最强的话也跟反正也比其他的时平多像调节弱的时候是我感觉到0。员工：这个。员工：而且这个车的顶配的话，智驾这安吗？智驾的话就成我们体验这个开智驾必须要经过一个半个小时左右的一个视频学习。就是提醒你什么时候该接管，试驾的时候需要注意啥，就是一个安全常识。如果你买这个车的话，就在艾别克兰的视频，然后驱完以后自造自那个答案，这个自动期的一个考试，考完就可以开始驾。你看从前面电门口出来到这儿，这全是为了他自己动。员工：这个车我感觉皮还是比一皮油车大部分油车没有平衡。这个车反正百分里加速是6.8秒，就算亏电以后才就是在7秒。它比一般的超篷车配件以后，他就声音保存或者动能减弱，有就本没啥感觉。客户：你俩配合三个不晕吧，晕吧，行，是比。员工：较快亮，甚至境单就这个车牌正，啥都没模，都没钱折店重塑试盖。这是下午在单位的设备，向给人再。客户：试驾。没，他是宁。员工：对，之前金流客优是吧？我太蓝智驾。这个智驾的话，就你可以在网上了解一下摩门塔20，这个确实是，反正至景去年的话之前还在过出版这的智驾的比赛四刹一次，近期优惠9000。而且你看SA因为它有这个二级资产挂，你像拐湾早的说的，它支撑线它要比一般的SU要好一点。员工：我在北京汉在最中间之前。员工：这个车窗静音性，还有这个整就整个座椅的材质。因为这个是用的是GL8同款的一个座椅，而
"""

def main():
    print("=" * 80)
    print("【完整工作流测试】销售对话文本提取")
    print("=" * 80)

    # 步骤1: 使用 LLM 分段提取原始信息
    print("\n步骤1: 使用 LLM 分段提取销售对话维度...")
    print("-" * 80)

    client = LiteLLMClient()

    # 使用分段提取方法
    extraction_map = extract_in_chunks(client, sales_conversation)
    
    # 转换为标准JSON格式
    llm_result = convert_to_standard_format(extraction_map)
    
    print(f"\nLLM分段提取完成！")
    print(f"提取了 {len([d for d in llm_result['detailed_extraction'] if d['is_match']])} 个匹配维度")

    # 步骤2: 使用 Skill 进行后处理
    print("\n步骤2: 使用 Skill 后处理器进行标准化处理...")
    print("-" * 80)

    # 创建后处理器实例
    processor = SalesTextPostProcessor()

    # 调用后处理方法
    result = processor.process(llm_result)

    # 步骤3: 输出最终结果
    print("\n步骤3: 输出最终结果...")
    print("-" * 80)

    # 统计匹配数量
    matched_count = sum(1 for item in result['detailed_extraction'] if item['is_match'])
    total_count = len(result['detailed_extraction'])

    print(f"\n提取统计：共{total_count}个维度 | 已匹配: {matched_count} | 未提及: {total_count - matched_count}")

    # 打印详细提取结果
    print("\n详细提取结果：")
    print("-" * 80)
    for item in result['detailed_extraction']:
        status = "OK" if item['is_match'] else "--"
        print(f"{status} {item['dimension']}: {item['value']}")

    # 打印摘要标签
    print("\n会话总结标签：")
    print("-" * 80)
    for tag_name, tag_items in result['summary_tags'].items():
        if tag_items and tag_items[0]['is_match']:
            print(f"## {tag_name}: {tag_items[0]['value']}")
        else:
            print(f"## {tag_name}: （无匹配信息）")

    # 输出JSON格式结果
    print("\nJSON格式输出：")
    print("-" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 保存结果到文件
    output_file = "extraction_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
