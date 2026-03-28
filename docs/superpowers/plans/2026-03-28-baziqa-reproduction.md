# BaziQA Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a strict-reproduction evaluation toolkit for Contest8 that generates local BaZi chart context, runs `Multi-turn` and `Structured` protocols through an OpenAI-compatible API, and writes scored result files.

**Architecture:** Add two thin CLI entrypoints under `acc_test/` and keep all reusable logic in focused modules under `acc_test/core/`. The pipeline is `dataset -> local bazi generation/cache -> prompt protocol -> LLM call -> answer parse -> scoring/output`, with tests covering each non-network component and one end-to-end subject session flow.

**Tech Stack:** Python 3, `pytest`, `python-dotenv`, `openai`, local `/home/sunnysab/Code/0-Cloned/bazi/bazi.py`

---

## File Structure

- Create: `acc_test/__init__.py`
- Create: `acc_test/bazi_eval_multiturn.py`
- Create: `acc_test/bazi_eval_structured.py`
- Create: `acc_test/core/__init__.py`
- Create: `acc_test/core/dataset.py`
- Create: `acc_test/core/bazi_provider.py`
- Create: `acc_test/core/formatter.py`
- Create: `acc_test/core/llm_client.py`
- Create: `acc_test/core/protocols.py`
- Create: `acc_test/core/parser.py`
- Create: `acc_test/core/evaluator.py`
- Create: `tests/conftest.py`
- Create: `tests/test_dataset.py`
- Create: `tests/test_parser.py`
- Create: `tests/test_bazi_provider.py`
- Create: `tests/test_evaluator.py`
- Create: `requirements.txt`
- Modify: `README.md`

## Execution Notes

- Follow `@superpowers/test-driven-development` for every behavior change.
- Follow `@superpowers/verification-before-completion` before any completion claim.
- User constraint: after each completed implementation task, create a git commit.
- If still on `main`, stop before production edits and confirm branch/worktree strategy or obtain explicit consent to proceed there.

### Task 1: Bootstrap package and dataset normalization

**Files:**
- Create: `acc_test/__init__.py`
- Create: `acc_test/core/__init__.py`
- Create: `acc_test/core/dataset.py`
- Create: `tests/conftest.py`
- Create: `tests/test_dataset.py`
- Create: `requirements.txt`

- [ ] **Step 1: Write the failing dataset tests**

```python
from acc_test.core.dataset import load_contest_dataset


def test_load_contest_dataset_skips_metadata_row():
    subjects = load_contest_dataset("data/contest8_2025.json")
    assert len(subjects) == 8


def test_load_contest_dataset_keeps_questions_and_birth_info():
    subject = load_contest_dataset("data/contest8_2025.json")[0]
    assert subject.person_id == "guangdong_female_19511114_P001"
    assert subject.birth.hour == 10
    assert len(subject.questions) == 5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors because `acc_test.core.dataset` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class BirthInfo:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    place: str
    raw: str
    approximate: bool


@dataclass(frozen=True)
class Question:
    question_id: str
    question: str
    options: tuple[str, ...]
    answer: str


@dataclass(frozen=True)
class Subject:
    person_id: str
    name: str
    gender: str
    birth: BirthInfo
    questions: tuple[Question, ...]


def load_contest_dataset(path: str | Path) -> list[Subject]:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_dataset.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt acc_test/__init__.py acc_test/core/__init__.py acc_test/core/dataset.py tests/conftest.py tests/test_dataset.py
git commit -m "feat: add contest dataset loader"
```

### Task 2: Answer parsing and protocol prompt builders

**Files:**
- Create: `acc_test/core/parser.py`
- Create: `acc_test/core/protocols.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: Write the failing parser/protocol tests**

```python
from acc_test.core.parser import extract_answer_letter
from acc_test.core.protocols import build_question_prompt


def test_extract_answer_letter_prefers_explicit_final_answer():
    text = "分析略\n最终答案：B\n另一个字母 A"
    assert extract_answer_letter(text, choices=("A", "B", "C", "D")) == "B"


def test_build_structured_prompt_contains_three_required_stages():
    prompt = build_question_prompt(
        protocol="structured",
        question="婚姻如何？",
        options=("A. 一婚", "B. 二婚", "C. 一生未嫁", "D. 夫早亡"),
    )
    assert "量化扫描" in prompt
    assert "冲突定级" in prompt
    assert "应象映射" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL because parser and protocol modules do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def extract_answer_letter(text: str, choices: Sequence[str]) -> str | None:
    ...


def build_question_prompt(protocol: str, question: str, options: Sequence[str]) -> str:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add acc_test/core/parser.py acc_test/core/protocols.py tests/test_parser.py
git commit -m "feat: add prompt builders and answer parser"
```

### Task 3: Local bazi provider with cache generation

**Files:**
- Create: `acc_test/core/bazi_provider.py`
- Create: `acc_test/core/formatter.py`
- Create: `tests/test_bazi_provider.py`

- [ ] **Step 1: Write the failing provider tests**

```python
from pathlib import Path

