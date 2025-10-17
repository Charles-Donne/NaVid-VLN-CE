# Episode Instruction 分析工具

使用Qwen大模型分析VLN-CE数据集中的导航指令。

## 快速开始

### 1. 安装依赖
```bash
pip install pyyaml requests
```

### 2. 配置API密钥（可选，如需AI分析）

编辑 `api_config.yaml` 文件：
```yaml
openrouter:
  api_key: "sk-or-v1-your-key-here"  # 替换为你的密钥
```

### 3. 使用

```bash
# 打印5个episodes（默认）
./print_instructions.sh

# 打印10个episodes
./print_instructions.sh 10

# 打印并AI分析（需要配置api_config.yaml）
./print_instructions.sh 5 -a
```

## 就这么简单！

- 第一个参数：打印多少个episodes（默认5）
- `-a`：启用AI分析
- `-h`：查看帮助

## API密钥

从 https://openrouter.ai/keys 获取密钥，然后编辑 `api_config.yaml`

## 文件说明

- `print_episode_instructions.py` - 主程序
- `print_instructions.sh` - 简单脚本
- `api_config.yaml` - API配置
- `setup_api_key.sh` - 配置向导（可选）
