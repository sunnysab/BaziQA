# 实验代码使用说明

本文档说明如何使用当前仓库中的实验代码，完成：

- 单次 `Multi-turn` / `Structured` 评测
- 多年份批量评测
- 多轮实验
- 断点续跑
- 中断恢复
- 结果汇总报告生成

## 1. 目录说明

实验代码主要入口：

- `acc_test/bazi_eval_multiturn.py`
  - 单数据集 `Multi-turn` 评测
- `acc_test/bazi_eval_structured.py`
  - 单数据集 `Structured` 评测
- `acc_test/run_benchmark.py`
  - 对 `contest8_2021.json` 到 `contest8_2025.json` 批量跑一个协议
- `scripts/run_all_experiments.sh`
  - 一次性跑多轮、多协议实验
- `acc_test/report_results.py`
  - 根据本地已有结果生成轻量汇总报告

结果目录：

- `result/bazi-results/`
  - 本地 `bazi.py` 生成的命盘缓存
- `result/evals/`
  - 单次评测结果、失败信息、轻量汇总
- `result/run1/`, `result/run2/`, `result/run3/`
  - 多轮实验输出
- `reports/`
  - 汇总报告

## 2. 环境准备

推荐使用仓库内虚拟环境：

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

本项目依赖本地排盘工具：

- `~/Code/0-Cloned/bazi/bazi.py`

代码会自动调用该脚本生成命盘缓存。

## 3. `.env` 配置

实验代码支持两套变量名，优先读取 `OPENAI_*`，缺失时回退到兼容别名。

推荐写法：

```bash
OPENAI_BASE_URL=http://your-gateway/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=openai/gpt-5.4|google/gemini-3.1-pro-preview
```

兼容写法：

```bash
URL=http://your-gateway/v1/chat/completion
KEY=your-key
MODEL=openai/gpt-5.4|google/gemini-3.1-pro-preview
```

说明：

- 多模型使用 `|` 分隔
- 代码会自动规范 `URL` 到 OpenAI chat completions 所需的标准接口路径
- 兼容部分网关返回的 SSE 文本流

## 4. 单次评测

### 4.1 Multi-turn

运行 2025 年数据，限制为 1 个命主：

```bash
.venv/bin/python acc_test/bazi_eval_multiturn.py data/contest8_2025.json --limit-subjects 1 --model openai/gpt-5.4
```

如果 `.env` 中有多个模型，也可以并发跑：

```bash
.venv/bin/python acc_test/bazi_eval_multiturn.py data/contest8_2025.json --limit-subjects 1 --max-workers 2
```

### 4.2 Structured

```bash
.venv/bin/python acc_test/bazi_eval_structured.py data/contest8_2025.json --limit-subjects 1 --model openai/gpt-5.4
```

## 5. 批量跑全年份

对 `contest8_2021` 到 `contest8_2025` 批量跑某一个协议：

```bash
.venv/bin/python acc_test/run_benchmark.py --protocol multiturn --model openai/gpt-5.4 --max-workers 2
.venv/bin/python acc_test/run_benchmark.py --protocol structured --model openai/gpt-5.4 --max-workers 2
```

参数说明：

- `--protocol`
  - `multiturn` 或 `structured`
- `--model`
  - 指定单模型；不传则读取 `.env` 中全部模型
- `--max-workers`
  - 并发数，只对“不同模型 / 不同年份任务”生效
- `--limit-subjects`
  - 只跑前 N 个命主，适合 smoke test
- `--output-root`
  - 指定输出目录
- `--resume` / `--no-resume`
  - 是否断点续跑，默认开启

## 6. 一次性跑所有实验

如果 `.env` 中已经配置了多个模型，直接运行：

```bash
RUNS=3 MAX_WORKERS=4 bash scripts/run_all_experiments.sh
```

如果只想临时限制到单个模型：

```bash
RUNS=3 MAX_WORKERS=4 bash scripts/run_all_experiments.sh --model openai/gpt-5.4
```

