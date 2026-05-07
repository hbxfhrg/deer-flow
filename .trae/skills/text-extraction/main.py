#!/usr/bin/env python3
"""
销售对话文本提取工具 - LLM提取 + Skill后处理
用于 deer-flow 工作流中，对LLM提取结果进行后处理
"""

import sys
import json
from text_extractor import SalesTextPostProcessor


def main():
    if len(sys.argv) > 1:
        llm_result = sys.argv[1]
    else:
        llm_result = sys.stdin.read()

    processor = SalesTextPostProcessor()
    result = processor.process(llm_result)
    print(processor.format_output(result))


if __name__ == "__main__":
    main()
