import asyncio
from deerflow.models import create_chat_model
from langchain_core.messages import HumanMessage

async def test_llm():
    try:
        print("尝试创建LLM模型...")
        llm = create_chat_model(name=None, thinking_enabled=False)
        print("LLM模型创建成功")
        
        print("\n尝试调用LLM...")
        response = await llm.ainvoke([HumanMessage(content="你好，测试一下")])
        print(f"LLM响应: {response.content[:100]}...")
        return True
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_llm())