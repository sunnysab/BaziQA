# BaziQA Strict Reproduction Design

**Date:** 2026-03-28

**Goal:** Reconstruct the missing evaluation code required to reproduce the public BaziQA paper setup for Contest8 datasets, using locally generated natal chart context and an OpenAI-compatible API.

## Scope

This design covers the first implementation target only:

- Strict reproduction of the paper-style evaluation workflow for `data/contest8_2021.json` through `data/contest8_2025.json`
- Local chart generation via `/home/sunnysab/Code/0-Cloned/bazi/bazi.py`
- Two inference protocols:
  - `Multi-turn`
  - `Structured`
- Model access through `.env` with OpenAI-compatible API settings
- Support for multiple models via `OPENAI_MODEL=model_a|model_b|...`
- Per-question results and aggregate accuracy output

This design does not cover:

- Final analysis plots or report reproduction
- External charting services
- Celebrity50-specific evaluation logic
- Fine-tuning, retrieval, or ensemble methods

## Constraints

The implementation must satisfy these hard constraints:

1. The model must not infer charts from raw birth data directly during evaluation.
2. Chart context must be generated locally before inference.
3. Each subject keeps a single conversation across its 5 associated questions.
4. `Structured` must remain an inference-time prompting scaffold, not a training or retrieval method.
5. The code must remain vendor-neutral for OpenAI-compatible APIs.

## Current Repository Reality

The current repository contains:

- Contest8 question files under `data/`
- documentation describing missing evaluation scripts
- no `acc_test/` implementation
- no published `result/bazi-results/*.json`

The current repository does not contain the structured natal-chart result files referenced in `dataset_and_input_format.md`. Therefore, the implementation must generate those files locally.

## Reproduction Policy

This work is a faithful reconstruction, not a claim of byte-for-byte recovery of the authors' internal prompts or scripts.

The public paper and docs reveal:

- evaluation protocol
- multi-turn session behavior
- structured reasoning step order
- expected chart-context concept

The public materials do not reveal:

- exact production prompts
- exact code for chart formatting
- exact parser logic used by the authors

Therefore, the implementation will preserve method semantics while documenting reconstructed prompt templates explicitly in code.

## Architecture

The implementation will add an `acc_test/` package with focused modules:

- `acc_test/bazi_eval_multiturn.py`
  - CLI entrypoint for multi-turn evaluation
- `acc_test/bazi_eval_structured.py`
  - CLI entrypoint for structured evaluation
- `acc_test/core/dataset.py`
  - normalize Contest8 data files
- `acc_test/core/bazi_provider.py`
  - call local `bazi.py`, capture output, create cache files
- `acc_test/core/formatter.py`
  - convert generated chart data into fixed model-facing text
- `acc_test/core/llm_client.py`
  - OpenAI-compatible chat client using `.env`
- `acc_test/core/protocols.py`
  - prompt templates for multi-turn and structured modes
- `acc_test/core/parser.py`
  - extract final multiple-choice answer from model output
- `acc_test/core/evaluator.py`
  - run sessions, score answers, write result files

Output directories:

- `result/bazi-results/`
  - generated local chart cache
- `result/evals/<model>/<protocol>/`
  - per-run evaluation output

## Data Flow

For each Contest8 dataset:

1. Load the JSON file.
2. Ignore the metadata row and normalize subject entries.
3. For each subject:
   - read birth data
   - determine gender flag
   - run local `bazi.py`
   - capture raw chart text
   - build a normalized cache record
   - render fixed chart context text
4. Start one conversation for that subject.
5. Ask the 5 questions sequentially in the same conversation.
6. Parse final answer letter.
7. Compare against gold answer.
8. Write detailed JSON results and summary metrics.

## Chart Generation Design

### Input

Source fields:

- `profile.birth.year`
- `profile.birth.month`
- `profile.birth.day`
- `profile.birth.hour`
- `profile.birth.minute`
- `profile.birth.place`
- `profile.gender`

### Local Provider

The implementation will call:

