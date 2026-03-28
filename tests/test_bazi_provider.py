from pathlib import Path

from acc_test.core.bazi_provider import BaziProvider
from acc_test.core.dataset import BirthInfo


def test_bazi_provider_builds_cli_args_for_female_subject(tmp_path: Path):
    provider = BaziProvider(cache_root=tmp_path, bazi_script=Path("/tmp/bazi.py"))
    birth = BirthInfo(
        year=1951,
        month=11,
        day=14,
        hour=10,
        minute=0,
        place="广东，中国",
        raw="raw",
        approximate=False,
    )

    args = provider.build_command_args(birth=birth, gender="female")

    assert "-g" in args
    assert "-n" in args
    assert args[-4:] == ["1951", "11", "14", "10"]


def test_bazi_provider_writes_cache_record(tmp_path: Path):
    provider = BaziProvider(cache_root=tmp_path, bazi_script=Path("/tmp/bazi.py"))

    path = provider.cache_path("contest8_2025", "P001")

    assert path.parent.name == "bazi-results"
    assert path.name == "contest8_2025_P001.json"
