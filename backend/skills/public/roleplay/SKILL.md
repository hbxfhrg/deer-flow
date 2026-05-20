---
name: roleplay
display_name: 至境E7展厅接待对练
description: 基于知识库内容进行至境E7展厅接待场景的自由对练，模拟真实客户对话，提供多维度评估和反馈。
version: 1.0.0
author: DeerFlow
email: support@deerflow.com
url: https://deerflow.com

type: python
entrypoint: roleplay.py

input_schema:
  type: object
  properties:
    scenario_count:
      type: integer
      title: 场景数量
      description: 生成的对练场景数量
      default: 5
      minimum: 1
      maximum: 10
    mode:
      type: string
      title: 对练模式
      description: 对练模式选择
      enum: ["free", "guided"]
      default: "free"

output_schema:
  type: object
  properties:
    session_id:
      type: string
      description: 对练会话ID
    status:
      type: string
      description: 会话状态
    first_message:
      type: string
      description: 第一条客户消息
    total_rounds:
      type: integer
      description: 总回合数

requirements: []

tags:
  - 对练
  - 角色扮演
  - 销售培训
  - 至境E7
---

## 使用说明

### 功能描述
本技能提供至境E7展厅接待场景的自由对练功能：
- 基于知识库内容动态生成对练场景
- 模拟真实客户进行自然对话
- 多维度评估学员表现
- 实时反馈和改进建议
- 生成综合评估报告

### 对练流程
1. 启动对练 → 系统生成客户开场白
2. 用户回复 → 系统评估并给出反馈
3. 继续对话 → 直到完成所有场景或手动结束
4. 生成报告 → 提供详细的评估结果

### 考核维度
- **产品知识**：对产品信息的掌握程度
- **表达能力**：语言表达和沟通技巧
- **倾听理解**：理解客户需求的能力
- **应对策略**：处理异议和促成交易的能力

### 输入参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| scenario_count | integer | 5 | 对练场景数量 |
| mode | string | free | 对练模式(free/guided) |

### 输出示例

```json
{
  "session_id": "roleplay-123456",
  "status": "started",
  "first_message": "您好，我想了解一下至境E7的续航能力...",
  "total_rounds": 5
}
```

### 结束对练
在对话中输入"结束"、"退出"、"quit"或"exit"即可结束对练并生成报告。
