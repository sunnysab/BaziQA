# 八字命理评估数据集 (BaZi Fortune-Telling Evaluation Dataset)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 数据集简介

本项目及相关论文知识成果现已应用于[AuraMate灵伴](https://auramate.net/)玄学陪伴产品。相关论文见[论文链接](https://arxiv.org/abs/2602.12889)。

本数据集是用于评估大型语言模型（LLM）在中国传统八字命理推理能力的基准测试集。数据集包含真实人物的出生信息（年月日时）、性别、出生地点，以及经过专家验证的命运事件问答题。

数据集分为两个部分：
1. **Contest8系列**（2021-2025年）：每年8位命主，每位命主5道选择题，共40题/年
2. **Celebrity50**：50位名人的详细命理信息和人生事件

## 📂 数据集结构

```
data/
├── README.md                    # 本文件
├── contest8_2021.json          # 2021年比赛数据（8人 × 5题 = 40题）
├── contest8_2022.json          # 2022年比赛数据（8人 × 5题 = 40题）
├── contest8_2023.json          # 2023年比赛数据（8人 × 5题 = 40题）
├── contest8_2024.json          # 2024年比赛数据（8人 × 5题 = 40题）
├── contest8_2025.json          # 2025年比赛数据（8人 × 5题 = 40题）
└── celebrity50_zh.json         # 50位名人数据集
```

## 📊 数据统计

| 数据集 | 命主数量 | 问题数量 | 年份 | 文件大小 |
|--------|----------|----------|------|----------|
| Contest8 2021 | 8 | 40 | 2021 | ~15KB |
| Contest8 2022 | 8 | 40 | 2022 | ~14KB |
| Contest8 2023 | 8 | 40 | 2023 | ~10KB |
| Contest8 2024 | 8 | 40 | 2024 | ~15KB |
| Contest8 2025 | 8 | 40 | 2025 | ~17KB |
| Celebrity50 | 50 | 250 | 多年 | ~220KB |
| **总计** | **90** | **450** | - | **~291KB** |

## 📋 数据格式

### Contest8 系列格式

每个Contest8文件包含：

```json
[
  {
    "contest_id": "contest8_2025",
    "current_year": "2025",
    "description": "本竞赛包含8位不同出生年月日时及性别的命主...",
    "total_questions": 40
  },
  {
    "person_id": "guangdong_female_19511114_P001",
    "name": "1951年广东出生女性",
    "profile": {
      "birth": {
        "year": 1951,
        "month": 11,
        "day": 14,
        "hour": 10,
        "minute": 0,
        "place": "广东，中国",
        "approximate": false
      },
      "gender": "female"
    },
    "categories": {
      "感情": [],
      "财富": [],
      "六亲": [],
      "事业": [],
      "健康": []
    },
    "questions": [
      {
        "question_id": "guangdong_female_19511114_P001-Q1",
        "question": "此命出生家境如何？",
        "options": [
          "A. 富裕",
          "B. 贫穷",
          "C. 父从商母是村干部",
          "D. 父母当官"
        ],
        "answer": "B"
      }
    ]
  }
]
```

### Celebrity50 格式

Celebrity50包含50位名人的详细信息：

```json
[
  {
    "person_id": "albert_ii_prince_of_monaco_P001",
    "name": "Albert II, Prince of Monaco",
    "profile": {
      "birth": {
        "year": 1958,
        "month": 3,
        "day": 14,
        "hour": 12,
        "minute": 0,
        "place": "Monaco, Monaco",
        "approximate": false
      },
      "gender": "male"
    },
    "categories": {
      "感情": ["详细的感情事件时间线..."],
      "财富": ["详细的财富事件时间线..."],
      "六亲": ["详细的家庭关系事件..."],
      "事业": ["详细的事业事件时间线..."],
      "健康": ["详细的健康事件..."]
    },
    "questions": [
      {
        "question_id": "albert_ii_prince_of_monaco_P001-Q1",
        "question": "此人在哪一年结婚？",
        "options": ["A. 2010", "B. 2011", "C. 2012", "D. 2013"],
        "answer": "B"
      }
    ]
  }
]
```

## 🔑 关键字段说明

### 命主信息（Person Profile）

- **person_id**: 唯一标识符，格式：`地区_性别_出生年月日_序号`
- **name**: 命主名称或描述
- **profile.birth**: 出生信息
  - `year`, `month`, `day`: 出生年月日
  - `hour`, `minute`: 出生时刻（24小时制）
  - `place`: 出生地点
  - `approximate`: 是否为估计时间（false表示精确）
- **profile.gender**: 性别（"male" / "female"）

### 问题信息（Questions）

- **question_id**: 唯一问题标识符
- **question**: 问题文本（中文）
- **options**: 选项列表（A/B/C/D）
- **answer**: 正确答案（字母）

### 事件分类（Categories）

问题按以下五大类别组织：

1. **感情**：婚姻、恋爱、情感关系
2. **财富**：经济状况、财运、投资
3. **六亲**：父母、兄弟姐妹、子女关系
4. **事业**：职业发展、工作变动
5. **健康**：身体状况、疾病、意外

## 💡 使用示例

### Python 读取数据

```python
import json

# 读取Contest8数据
with open('contest8_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 获取比赛元信息
contest_info = data[0]
print(f"比赛ID: {contest_info['contest_id']}")
print(f"总题数: {contest_info['total_questions']}")

# 遍历每个命主
for person in data[1:]:
    print(f"\n命主: {person['name']}")
    print(f"出生: {person['profile']['birth']['year']}年{person['profile']['birth']['month']}月{person['profile']['birth']['day']}日")
    
    # 遍历问题
    for q in person['questions']:
        print(f"  问题: {q['question']}")
        print(f"  答案: {q['answer']}")
```

### 评估示例

```python
def evaluate_model(model_answers, ground_truth):
    """
    评估模型准确率
    
    Args:
        model_answers: dict, {question_id: answer}
        ground_truth: dict, {question_id: correct_answer}
    
    Returns:
        accuracy: float
    """
    correct = 0
    total = len(ground_truth)
    
    for qid, correct_answer in ground_truth.items():
        if model_answers.get(qid) == correct_answer:
            correct += 1
    
    return correct / total if total > 0 else 0.0

# 使用示例
ground_truth = {}
for person in data[1:]:
    for q in person['questions']:
        ground_truth[q['question_id']] = q['answer']

# 假设模型给出答案
model_answers = {
    "guangdong_female_19511114_P001-Q1": "B",
    # ... 更多答案
}

accuracy = evaluate_model(model_answers, ground_truth)
print(f"准确率: {accuracy:.2%}")
```

## 📈 基准性能

使用本数据集评估的模型性能（Contest8 2021-2025平均，不去除极值）：

| 模型 | 方法 | 平均准确率 |
|------|------|-----------|
| DeepSeek-Chat-v3 | Multi-turn | 36.70% |
| DeepSeek-Chat-v3 | Structured | 38.00% |
| DeepSeek-R1 | Multi-turn | 34.10% |
| DeepSeek-R1 | Structured | 35.00% |
| GPT-5.1-Chat | Multi-turn | 32.50% |
| Gemini-3-Pro | Multi-turn | 32.10% |
| Gemini-2.5-Flash | Multi-turn | 32.40% |
| OpenAI GPT-5.4 | Multi-turn | 30.83% |
| OpenAI GPT-5.4 | Structured | 31.33% |
| Gemini-3.1-Pro-Preview | Multi-turn | 38.33% |
| Gemini-3.1-Pro-Preview | Structured | 33.33% |

*注：DeepSeek / GPT-5.1 / Gemini-3-Pro / Gemini-2.5-Flash 为论文报告结果；OpenAI GPT-5.4 与 Gemini-3.1-Pro-Preview 为当前仓库本地三轮复现均值（`result/run1`–`result/run3`）。详细评估方法和结果请参考相关论文与仓库内结果文件。*

## 🧪 严格复现评测

当前仓库已补充一套面向 Contest8 的严格复现评测脚本，评测流程为：

1. 读取 `data/contest8_*.json`
2. 调用本地 `~/Code/0-Cloned/bazi/bazi.py` 生成命盘文本
3. 将命盘作为固定上下文输入模型
4. 以 `Multi-turn` 或 `Structured` 协议逐题评测
5. 输出逐题结果与准确率到 `result/evals/`

### 依赖安装

建议在仓库内创建虚拟环境：

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### `.env` 配置

脚本支持两套键名，优先读取 `OPENAI_*`，缺失时回退到兼容别名：

```bash
OPENAI_BASE_URL=http://your-gateway/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5.4|google/gemini-3.1-pro-preview
```

或：

```bash
URL=http://your-gateway/v1/chat/completion
KEY=your-key
MODEL=gpt-5.4|google/gemini-3.1-pro-preview
```

说明：

- `OPENAI_MODEL` / `MODEL` 支持用 `|` 分隔多个模型，脚本会逐个评测。
- 若 `URL` 直接填网关首页或单聊天接口，脚本会自动规范到标准 OpenAI chat completions 路径。
- 本地 `bazi.py` 依赖 `bidict`、`colorama`、`lunar_python`，已包含在 `requirements.txt`。

### 运行 Multi-turn

```bash
.venv/bin/python acc_test/bazi_eval_multiturn.py data/contest8_2025.json --limit-subjects 1 --model gpt-5.4
```

多模型并发：

```bash
.venv/bin/python acc_test/bazi_eval_multiturn.py data/contest8_2025.json --limit-subjects 1 --max-workers 2
```

### 运行 Structured

```bash
.venv/bin/python acc_test/bazi_eval_structured.py data/contest8_2025.json --limit-subjects 1 --model gpt-5.4
```

### 批量跑 Contest8 全年份

```bash
.venv/bin/python acc_test/run_benchmark.py --protocol multiturn --model gpt-5.4 --max-workers 2
.venv/bin/python acc_test/run_benchmark.py --protocol structured --model gpt-5.4 --max-workers 2
```

默认会自动断点续跑，跳过当前 `output-root` 下已经存在的成功结果。若需要强制重跑，可显式关闭：

```bash
.venv/bin/python acc_test/run_benchmark.py --protocol multiturn --no-resume
```

### 一次性跑所有实验

如果 `.env` 中已经配置了两个模型，可以直接用：

```bash
RUNS=3 MAX_WORKERS=4 bash scripts/run_all_experiments.sh
```

如果只想临时限制到某个模型：

```bash
RUNS=3 MAX_WORKERS=4 bash scripts/run_all_experiments.sh --model gpt-5.4
```

### 生成轻量汇总报告

基于本地已保存的结果文件生成 markdown 汇总：

```bash
.venv/bin/python acc_test/report_results.py --root result
```

默认输出到：

```text
reports/summary-YYYY-MM-DD.md
```

说明：

- `--max-workers` 只会并发“不同模型 / 不同年份”的任务。
- 同一命主内部 5 道题仍保持串行，以保证 multi-turn 会话语义不被破坏。
- 如果某个模型/年份任务失败，已完成的结果文件会保留，失败详情会写入 `failures_<protocol>.json`。
- `scripts/run_all_experiments.sh` 遇到单个任务失败时不会中断后续轮次，会在全部任务结束后以非零状态退出。
- `run_benchmark.py` 默认开启断点续跑，已有成功结果会显示为 `SKIP ... reason=existing_result`。
- 在 `run_all_experiments.sh` 执行时按 `Ctrl+C`，脚本会在当前子任务结束后停止，并保留已经完成的结果与汇总。

结果会写入：

```text
result/bazi-results/
result/evals/<model>/<protocol>/
result/evals/summary_<protocol>.md
result/evals/failures_<protocol>.json
```

## 🎯 数据集特点

### ✅ 优势

1. **真实性**：所有命主为真实人物，事件经过验证
2. **标准化**：统一的JSON格式，易于解析和处理
3. **多样性**：涵盖不同年代、性别、地区的命主
4. **专业性**：问题由专业命理师设计和审核
5. **可重复**：固定的测试集，便于模型对比

### ⚠️ 局限性

1. 样本量有限（90人，450题）
2. 主要为中文语境，可能存在文化特异性
3. 选择题格式，可能无法全面评估推理能力
4. 缺少推理过程的标注

## 🔬 研究用途

本数据集适用于以下研究方向：

- 大型语言模型的领域知识评估
- 传统文化知识的AI理解能力
- 多步推理和因果推理能力测试
- 中文自然语言理解
- Few-shot学习和In-context学习

## 📄 引用

如果您在研究中使用了本数据集，请引用：

```bibtex
@dataset{bazi_QA,
  title={BaZi Fortune-Telling QA Dataset},
  author={Jiangxi Chen},
  year={2025},
  publisher={GitHub},
  url={https://github.com/ChenJiangxi/BaziQA}
}
```

## 📜 许可证

本数据集采用 **MIT License** 开源协议。

您可以自由地：
- ✅ 使用：用于商业或非商业目的
- ✅ 修改：改编和修改数据集
- ✅ 分发：分享给他人
- ✅ 私用：用于私人项目

但需要：
- ⚠️ 保留版权声明和许可证声明
- ⚠️ 声明是否进行了修改

详见 [LICENSE](../LICENSE) 文件。

## ⚠️ 免责声明

1. **科研用途**：本数据集仅用于学术研究和AI评估，不构成任何形式的命理建议。
2. **隐私保护**：名人信息来自公开资料，其他命主已进行匿名化处理。
3. **文化尊重**：八字命理为中国传统文化的一部分，使用时请尊重文化传统。
4. **结果解释**：AI模型的预测结果不应被视为专业的命理咨询。

## 🤝 贡献

欢迎贡献！如果您发现数据错误或有改进建议，请：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

或直接在 [Issues](https://github.com/Chenjiangxi/BaziQA/issues) 页面报告问题。

## 📧 联系方式

如有疑问或建议，请通过以下方式联系：

- **GitHub Issues**: [提交Issue](https://github.com/Chenjiangxi/BaziQA/issues)

## 🔗 相关资源

- [AuraMate灵伴 项目主页](https://auramate.net/)
- [论文链接](https://arxiv.org/abs/2602.12889)

## 📊 更新日志

### v1.0.0 (2025-02)
- 🎉 初始发布
- ✅ 包含Contest8 2021-2025数据（40题/年 × 5年 = 200题）
- ✅ 包含Celebrity50数据集（50人 × 5题 = 250题）
- ✅ 提供完整的元数据和文档

---

**最后更新**: 2025年2月13日