- `/home/sunnysab/Code/0-Cloned/bazi/bazi.py`

Expected invocation shape:

- Gregorian mode via `-g`
- add `-n` for female subjects
- use hour only, as required by the local script interface

### Cache Record

Each generated record will contain:

- `person_id`
- `name`
- `birth_input`
- `generator`
- `generated_at`
- `raw_output`
- `formatted_text`

The initial version will preserve the raw `bazi.py` output verbatim for auditability, and derive a stable formatted context from it without discarding the raw text.

## Model-Facing Context Format

The model context will follow a fixed textual template. It will not expose the original subject name directly when anonymization is enabled.

The formatted context will include:

- anonymous subject id
- gender
- source birth record
- generated chart summary
- original `bazi.py` chart body

Rationale:

- strict reproduction requires chart-first evaluation
- the public docs describe fixed chart context, but the exact formatter is unavailable
- keeping a stable wrapper plus the full local chart output preserves reproducibility and debugging visibility

## Protocol Design

### Multi-turn

Behavior:

- one system prompt per subject session
- one initial user message containing the fixed chart context
- five follow-up user messages, one per question
- conversation history retained across all five questions
- no correctness feedback after any question

Answer contract:

- the model may explain briefly
- the final line must be `最终答案：<LETTER>`

### Structured

Behavior:

- same subject session structure as multi-turn
- each question prompt explicitly forces three ordered reasoning stages

Required stages:

1. `量化扫描`
   - assess day-master strength, five-element balance, and global pattern
2. `冲突定级`
   - identify dominant interactions relevant to the target event and current temporal context
3. `应象映射`
   - map the dominant symbolic signals to the provided answer choices

Answer contract:

- the final line must be `最终答案：<LETTER>`

Structured is explicitly an inference-time scaffold only.

## Prompting Policy

Prompt templates will be concise and deterministic:

- no chain-of-thought exposure requirements beyond the visible stage headings
- no extra domain knowledge beyond what the chart and question already supply
- no self-consistency loops in the first version

This keeps the implementation aligned with the public paper's protocol framing.

## API Configuration

Settings will be loaded from `.env`:

- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

`OPENAI_MODEL` may contain multiple model ids separated by `|`.

Behavior:

- split on `|`
- trim whitespace
- ignore empty segments
- evaluate each model independently

Optional tuning settings may also be supported if present:

- `OPENAI_TEMPERATURE`
- `OPENAI_MAX_TOKENS`
- `OPENAI_TIMEOUT`

The first version will not require vendor-specific fields.

## Result Files

Per-run result JSON should include:

- dataset path
- protocol name
- model id
- started_at
- finished_at
- total questions
- correct questions
- accuracy
- subjects

Each subject entry should include:

- `person_id`
- `anonymous_id`
- `chart_cache_path`
- question list

Each question entry should include:

- `question_id`
- `question`
- `options`
- `gold_answer`
- `model_answer`
- `correct`
- `model_output`

## Error Handling

The implementation must fail clearly for:

- missing `.env` or missing required API fields
- unsupported dataset shape
- chart generation failure
- empty model list after parsing

The implementation should continue safely for:

- one model failing while others remain runnable
- one subject chart cache already existing
- malformed model text when the answer parser can still recover a final choice

## Testing Strategy

The first version should validate:

1. dataset normalization on one Contest8 file
2. local chart generation for one subject
3. chart caching behavior
4. answer parsing from varied output forms
5. one subject end-to-end multi-turn run
6. one subject end-to-end structured run

If live API tests are limited by credentials or latency, unit coverage should still verify all non-network components.

## Open Questions Resolved For V1

- Strict reproduction target: yes
- Local chart generator: `/home/sunnysab/Code/0-Cloned/bazi`
- API style: OpenAI-compatible via `.env`
- Multiple models: yes, split by `|`

## Implementation Recommendation

Proceed with a lightweight CLI reproduction tool, but structure internals as reusable modules so later reporting and analysis work can be added without rewriting the core evaluation loop.
