from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys

from acc_test.core.dataset import BirthInfo
from acc_test.core.formatter import format_bazi_context


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
    def __init__(self, cache_root: Path, bazi_script: Path) -> None:
        self.cache_root = Path(cache_root)
        self.bazi_script = Path(bazi_script)

    def build_command_args(self, *, birth: BirthInfo, gender: str) -> list[str]:
        args = [
            sys.executable,
            str(self.bazi_script),
            "-g",
        ]
        if gender.lower() == "female":
            args.append("-n")
        args.extend(
            [
                str(birth.year),
                str(birth.month),
                str(birth.day),
                str(birth.hour),
            ]
        )
        return args

    def cache_path(self, dataset_name: str, person_id: str) -> Path:
        return self.cache_root / "bazi-results" / f"{dataset_name}_{person_id}.json"

    def generate_or_load(
        self,
        *,
        dataset_name: str,
        person_id: str,
        subject_name: str,
        anonymous_id: str,
        birth: BirthInfo,
        gender: str,
    ) -> BaziCacheRecord:
        cache_path = self.cache_path(dataset_name, person_id)
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return BaziCacheRecord(**payload)

        command = self.build_command_args(birth=birth, gender=gender)
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        raw_output = completed.stdout
        record = BaziCacheRecord(
            person_id=person_id,
            name=subject_name,
            birth_input=asdict(birth),
            generator=str(self.bazi_script),
            generated_at=datetime.now(UTC).isoformat(),
            raw_output=raw_output,
            formatted_text=format_bazi_context(
                anonymous_id=anonymous_id,
                gender=gender,
                birth_raw=birth.raw,
                raw_output=raw_output,
            ),
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(asdict(record), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record
