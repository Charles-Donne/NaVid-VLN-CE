#!/bin/bash

# 打印Episode Instructions脚本 - 简化版

# 默认配置
DEFAULT_CONFIG="VLN_CE/vlnce_baselines/config/r2r_baselines/navid_r2r.yaml"
NUM_EPISODES=${1:-5}  # 第一个参数是数量，默认5个

# 使用说明
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "用法: $0 [数量] [-a]"
    echo ""
    echo "  数量     打印多少个episodes（默认5）"
    echo "  -a       启用AI分析（需要配置api_config.yaml）"
    echo ""
    echo "示例:"
    echo "  $0           # 打印5个episodes"
    echo "  $0 10        # 打印10个episodes"
    echo "  $0 5 -a      # 打印5个episodes并分析"
    exit 0
fi

# 检查是否需要分析
ANALYZE=""
if [[ "$2" == "-a" ]] || [[ "$1" == "-a" ]]; then
    ANALYZE="--analyze"
    if [[ "$1" == "-a" ]]; then
        NUM_EPISODES=5
    fi
fi

# 运行Python程序
python print_episode_instructions.py \
    --config "$DEFAULT_CONFIG" \
    --max-episodes "$NUM_EPISODES" \
    $ANALYZE
