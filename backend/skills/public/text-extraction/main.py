#!/usr/bin/env python3
"""
销售对话文本提取工具 - LLM提取 + Skill后处理
用于 deer-flow 工作流中，对LLM提取结果进行后处理

使用方式:
    python main.py <llm_result_json> [--segment-threshold <value>]
    echo <llm_result_json> | python main.py [--segment-threshold <value>]
    
参数:
    --segment-threshold: 分段处理阈值，超过此长度自动分段（默认1500）
"""

import sys
import json
import argparse
from text_extractor import SalesTextPostProcessor


def main():
    parser = argparse.ArgumentParser(description='销售对话文本提取工具')
    parser.add_argument('llm_result', nargs='?', default=None, help='LLM提取结果JSON')
    parser.add_argument('--segment-threshold', type=int, default=None, 
                        help='分段处理阈值（默认1500字符）')
    
    args = parser.parse_args()
    
    # 获取输入数据
    if args.llm_result:
        llm_result = args.llm_result
    else:
        llm_result = sys.stdin.read()
    
    # 构建配置参数
    kwargs = {}
    if args.segment_threshold is not None:
        kwargs['segment_threshold'] = args.segment_threshold

    processor = SalesTextPostProcessor(**kwargs)
    result = processor.process(llm_result)
    print(processor.format_output(result))


if __name__ == "__main__":
    main()
