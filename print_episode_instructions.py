#!/usr/bin/env python3
"""
打印Episode Instruction工具
用于查看VLN-CE数据集中指定episode的导航指令
并使用Qwen大模型进行指令分析
"""

import argparse
import os
import json
import requests
import yaml
from datetime import datetime
from pathlib import Path
from habitat.datasets import make_dataset
from VLN_CE.vlnce_baselines.config.default import get_config


def load_api_config(config_path="api_config.yaml"):
    """
    加载API配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典，如果文件不存在则返回默认配置
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            print(f"⚠️  警告：无法读取配置文件 {config_path}: {e}")
            print("使用默认配置和环境变量")
    
    # 返回默认配置
    return {
        'openrouter': {
            'api_key': os.environ.get('OPENROUTER_API_KEY', ''),
            'base_url': 'https://openrouter.ai/api/v1/chat/completions',
            'default_model': 'qwen/qwen-2.5-72b-instruct',
            'timeout': 30,
            'max_retries': 3
        },
        'output': {
            'default_output_file': 'instruction_analysis_results.json',
            'output_dir': 'analysis_results',
            'use_timestamp': True
        }
    }


def analyze_instruction_with_qwen(instruction_text, api_key=None, model=None, api_config=None):
    """
    使用Qwen大模型通过OpenRouter API分析导航指令
    
    Args:
        instruction_text: 导航指令文本
        api_key: OpenRouter API密钥（如果为None则从配置文件读取）
        model: 使用的模型名称（如果为None则从配置文件读取）
        api_config: API配置字典
        
    Returns:
        分析结果字符串，如果失败返回错误信息
    """
    # 如果没有提供配置，加载默认配置
    if api_config is None:
        api_config = load_api_config()
    
    # 获取API配置
    openrouter_config = api_config.get('openrouter', {})
    
    # 确定API密钥（优先级：参数 > 配置文件 > 环境变量）
    if api_key is None:
        api_key = openrouter_config.get('api_key') or os.environ.get('OPENROUTER_API_KEY')
    
    # 确定模型（优先级：参数 > 配置文件）
    if model is None:
        model = openrouter_config.get('default_model', 'qwen/qwen-2.5-72b-instruct')
    
    # 获取URL和超时设置
    url = openrouter_config.get('base_url', 'https://openrouter.ai/api/v1/chat/completions')
    timeout = openrouter_config.get('timeout', 30)
    
    # 构建分析提示词
    analysis_prompt = f"""请分析以下视觉语言导航（VLN）指令，提供详细的分析：

导航指令："{instruction_text}"

请从以下几个方面进行分析：
1. **任务类型**：这是什么类型的导航任务？（如：目标导航、房间切换、物体寻找等）
2. **关键地标**：指令中提到了哪些重要的地标或物体？
3. **动作序列**：需要执行哪些主要动作？（如：前进、转向、进入房间等）
4. **空间关系**：涉及哪些空间关系描述？（如：左边、右边、前方、后方等）
5. **难度评估**：这个指令的复杂度如何？（简单/中等/困难）
6. **潜在挑战**：执行这个指令可能遇到什么困难？

请用中文回答，格式清晰。"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": analysis_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        analysis = result['choices'][0]['message']['content']
        return analysis
        
    except requests.exceptions.RequestException as e:
        return f"❌ API调用失败: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"❌ 解析响应失败: {str(e)}"
    except Exception as e:
        return f"❌ 未知错误: {str(e)}"


