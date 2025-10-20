#!/usr/bin/env python3
"""
Navigation Instruction Decomposition Pipeline
导航指令分解分析工具
"""

import os
import sys
import json
import yaml
import requests
from typing import Dict, List, Any

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)


# ============================================================================
# 🔧 系统提示词配置
# ============================================================================

SYSTEM_PROMPT = """You are a Language Decomposer for an embodied navigation system.  
Your task is to break a natural language navigation instruction into multiple structured sub-instructions.  
Each sub-instruction must describe one atomic spatial or semantic action, aligned with visual landmarks.  

Output strictly in JSON format following this schema:

{
  "instruction_original": "<the original instruction>",
  "sub_instructions": [
    {
      "sub_id": <int>,
      "sub_instruction": "<short, clear action phrase>",
      "action_type": "<one of: move_forward | turn | enter | exit | stop | look | approach | navigate>",
      "target_landmark": "<main object or area mentioned>",
      "spatial_relation": "<relation phrase if any, e.g. past / before / through / toward>",
      "scene_transition": "<if environment changes, describe it>",
      "completion_condition": "<how to determine this subtask is completed>"
    }
  ]
}

IMPORTANT:
- Return ONLY valid JSON, no markdown, no extra text
- Each sub-instruction must be atomic (one single action)
- sub_id starts from 1
- action_type must be one of the specified types
"""

USER_PROMPT_TEMPLATE = """Please decompose the following navigation instruction:

Instruction: {instruction}

Return the structured decomposition in JSON format."""

# ============================================================================


def load_config() -> Dict[str, Any]:
    """加载API配置"""
    config_path = os.path.join(project_root, 'llm_api', 'api_config.yaml')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"找不到配置文件: {config_path}\n"
            f"请在 llm_api/ 目录创建 api_config.yaml 文件"
        )
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def decompose_instruction(instruction: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    分解导航指令为结构化的子指令
    
    Args:
        instruction: 原始导航指令
        config: API配置字典
        
    Returns:
        包含分解结果的字典，格式如下：
        {
            "instruction_original": str,
            "sub_instructions": [
                {
                    "sub_id": int,
                    "sub_instruction": str,
                    "action_type": str,
                    "target_landmark": str,
                    "spatial_relation": str,
                    "scene_transition": str,
                    "completion_condition": str
                }
            ]
        }
    """
    api_key = config['openrouter']['api_key']
    model = config['openrouter']['default_model']
    
    # 构建提示词
    user_prompt = USER_PROMPT_TEMPLATE.format(instruction=instruction)
    
    # 调用API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": config['openrouter'].get('temperature', 0.3),
        "max_tokens": config['openrouter'].get('max_tokens', 2000),
        "response_format": {"type": "json_object"}  # 强制返回JSON
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=config['openrouter'].get('timeout', 30)
    )
    
    response.raise_for_status()
    result = response.json()
    
    # 解析返回的JSON
    llm_output = result['choices'][0]['message']['content']
    
    try:
        decomposition = json.loads(llm_output)
        return decomposition
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM返回的不是有效的JSON: {llm_output}") from e


def print_decomposition(decomposition: Dict[str, Any], detailed: bool = True):
    """
    打印分解结果
    
    Args:
        decomposition: 分解结果字典
        detailed: 是否显示详细信息
    """
    print("="*80)
    print("📋 指令分解结果")
    print("="*80)
    print(f"\n原始指令: {decomposition['instruction_original']}")
    print(f"\n共分解为 {len(decomposition['sub_instructions'])} 个子指令:\n")
    
    for sub in decomposition['sub_instructions']:
        print(f"[子指令 {sub['sub_id']}]")
        print(f"  ▸ 动作: {sub['sub_instruction']}")
        
        if detailed:
            print(f"  ▸ 类型: {sub['action_type']}")
            print(f"  ▸ 目标地标: {sub['target_landmark']}")
            if sub.get('spatial_relation'):
                print(f"  ▸ 空间关系: {sub['spatial_relation']}")
            if sub.get('scene_transition'):
                print(f"  ▸ 场景转换: {sub['scene_transition']}")
            print(f"  ▸ 完成条件: {sub['completion_condition']}")
        
        print()
    
    print("="*80)


def save_decomposition(decomposition: Dict[str, Any], output_path: str):
    """
    保存分解结果到JSON文件
    
    Args:
        decomposition: 分解结果字典
        output_path: 输出文件路径
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(decomposition, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 结果已保存到: {output_path}")


def main():
    """主函数：演示如何使用指令分解功能"""
    import argparse
    
    parser = argparse.ArgumentParser(description='导航指令分解工具')
    parser.add_argument('instruction', nargs='?', 
                       help='要分解的导航指令（如果不提供则使用示例）')
    parser.add_argument('--output', '-o', 
                       help='保存结果的JSON文件路径')
    parser.add_argument('--simple', '-s', action='store_true',
                       help='简化输出（不显示详细信息）')
    
    args = parser.parse_args()
    
    # 使用示例指令或用户提供的指令
    if args.instruction:
        instruction = args.instruction
    else:
        instruction = "Walk across the room toward the bedroom. Stop just inside the doorway."
        print(f"📝 使用示例指令: {instruction}\n")
    
    try:
        # 加载配置
        print("加载API配置...")
        config = load_config()
        
        # 分解指令
        print("🤖 正在分解指令...\n")
        decomposition = decompose_instruction(instruction, config)
        
        # 打印结果
        print_decomposition(decomposition, detailed=not args.simple)
        
        # 保存结果（如果指定了输出路径）
        if args.output:
            save_decomposition(decomposition, args.output)
        
        return decomposition
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
