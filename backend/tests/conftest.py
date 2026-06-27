from pathlib import Path

import pytest

from orchestration.loader import load_journeys

FIXTURES = Path(__file__).parent / "fixtures" / "journeys"


@pytest.fixture
def registry() -> dict[str, dict]:
    """The loaded test journey registry (also exercises A1 loader + validation)."""
    return load_journeys(FIXTURES)
