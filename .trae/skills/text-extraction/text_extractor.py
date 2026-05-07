#!/usr/bin/env python3
"""
销售对话文本提取工具 - LLM提取 + Skill后处理
LLM负责提取，Skill负责修正和补齐结果
"""

import json
import re
import sys
import os


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
    """销售对话文本后处理器 - 对LLM提取结果进行修正和补齐"""

    def __init__(self, config=None, **kwargs):
        self.config = config or ConfigLoader.load_config()
        self._apply_overrides(**kwargs)
        self._extract_config()

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
        summary_tags = self._generate_summary_tags(detailed_extraction)

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
        """生成摘要标签"""
        tags = {}

        car_model_tags = []
        for item in extractions:
            if item['dimension'] == '意向车型' and item['is_match']:
                car_model_tags.append({
                    "id": "1690",
                    "dimension": "意向车型标签",
                    "is_match": True,
                    "value": f"意向车型：{item['value']}",
                    "remarks": "",
                    "original_utterances": item.get('original_utterances', '')
                })
        if car_model_tags:
            tags['意向车型标签'] = car_model_tags

        budget_tags = []
        for item in extractions:
            if item['dimension'] == '预算区间' and item['is_match']:
                budget_tags.append({
                    "id": "1690",
                    "dimension": "预算与购车方式标签",
                    "is_match": True,
                    "value": f"预算区间：{item['value']}",
                    "remarks": "",
                    "original_utterances": item.get('original_utterances', '')
                })
        if budget_tags:
            tags['预算与购车方式标签'] = budget_tags

        customer_tags = []
        for item in extractions:
            if item['dimension'] == '客户类型' and item['is_match']:
                customer_tags.append({
                    "id": "1690",
                    "dimension": "客户基础标签",
                    "is_match": True,
                    "value": f"客户类型：{item['value']}",
                    "remarks": "",
                    "original_utterances": item.get('original_utterances', '')
                })
        if customer_tags:
            tags['客户基础标签'] = customer_tags

        competitor_tags = []
        for item in extractions:
            if item['dimension'] == '对比车型' and item['is_match']:
                competitor_tags.append({
                    "id": "1690",
                    "dimension": "竞品对比标签",
                    "is_match": True,
                    "value": f"客户提及竞品车型：{item['value']}",
                    "remarks": "",
                    "original_utterances": item.get('original_utterances', '')
                })
        if competitor_tags:
            tags['竞品对比标签'] = competitor_tags

        focus_tags = []
        for item in extractions:
            if item['dimension'] == '关注点' and item['is_match']:
                focus_tags.append({
                    "id": "1690",
                    "dimension": "核心需求标签",
                    "is_match": True,
                    "value": f"关注点：{item['value']}",
                    "remarks": "",
                    "original_utterances": item.get('original_utterances', '')
                })
        if focus_tags:
            tags['核心需求标签'] = focus_tags

        stage_tags = []
        for item in extractions:
            if item['dimension'] == '购车阶段' and item['is_match']:
                stage_tags.append({
                    "id": "1690",
                    "dimension": "购车决策信息标签",
                    "is_match": True,
                    "value": f"购车阶段：{item['value']}",
                    "remarks": "",
                    "original_utterances": item.get('original_utterances', '')
                })
        if stage_tags:
            tags['购车决策信息标签'] = stage_tags

        action_tags = []
        for item in extractions:
            if item['dimension'] == '体验动作' and item['is_match']:
                action_tags.append({
                    "id": "1690",
                    "dimension": "服务与行动标签",
                    "is_match": True,
                    "value": f"体验动作：{item['value']}",
                    "remarks": "",
                    "original_utterances": item.get('original_utterances', '')
                })
        if action_tags:
            tags['服务与行动标签'] = action_tags

        return tags

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