脚本行为：

- 外层按 `run1 -> run2 -> run3`
- 每轮依次跑：
  - `multiturn`
  - `structured`
- 每个 `run_benchmark.py` 内部对不同模型 / 不同年份任务并发执行

可配置环境变量：

- `RUNS`
  - 轮数，默认 `3`
- `MAX_WORKERS`
  - 并发数，默认 `4`
- `PROTOCOLS`
  - 默认 `"multiturn structured"`
- `CACHE_ROOT`
  - 命盘缓存目录，默认 `result`
- `OUTPUT_BASE`
  - 轮次输出目录根，默认 `result`
- `DATA_DIR`
  - 数据目录，默认 `data`
- `PYTHON_BIN`
  - Python 路径，默认 `.venv/bin/python`
- `DRY_RUN=1`
  - 仅打印命令矩阵，不实际执行

示例：

```bash
DRY_RUN=1 RUNS=2 MAX_WORKERS=4 bash scripts/run_all_experiments.sh --model openai/gpt-5.4
```

## 7. 断点续跑

`run_benchmark.py` 默认开启断点续跑。

规则：

- 如果当前 `output-root/evals/` 下已经有某个 `model + dataset` 的成功结果
- 再次运行时会自动跳过
- 终端会显示：

```text
SKIP	openai/gpt-5.4	contest8_2025.json	reason=existing_result
```

如果你想强制重跑：

```bash
.venv/bin/python acc_test/run_benchmark.py --protocol multiturn --no-resume
```

## 8. 错误处理与中断恢复

### 8.1 单数据集 CLI

当你同时跑多个模型时：

- 某个模型失败，不会拖垮其他模型
- 成功模型结果会保留
- 失败模型会生成错误文件：

```text
result/evals/failures/<model>_<protocol>_error.txt
```

### 8.2 批量 benchmark

当 `run_benchmark.py` 中某个 `model + year` 任务失败时：

- 已完成结果保留
- 失败详情写入：

```text
<output-root>/evals/failures_<protocol>.json
```

### 8.3 Ctrl+C

执行 `scripts/run_all_experiments.sh` 时按 `Ctrl+C`：

- 不会立刻把全部进度丢掉
- 脚本会在当前子任务结束后停止
- 已写出的结果、summary、failure report 都会保留

## 9. 生成轻量汇总报告

根据本地已有结果生成 markdown：

```bash
.venv/bin/python acc_test/report_results.py --root result
```

默认输出：

```text
reports/summary-YYYY-MM-DD.md
```

报告包含：

- 概览
- 按 `model + protocol` 的宏平均准确率
- 分年份准确率表
- 失败任务汇总

## 10. 推荐工作流

### 10.1 先做 smoke test

```bash
.venv/bin/python acc_test/bazi_eval_multiturn.py data/contest8_2025.json --limit-subjects 1 --model openai/gpt-5.4
.venv/bin/python acc_test/bazi_eval_structured.py data/contest8_2025.json --limit-subjects 1 --model openai/gpt-5.4
```

### 10.2 再跑全年份

```bash
.venv/bin/python acc_test/run_benchmark.py --protocol multiturn --model openai/gpt-5.4 --max-workers 2
.venv/bin/python acc_test/run_benchmark.py --protocol structured --model openai/gpt-5.4 --max-workers 2
```

### 10.3 最后跑多轮实验

```bash
RUNS=3 MAX_WORKERS=4 bash scripts/run_all_experiments.sh
```

### 10.4 生成报告

```bash
.venv/bin/python acc_test/report_results.py --root result
```

## 11. 当前已知限制

- 同一命主内部 5 道题必须串行，不支持并发
- 某些网关会偶发返回空 SSE chunk，代码已加入重试与错误隔离，但不能保证第三方服务完全稳定
- 当前结果文件是按任务落盘，不是逐题增量保存
