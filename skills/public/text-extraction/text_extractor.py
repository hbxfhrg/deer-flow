#!/usr/bin/env python3
"""
销售对话文本提取工具 - LLM提取 + Skill后处理
LLM负责提取，Skill负责修正和补齐结果，并调用LLM生成会话总结
"""

import json
import re
import sys
import os

# 添加 deerflow 路径用于调用 LLM
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'packages', 'harness'))

try:
    from deerflow.client import DeerFlowClient
    HAS_DEERFLOW = True
except ImportError:
    HAS_DEERFLOW = False


class ConfigLoader:
    """配置加载器"""
    
    DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
    
    @staticmethod
    def _resolve_env_var(value):
        if not isinstance(value, str):
            return value
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'
        match = re.match(pattern, value)
        if match:
            env_var = match.group(1)
            default = match.group(2) if match.group(2) is not None else ""
            return os.environ.get(env_var, default)
        if value.startswith('$'):
            return os.environ.get(value[1:], value)
        return value
    
    @staticmethod
    def _resolve_config_env_vars(config):
        if isinstance(config, dict):
            return {k: ConfigLoader._resolve_config_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [ConfigLoader._resolve_config_env_vars(item) for item in config]
        else:
            return ConfigLoader._resolve_env_var(config)
    
    @staticmethod
    def load_config(config_path=None):
        path = config_path or ConfigLoader.DEFAULT_CONFIG_PATH
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return ConfigLoader._resolve_config_env_vars(config)
        return ConfigLoader.get_default_config()
    
    @staticmethod
    def get_default_config():
        return {
            "extraction": {
                "required_dimensions": [
                    {"id": "1669", "dimension": "意向车型"},
                    {"id": "1672", "dimension": "预算区间"},
                    {"id": "1675", "dimension": "客户类型"},
                    {"id": "1680", "dimension": "用途"},
                    {"id": "1683", "dimension": "对比车型"},
                    {"id": "1685", "dimension": "决策人"},
                    {"id": "1687", "dimension": "体验动作"},
                    {"id": "1716", "dimension": "身份"},
                    {"id": "1717", "dimension": "购车阶段"},
                    {"id": "1718", "dimension": "意向配置"},
                    {"id": "1719", "dimension": "意向动力"},
                    {"id": "1720", "dimension": "意向外观/内饰"},
                    {"id": "1721", "dimension": "关注点"},
                    {"id": "1722", "dimension": "痛点"},
                    {"id": "1723", "dimension": "购车方式"},
                    {"id": "1724", "dimension": "置换意向"},
                    {"id": "1725", "dimension": "金融意向"},
                    {"id": "1727", "dimension": "顾虑点/关注点"},
                    {"id": "1728", "dimension": "购车时间"},
                    {"id": "1729", "dimension": "决策障碍"},
                    {"id": "1730", "dimension": "客户态度"}
                ],
                "focus_options": ["价格", "续航", "空间", "油耗", "配置", "安全", "品牌"],
                "car_models": [
                    "至境E7", "至境世家", "至境L7", "GL8陆尊燃油版", "全新GL8陆尊",
                    "昂科威S", "昂科威PLUS", "君越", "君威", "GL8陆尚",
                    "GL8陆上公务舱", "别克世纪", "威朗Pro", "微蓝6", "别克E5"
                ]
            },
            "output": {
                "format": "json",
                "indent": 2,
                "ensure_ascii": False
            }
        }


class SalesTextPostProcessor:
    """销售对话文本后处理器 - 对LLM提取结果进行修正和补齐，并调用LLM生成会话总结"""

    def __init__(self, config=None, **kwargs):
        self.config = config or ConfigLoader.load_config()
        self._apply_overrides(**kwargs)
        self._extract_config()
        self._init_deerflow_client()

    def _init_deerflow_client(self):
        """初始化 DeerFlowClient 用于调用 LLM"""
        self.deerflow_client = None
        if HAS_DEERFLOW:
            try:
                self.deerflow_client = DeerFlowClient(
                    agent_name="text-extraction-agent",
                    thinking_enabled=False  # 关闭思考功能
                )
            except Exception as e:
                print(f"警告: 无法初始化 DeerFlowClient: {e}", file=sys.stderr)

    def _apply_overrides(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.config.get('extraction', {}):
                self.config['extraction'][key] = value
            elif key in self.config.get('output', {}):
                self.config['output'][key] = value

    def _extract_config(self):
        extraction_config = self.config['extraction']
        self.required_dimensions = extraction_config['required_dimensions']
        self.focus_options = extraction_config['focus_options']
        self.car_models = extraction_config['car_models']
        self.output_config = self.config.get('output', {})

    def process(self, llm_result):
        """
        处理LLM提取结果

        Args:
            llm_result: LLM返回的原始提取结果（dict或str）

        Returns:
            修正后的标准格式JSON
        """
        if isinstance(llm_result, str):
            llm_result = self._parse_llm_json(llm_result)

        detailed_extraction = self._normalize_dimensions(llm_result.get('detailed_extraction', []))
        summary_tags = self._generate_summary_tags_with_llm(detailed_extraction)

        return {
            "detailed_extraction": detailed_extraction,
            "summary_tags": summary_tags
        }

    def _parse_llm_json(self, text):
        """解析LLM返回的文本为JSON"""
        try:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            pass
        return {"detailed_extraction": [], "summary_tags": {}}

    def _normalize_dimensions(self, extractions):
        """标准化维度数据"""
        if not isinstance(extractions, list):
            extractions = []

        extracted = {e['dimension']: e for e in extractions if isinstance(e, dict) and 'dimension' in e}

        result = []
        for dim in self.required_dimensions:
            dim_id = dim['id']
            dim_name = dim['dimension']

            if dim_name in extracted:
                item = self._normalize_item(extracted[dim_name])
                item['id'] = dim_id
                result.append(item)
            else:
                result.append({
                    "id": dim_id,
                    "dimension": dim_name,
                    "is_match": False,
                    "value": "未提及",
                    "remarks": "未提及该维度信息",
                    "original_utterances": ""
                })

        return result

    def _normalize_item(self, item):
        """标准化单个维度项"""
        return {
            "dimension": item.get('dimension', ''),
            "is_match": item.get('is_match', True),
            "value": item.get('value', '未提及'),
            "remarks": item.get('remarks', ''),
            "original_utterances": item.get('original_utterances', '')
        }

    def _generate_summary_tags(self, extractions):
        """生成摘要标签 - 使用逻辑拼接（降级方案）"""
        tags = {}

        extraction_map = {item['dimension']: item for item in extractions if item.get('is_match')}

        tags['意向车型标签'] = self._generate_car_model_summary(extraction_map)
        tags['竞品对比标签'] = self._generate_competitor_summary(extraction_map)
        tags['客户基础标签'] = self._generate_customer_summary(extraction_map)
        tags['核心需求标签'] = self._generate_needs_summary(extraction_map)
        tags['预算与购车方式标签'] = self._generate_budget_summary(extraction_map)
        tags['购车决策信息标签'] = self._generate_decision_summary(extraction_map)
        tags['服务与行动标签'] = self._generate_action_summary(extraction_map)

        return tags

    def _generate_summary_tags_with_llm(self, extractions):
        """生成摘要标签 - 使用 LLM 生成连贯的会话总结"""
        # 如果没有 DeerFlowClient，使用降级方案
        if not self.deerflow_client:
            print("警告: DeerFlowClient 不可用，使用降级方案生成摘要", file=sys.stderr)
            return self._generate_summary_tags(extractions)

        # 构建提取结果文本，供 LLM 参考
        matched_items = [item for item in extractions if item.get('is_match')]
        extraction_text = "\n".join([
            f"- {item['dimension']}: {item['value']}（{item.get('original_utterances', '')[:50]}）" 
            for item in matched_items
        ])

        # 构建 LLM 提示词
        prompt = f"""请根据以下提取的销售对话维度信息，生成7个连贯的会话总结标签：

【提取的维度信息】
{extraction_text}

【生成要求】
1. 生成7个标签：意向车型标签、竞品对比标签、客户基础标签、核心需求标签、预算与购车方式标签、购车决策信息标签、服务与行动标签
2. 每个标签的 value 必须是连贯的总结句（2-4句），整合相关维度的关键点
3. 不需要在总结句中标注原文依据
4. 如果某个标签无信息可总结，value 应为空字符串，is_match 为 false
5. 输出格式为 JSON，包含 summary_tags 对象，每个标签是一个数组，数组中包含一个对象

【输出格式示例】
{{
  "summary_tags": {{
    "意向车型标签": [{{"id": "1690", "dimension": "意向车型标签", "is_match": true, "value": "客户意向车型为至境E7，对插混动力感兴趣。", "remarks": "", "original_utterances": ""}}],
    "竞品对比标签": [{{"id": "1690", "dimension": "竞品对比标签", "is_match": true, "value": "客户对比过汉兰达，认为其空间不足。", "remarks": "", "original_utterances": ""}}],
    "客户基础标签": [{{"id": "1690", "dimension": "客户基础标签", "is_match": true, "value": "首次到店客户，购车用途为家用。", "remarks": "", "original_utterances": ""}}],
    "核心需求标签": [{{"id": "1690", "dimension": "核心需求标签", "is_match": true, "value": "客户关注空间和安全配置。", "remarks": "", "original_utterances": ""}}],
    "预算与购车方式标签": [{{"id": "1690", "dimension": "预算与购车方式标签", "is_match": false, "value": "", "remarks": "", "original_utterances": ""}}],
    "购车决策信息标签": [{{"id": "1690", "dimension": "购车决策信息标签", "is_match": true, "value": "客户处于了解阶段，决策人为本人。", "remarks": "", "original_utterances": ""}}],
    "服务与行动标签": [{{"id": "1690", "dimension": "服务与行动标签", "is_match": true, "value": "客户完成试乘试驾，态度积极。", "remarks": "", "original_utterances": ""}}]
  }}
}}

请直接输出JSON，不需要任何解释。
"""

        try:
            response = self.deerflow_client.chat(prompt)
            
            # 提取 JSON
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
            return result.get('summary_tags', self._generate_summary_tags(extractions))
        
        except Exception as e:
            print(f"警告: LLM 调用失败，使用降级方案: {e}", file=sys.stderr)
            return self._generate_summary_tags(extractions)

    def _generate_car_model_summary(self, extraction_map):
        """生成意向车型标签总结"""
        car_model = extraction_map.get('意向车型')
        power_type = extraction_map.get('意向动力')
        config = extraction_map.get('意向配置')

        if not car_model:
            return [{"id": "1690", "dimension": "意向车型标签", "is_match": False, "value": "", "remarks": "", "original_utterances": ""}]

        parts = []
        sources = []

        parts.append(f"客户意向车型为{car_model['value']}")
        if car_model.get('original_utterances'):
            sources.append(car_model['original_utterances'])

        if power_type and power_type['value'] != '未提及':
            parts.append(f"，意向动力类型为{power_type['value']}")
            if power_type.get('original_utterances'):
                sources.append(power_type['original_utterances'])

        if config and config['value'] != '未提及':
            parts.append(f"，关注配置{config['value']}")
            if config.get('original_utterances'):
                sources.append(config['original_utterances'])

        summary = ''.join(parts) + "。"

        return [{"id": "1690", "dimension": "意向车型标签", "is_match": True, "value": summary, "remarks": "", "original_utterances": '; '.join(sources)}]

    def _generate_competitor_summary(self, extraction_map):
        """生成竞品对比标签总结"""
        competitor = extraction_map.get('对比车型')
        pain_point = extraction_map.get('痛点')

        if not competitor and not pain_point:
            return [{"id": "1690", "dimension": "竞品对比标签", "is_match": False, "value": "", "remarks": "", "original_utterances": ""}]

        parts = []
        sources = []

        if competitor and competitor['value'] != '未提及':
            parts.append(f"客户提及竞品车型{competitor['value']}")
            if competitor.get('original_utterances'):
                sources.append(competitor['original_utterances'])

        if pain_point and pain_point['value'] != '未提及':
            if parts:
                parts.append(f"，认为其{pain_point['value']}")
            else:
                parts.append(f"客户反馈痛点：{pain_point['value']}")
            if pain_point.get('original_utterances'):
                sources.append(pain_point['original_utterances'])

        summary = ''.join(parts) + "。"

        return [{"id": "1690", "dimension": "竞品对比标签", "is_match": True, "value": summary, "remarks": "", "original_utterances": '; '.join(sources)}]

    def _generate_customer_summary(self, extraction_map):
        """生成客户基础标签总结"""
        customer_type = extraction_map.get('客户类型')
        purpose = extraction_map.get('用途')
        identity = extraction_map.get('身份')

        if not customer_type and not purpose and not identity:
            return [{"id": "1690", "dimension": "客户基础标签", "is_match": False, "value": "", "remarks": "", "original_utterances": ""}]

        parts = []
        sources = []

        if customer_type and customer_type['value'] != '未提及':
            parts.append(f"客户类型为{customer_type['value']}")
            if customer_type.get('original_utterances'):
                sources.append(customer_type['original_utterances'])

        if purpose and purpose['value'] != '未提及':
            if parts:
                parts.append(f"，购车用途为{purpose['value']}")
            else:
                parts.append(f"购车用途为{purpose['value']}")
            if purpose.get('original_utterances'):
                sources.append(purpose['original_utterances'])

        if identity and identity['value'] != '未提及':
            if parts:
                parts.append(f"，身份为{identity['value']}")
            else:
                parts.append(f"身份为{identity['value']}")
            if identity.get('original_utterances'):
                sources.append(identity['original_utterances'])

        summary = ''.join(parts) + "。"

        return [{"id": "1690", "dimension": "客户基础标签", "is_match": True, "value": summary, "remarks": "", "original_utterances": '; '.join(sources)}]

    def _generate_needs_summary(self, extraction_map):
        """生成核心需求标签总结"""
        focus = extraction_map.get('关注点')
        concern = extraction_map.get('顾虑点/关注点')

        if not focus and not concern:
            return [{"id": "1690", "dimension": "核心需求标签", "is_match": False, "value": "", "remarks": "", "original_utterances": ""}]

        parts = []
        sources = []

        if focus and focus['value'] != '未提及':
            parts.append(f"客户关注点为{focus['value']}")
            if focus.get('original_utterances'):
                sources.append(focus['original_utterances'])

        if concern and concern['value'] != '未提及':
            if parts:
                parts.append(f"，顾虑点为{concern['value']}")
            else:
                parts.append(f"客户顾虑点为{concern['value']}")
            if concern.get('original_utterances'):
                sources.append(concern['original_utterances'])

        summary = ''.join(parts) + "。"

        return [{"id": "1690", "dimension": "核心需求标签", "is_match": True, "value": summary, "remarks": "", "original_utterances": '; '.join(sources)}]

    def _generate_budget_summary(self, extraction_map):
        """生成预算与购车方式标签总结"""
        budget = extraction_map.get('预算区间')
        purchase_method = extraction_map.get('购车方式')
        finance = extraction_map.get('金融意向')
        trade_in = extraction_map.get('置换意向')

        if not budget and not purchase_method and not finance and not trade_in:
            return [{"id": "1690", "dimension": "预算与购车方式标签", "is_match": False, "value": "", "remarks": "", "original_utterances": ""}]

        parts = []
        sources = []

        if budget and budget['value'] != '未提及':
            parts.append(f"客户预算区间为{budget['value']}")
            if budget.get('original_utterances'):
                sources.append(budget['original_utterances'])

        if purchase_method and purchase_method['value'] != '未提及':
            if parts:
                parts.append(f"，购车方式为{purchase_method['value']}")
            else:
                parts.append(f"购车方式为{purchase_method['value']}")
            if purchase_method.get('original_utterances'):
                sources.append(purchase_method['original_utterances'])

        if finance and finance['value'] != '未提及':
            if parts:
                parts.append(f"，有{finance['value']}金融意向")
            else:
                parts.append(f"有{finance['value']}金融意向")
            if finance.get('original_utterances'):
                sources.append(finance['original_utterances'])

        if trade_in and trade_in['value'] != '未提及':
            if parts:
                parts.append(f"，{trade_in['value']}置换意向")
            else:
                parts.append(f"{trade_in['value']}置换意向")
            if trade_in.get('original_utterances'):
                sources.append(trade_in['original_utterances'])

        summary = ''.join(parts) + "。"

        return [{"id": "1690", "dimension": "预算与购车方式标签", "is_match": True, "value": summary, "remarks": "", "original_utterances": '; '.join(sources)}]

    def _generate_decision_summary(self, extraction_map):
        """生成购车决策信息标签总结"""
        stage = extraction_map.get('购车阶段')
        decision_maker = extraction_map.get('决策人')
        obstacle = extraction_map.get('决策障碍')
        time = extraction_map.get('购车时间')

        if not stage and not decision_maker and not obstacle and not time:
            return [{"id": "1690", "dimension": "购车决策信息标签", "is_match": False, "value": "", "remarks": "", "original_utterances": ""}]

        parts = []
        sources = []

        if stage and stage['value'] != '未提及':
            parts.append(f"客户当前处于{stage['value']}")
            if stage.get('original_utterances'):
                sources.append(stage['original_utterances'])

        if decision_maker and decision_maker['value'] != '未提及':
            if parts:
                parts.append(f"，决策人为{decision_maker['value']}")
            else:
                parts.append(f"决策人为{decision_maker['value']}")
            if decision_maker.get('original_utterances'):
                sources.append(decision_maker['original_utterances'])

        if obstacle and obstacle['value'] != '未提及':
            if parts:
                parts.append(f"，决策障碍为{obstacle['value']}")
            else:
                parts.append(f"决策障碍为{obstacle['value']}")
            if obstacle.get('original_utterances'):
                sources.append(obstacle['original_utterances'])

        if time and time['value'] != '未提及':
            if parts:
                parts.append(f"，计划购车时间为{time['value']}")
            else:
                parts.append(f"计划购车时间为{time['value']}")
            if time.get('original_utterances'):
                sources.append(time['original_utterances'])

        summary = ''.join(parts) + "。"

        return [{"id": "1690", "dimension": "购车决策信息标签", "is_match": True, "value": summary, "remarks": "", "original_utterances": '; '.join(sources)}]

    def _generate_action_summary(self, extraction_map):
        """生成服务与行动标签总结"""
        action = extraction_map.get('体验动作')
        customer_attitude = extraction_map.get('客户态度')

        if not action and not customer_attitude:
            return [{"id": "1690", "dimension": "服务与行动标签", "is_match": False, "value": "", "remarks": "", "original_utterances": ""}]

        parts = []
        sources = []

        if action and action['value'] != '未提及':
            parts.append(f"客户进行了{action['value']}")
            if action.get('original_utterances'):
                sources.append(action['original_utterances'])

        if customer_attitude and customer_attitude['value'] != '未提及':
            if parts:
                parts.append(f"，客户态度{customer_attitude['value']}")
            else:
                parts.append(f"客户态度{customer_attitude['value']}")
            if customer_attitude.get('original_utterances'):
                sources.append(customer_attitude['original_utterances'])

        summary = ''.join(parts) + "。"

        return [{"id": "1690", "dimension": "服务与行动标签", "is_match": True, "value": summary, "remarks": "", "original_utterances": '; '.join(sources)}]

    def format_output(self, data):
        """格式化输出"""
        indent = self.output_config.get('indent', 2)
        return json.dumps(data, indent=indent, ensure_ascii=False)


def main():
    if len(sys.argv) > 1:
        llm_result = sys.argv[1]
    else:
        print("请输入LLM提取结果JSON：")
        llm_result = sys.stdin.read()

    processor = SalesTextPostProcessor()
    result = processor.process(llm_result)
    print(processor.format_output(result))


if __name__ == "__main__":
    main()
