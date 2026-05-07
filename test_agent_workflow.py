"""测试 text-extraction-agent 完整工作流"""
import sys
import json

# 添加 deerflow 路径
sys.path.insert(0, r"d:\deer-flow\backend\packages\harness")

from deerflow.client import DeerFlowClient

# 测试用的销售对话
sales_conversation = """
员工：您好，欢迎光临，请问您是第一次来吗？
客户：是的，我第一次来。想看看至境E7。
员工：好的，至境E7是我们最新的车型。请问您的预算是多少？
客户：大概15-20万吧。
员工：您是家用还是商务用？
客户：家用，两个孩子，所以比较关注空间和安全。
员工：您之前有看过其他品牌吗？
客户：我对比过汉兰达，感觉空间不够大。
员工：好的，您想试驾一下至境E7吗？
客户：可以，试驾一下吧。
"""

def main():
    print("=" * 70)
    print("测试 text-extraction-agent 完整工作流")
    print("=" * 70)

    # 创建 Agent
    client = DeerFlowClient(agent_name="text-extraction-agent")

    # 构建提示词 - 模拟 Agent 的工作流程
    prompt = f"""请分析以下销售对话，提取21个维度的信息。

销售对话：
{sales_conversation}

请按照以下步骤执行：

1. 首先，用你的LLM能力从对话中提取21个维度的原始信息，输出一个JSON对象，包含detailed_extraction数组

2. 然后，调用text-extraction skill对提取结果进行后处理（标准化、补齐缺失维度、生成摘要标签）

3. 最终输出标准化的JSON结果

重要：最终输出必须是一个有效的JSON，包含detailed_extraction和summary_tags两个键。
"""

    print("\n📝 发送请求到 Agent...")
    print("-" * 70)

    try:
        # 调用 Agent
        response = client.chat(prompt)

        print("\n📤 Agent 响应：")
        print("-" * 70)
        print(response)

        # 尝试解析 JSON 结果
        try:
            # 尝试从响应中提取 JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "{" in response:
                start = response.find("{")
                json_str = response[start:response.rfind("}") + 1]
            else:
                json_str = response

            result = json.loads(json_str)

            print("\n✅ JSON 解析成功！")
            print("\n📊 提取统计：")
            matched = sum(1 for d in result.get('detailed_extraction', []) if d.get('is_match', False))
            print(f"   已匹配维度: {matched}/21")

            print("\n📋 匹配到的维度：")
            for dim in result.get('detailed_extraction', []):
                if dim.get('is_match', False):
                    print(f"   ✅ {dim['dimension']}: {dim['value']}")

        except json.JSONDecodeError as e:
            print(f"\n⚠️ JSON 解析失败: {e}")
            print("Agent 可能还未实现完整的工作流")

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