def print_episode_instructions(config_path, episode_ids=None, max_episodes=10, 
                               analyze=False, api_key=None, model=None,
                               save_analysis=False, output_file=None, api_config_path="api_config.yaml"):
    """
    打印指定episode的instruction并可选地使用大模型分析
    
    Args:
        config_path: VLN-CE配置文件路径
        episode_ids: 要打印的episode ID列表（如果为None则打印前max_episodes个）
        max_episodes: 当episode_ids为None时，打印的最大episode数量
        analyze: 是否使用大模型分析指令
        api_key: OpenRouter API密钥（可选，优先从配置文件读取）
        model: 使用的Qwen模型（可选，优先从配置文件读取）
        save_analysis: 是否保存分析结果到文件
        output_file: 输出文件路径（可选，可从配置文件读取）
        api_config_path: API配置文件路径
    """
    # 加载API配置
    api_config = load_api_config(api_config_path)
    
    # 如果需要分析，验证API密钥
    if analyze:
        # 从配置文件或环境变量获取API密钥
        effective_api_key = api_key or api_config.get('openrouter', {}).get('api_key') or os.environ.get('OPENROUTER_API_KEY')
        
        if not effective_api_key or effective_api_key == 'your_api_key_here':
            print("❌ 错误：需要分析但未提供有效的API密钥！")
            print("\n请通过以下任一方式配置API密钥：")
            print("  1. 编辑 api_config.yaml 文件，设置 openrouter.api_key")
            print("  2. 设置环境变量: export OPENROUTER_API_KEY=your_key")
            print("  3. 使用命令行参数: --api-key your_key")
            print("  4. 运行配置向导: ./setup_api_key.sh")
            return
        
        # 使用有效的API密钥
        api_key = effective_api_key
    
    # 获取输出配置
    output_config = api_config.get('output', {})
    
    # 加载配置
    config = get_config(config_path)
    
    # 创建数据集
    dataset = make_dataset(
        id_dataset=config.TASK_CONFIG.DATASET.TYPE, 
        config=config.TASK_CONFIG.DATASET
    )
    
    # 按episode ID排序
    dataset.episodes.sort(key=lambda ep: ep.episode_id)
    
    print(f"数据集总共包含 {len(dataset.episodes)} 个episodes\n")
    print("=" * 80)
    
    # 如果指定了episode_ids，只打印这些episode
    if episode_ids:
        episodes_to_print = [ep for ep in dataset.episodes if str(ep.episode_id) in episode_ids]
        if not episodes_to_print:
            print(f"警告：未找到指定的episode ID: {episode_ids}")
            return
    else:
        # 否则打印前max_episodes个
        episodes_to_print = dataset.episodes[:max_episodes]
    
    # 用于保存分析结果
    all_analysis_results = []
    
    # 打印每个episode的信息
    for idx, episode in enumerate(episodes_to_print, 1):
        print(f"\n{'='*80}")
        print(f"Episode #{idx}/{len(episodes_to_print)}")
        print(f"{'='*80}")
        print(f"📋 Episode ID: {episode.episode_id}")
        print(f"🏠 Scene ID: {episode.scene_id}")
        
        # 获取instruction文本
        instruction_text = None
        
        # 打印instruction（不同数据集可能有不同的属性名）
        if hasattr(episode, 'instruction'):
            if hasattr(episode.instruction, 'instruction_text'):
                instruction_text = episode.instruction.instruction_text
                print(f"📝 Instruction: {instruction_text}")
            else:
                instruction_text = str(episode.instruction)
                print(f"📝 Instruction: {instruction_text}")
        elif hasattr(episode, 'goals'):
            instruction_text = str(episode.goals)
            print(f"🎯 Goals: {instruction_text}")
        else:
            print("📝 Instruction: N/A")
        
        # 打印起始位置和朝向
        if hasattr(episode, 'start_position'):
            print(f"📍 Start Position: {episode.start_position}")
        if hasattr(episode, 'start_rotation'):
            print(f"🧭 Start Rotation: {episode.start_rotation}")
        
        # 使用大模型分析指令
        if analyze and instruction_text:
            print(f"\n{'─'*80}")
            
            # 显示使用的模型
            effective_model = model or api_config.get('openrouter', {}).get('default_model', 'qwen/qwen-2.5-72b-instruct')
            print(f"🤖 Qwen大模型分析中... (使用模型: {effective_model})")
            print(f"{'─'*80}")
            
            analysis = analyze_instruction_with_qwen(instruction_text, api_key, model, api_config)
            print(analysis)
            
            # 保存分析结果
            if save_analysis:
                all_analysis_results.append({
                    "episode_id": episode.episode_id,
                    "scene_id": episode.scene_id,
                    "instruction": instruction_text,
                    "analysis": analysis
                })
        
        print(f"{'='*80}")
    
    print(f"\n✅ 总共打印了 {len(episodes_to_print)} 个episodes的信息")
    
    # 保存分析结果到文件
    if save_analysis and all_analysis_results:
        # 确定输出文件路径
        if not output_file:
            output_file = output_config.get('default_output_file', 'instruction_analysis_results.json')
            
            # 如果配置要求使用时间戳
            if output_config.get('use_timestamp', False):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(output_file)
                output_file = f"{name}_{timestamp}{ext}"
        
        # 创建输出目录
        output_dir = output_config.get('output_dir', 'analysis_results')
        os.makedirs(output_dir, exist_ok=True)
        
        # 完整输出路径
        full_output_path = os.path.join(output_dir, output_file)
        
        with open(full_output_path, 'w', encoding='utf-8') as f:
            json.dump(all_analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 分析结果已保存到: {full_output_path}")


def main():
    """主函数：解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="打印VLN-CE数据集中episode的instruction并可选地使用Qwen大模型分析"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="配置文件路径（YAML格式）"
    )
    
    parser.add_argument(
        "--episode-ids",
        type=str,
        nargs="+",
        default=None,
        help="要打印的episode ID列表（空格分隔），例如：--episode-ids 123 456 789"
    )
    
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=10,
        help="当未指定episode-ids时，打印的最大episode数量（默认：10）"
    )
    
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="使用Qwen大模型分析导航指令"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenRouter API密钥（也可通过环境变量OPENROUTER_API_KEY设置）"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="使用的Qwen模型（如不指定则从api_config.yaml读取）\n"
             "可选：qwen/qwen-2.5-72b-instruct, qwen/qwen-2-72b-instruct, qwen/qwen-2.5-7b-instruct 等"
    )
    
    parser.add_argument(
        "--save-analysis",
        action="store_true",
        help="将分析结果保存到JSON文件"
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="分析结果输出文件路径（如不指定则从api_config.yaml读取）"
    )
    
    parser.add_argument(
        "--api-config",
        type=str,
        default="api_config.yaml",
        help="API配置文件路径（默认：api_config.yaml）"
    )
    
    args = parser.parse_args()
    
    # 执行打印和分析
    print_episode_instructions(
        config_path=args.config,
        episode_ids=args.episode_ids,
        max_episodes=args.max_episodes,
        analyze=args.analyze,
        api_key=args.api_key,
        model=args.model,
        save_analysis=args.save_analysis,
        output_file=args.output_file,
        api_config_path=args.api_config
    )


if __name__ == "__main__":
    main()
