from acc_test.core.dataset import load_contest_dataset


def test_load_contest_dataset_skips_metadata_row():
    subjects = load_contest_dataset("data/contest8_2025.json")
    assert len(subjects) == 8


def test_load_contest_dataset_keeps_questions_and_birth_info():
    subject = load_contest_dataset("data/contest8_2025.json")[0]
    assert subject.person_id == "guangdong_female_19511114_P001"
    assert subject.birth.hour == 10
    assert len(subject.questions) == 5

