# Episode分析工具 - 精简版

## 🎯 功能

- 随机选取1个episode 或 指定episode ID
- 提取episode信息和instruction
- 可选：将instruction交给LLM分析

## 🚀 使用方法

```bash
# 随机选1个episode
./analyze.sh

# 随机选1个episode + LLM分析
./analyze.sh -a

# 指定episode ID: 123
./analyze.sh 123

# 指定episode + LLM分析
./analyze.sh 123 -a
```

## ✏️ 编辑提示词

**在 `analyze_episode.py` 文件的顶部（第18-29行）**：

```python
# ============================================================================
# 🔧 在这里编辑提示词
# ============================================================================

SYSTEM_PROMPT = """你是一个专业的视觉语言导航（VLN）任务分析专家。
请根据给定的导航指令，提供简洁但专业的分析。"""

USER_PROMPT_TEMPLATE = """请分析以下导航指令：

指令：{instruction}

请简要分析：
1. 任务目标
2. 关键地标
3. 需要执行的动作
"""

# ============================================================================
```

### 提示词说明

- **SYSTEM_PROMPT**：系统提示词，定义LLM的角色和行为
- **USER_PROMPT_TEMPLATE**：用户提示词模板，`{instruction}` 会被自动替换为实际指令

### 修改示例

想要更详细的分析？修改为：

```python
USER_PROMPT_TEMPLATE = """请详细分析以下导航指令：

指令：{instruction}

请从以下方面分析：
1. 任务目标是什么
2. 涉及哪些地标和物体
3. 需要执行的动作序列
4. 空间关系描述
5. 潜在的挑战
"""
```

## 📝 配置

确保 `api_config.yaml` 已配置API密钥：

```yaml
openrouter:
  api_key: "sk-or-v1-your-key"
  default_model: "qwen/qwen-2.5-72b-instruct"
  temperature: 0.7
  max_tokens: 1000
```

## 文件说明

- `analyze_episode.py` - 主程序（130行，包含提示词）
- `analyze.sh` - 简单脚本（30行）
- `api_config.yaml` - API配置

就这么简单！🎉
