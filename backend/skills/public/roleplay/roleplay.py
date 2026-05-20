"""
至境E7展厅接待对练技能入口

本技能提供基于知识库的自由对练功能，用户可以直接从界面触发。
"""

import sys
import os
import json
import asyncio

# 添加roleplay-agent的路径
_roleplay_path = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "..", ".deer-flow", "agents", "roleplay-agent", "src"
)
if _roleplay_path not in sys.path:
    sys.path.insert(0, _roleplay_path)


def main():
    """技能主入口函数"""
    # 解析输入参数
    input_data = {}
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.argv[1])
        except:
            pass
    
    scenario_count = input_data.get("scenario_count", 5)
    mode = input_data.get("mode", "free")
    
    print("🎯 正在启动「至境E7」展厅接待对练...")
    
    # 创建对练Agent实例
    try:
        from agent import RoleplayAgent
        agent = RoleplayAgent()
        
        # 开始对练会话（使用自由模式）
        session = agent.start_session(num_scenarios=scenario_count, mode=mode)
        
        result = {
            "session_id": session.get("session_id", ""),
            "status": "started",
            "first_message": session.get("first_message", ""),
            "total_rounds": session.get("total_rounds", scenario_count),
            "message": "对练会话已创建"
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        result = {
            "status": "error",
            "message": f"启动对练失败: {str(e)}"
        }
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
