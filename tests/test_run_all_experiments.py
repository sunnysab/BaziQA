from pathlib import Path
import os
import subprocess


def test_run_all_experiments_dry_run_prints_expected_matrix():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_all_experiments.sh"

    env = os.environ.copy()
    env.update(
        {
            "DRY_RUN": "1",
            "RUNS": "2",
            "MAX_WORKERS": "4",
            "PROTOCOLS": "multiturn structured",
            "PYTHON_BIN": str(repo_root / ".venv" / "bin" / "python"),
        }
    )

    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 4
    assert all("acc_test/run_benchmark.py" in line for line in lines)
    assert any("--output-root result/run1" in line for line in lines)
    assert any("--output-root result/run2" in line for line in lines)