from acc_test.core.bazi_provider import BaziProvider
from acc_test.core.dataset import BirthInfo


def test_bazi_provider_builds_cli_args_for_female_subject(tmp_path: Path):
    provider = BaziProvider(cache_root=tmp_path, bazi_script=Path("/tmp/bazi.py"))
    birth = BirthInfo(1951, 11, 14, 10, 0, "广东，中国", "raw", False)
    args = provider.build_command_args(birth=birth, gender="female")
    assert "-g" in args and "-n" in args


def test_bazi_provider_writes_cache_record(tmp_path: Path):
    provider = BaziProvider(cache_root=tmp_path, bazi_script=Path("/tmp/bazi.py"))
    path = provider.cache_path("contest8_2025", "P001")
    assert path.parent.name == "bazi-results"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_bazi_provider.py -v`
Expected: FAIL because provider module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class BaziCacheRecord:
    person_id: str
    name: str
    birth_input: dict[str, object]
    generator: str
    generated_at: str
    raw_output: str
    formatted_text: str


class BaziProvider:
    def build_command_args(self, birth: BirthInfo, gender: str) -> list[str]:
        ...

    def generate_or_load(...):
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_bazi_provider.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add acc_test/core/bazi_provider.py acc_test/core/formatter.py tests/test_bazi_provider.py
git commit -m "feat: add local bazi provider and formatter"
```

### Task 4: Evaluator core and LLM client seam

**Files:**
- Create: `acc_test/core/llm_client.py`
- Create: `acc_test/core/evaluator.py`
- Create: `tests/test_evaluator.py`

- [ ] **Step 1: Write the failing evaluator tests**

```python
from acc_test.core.evaluator import score_subject_answers


def test_score_subject_answers_marks_correct_and_incorrect():
    scored = score_subject_answers(
        gold_answers=["B", "D"],
        predicted_answers=["B", "A"],
    )
    assert scored.correct_count == 1
    assert scored.total_count == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_evaluator.py -v`
Expected: FAIL because evaluator module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class OpenAICompatibleClient:
    @classmethod
    def from_env(cls) -> "OpenAICompatibleClient":
        ...


def score_subject_answers(gold_answers: Sequence[str], predicted_answers: Sequence[str]) -> ScoreSummary:
    ...


def evaluate_subject(...):
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_evaluator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add acc_test/core/llm_client.py acc_test/core/evaluator.py tests/test_evaluator.py
git commit -m "feat: add evaluator core and llm client"
```

### Task 5: CLI entrypoints and result writing

**Files:**
- Create: `acc_test/bazi_eval_multiturn.py`
- Create: `acc_test/bazi_eval_structured.py`
- Modify: `acc_test/core/evaluator.py`

- [ ] **Step 1: Write the failing CLI smoke tests or command-level assertions**

```python
from acc_test.bazi_eval_multiturn import build_arg_parser


def test_cli_accepts_dataset_path_and_limit_subjects():
    parser = build_arg_parser()
    args = parser.parse_args(["data/contest8_2025.json", "--limit-subjects", "1"])
    assert args.dataset_path.endswith("contest8_2025.json")
    assert args.limit_subjects == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_evaluator.py -v`
Expected: FAIL because entrypoint parser is missing.

- [ ] **Step 3: Write minimal implementation**

```python
def build_arg_parser() -> argparse.ArgumentParser:
    ...


def main() -> int:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_evaluator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add acc_test/bazi_eval_multiturn.py acc_test/bazi_eval_structured.py acc_test/core/evaluator.py tests/test_evaluator.py
git commit -m "feat: add evaluation cli entrypoints"
```

### Task 6: Documentation and end-to-end verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write the failing documentation acceptance checklist**

Checklist:
- README explains required `.env` keys
- README explains `OPENAI_MODEL` supports `|`
- README shows one multi-turn command
- README shows one structured command
- README mentions local `bazi` dependency

- [ ] **Step 2: Run implementation verification**

Run: `pytest tests -v`
Expected: PASS

- [ ] **Step 3: Run focused end-to-end smoke test**

Run: `python acc_test/bazi_eval_multiturn.py data/contest8_2025.json --limit-subjects 1`
Expected: exit 0 and write a result file under `result/evals/...`

- [ ] **Step 4: Update README with final usage**

```markdown
python acc_test/bazi_eval_multiturn.py data/contest8_2025.json --limit-subjects 1
python acc_test/bazi_eval_structured.py data/contest8_2025.json --limit-subjects 1
```

- [ ] **Step 5: Commit**

```bash
git add README.md result acc_test tests
git commit -m "docs: add reproduction usage guide"
```
