import pytest

from src.create_github_repo import normalize_repo_name


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Mi Repo", "mi-repo"),
        ("   ESPACIOS   ", "espacios"),
        ("Repo_123", "repo_123"),
        ("R@ro!#Nombre", "rronombre"),
        ("MAYUSCULAS-y_minusculas", "mayusculas-y_minusculas"),
    ],
)
def test_normalize_repo_name_valid(raw, expected):
    assert normalize_repo_name(raw) == expected


def test_normalize_repo_name_empty_raises():
    with pytest.raises(ValueError):
        normalize_repo_name("   ")


def test_normalize_repo_name_type_error():
    with pytest.raises(TypeError):
        normalize_repo_name(123)  # type: ignore[arg-type]
