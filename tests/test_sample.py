import time
import pytest


def test_fast():
    assert 1 + 1 == 2


@pytest.mark.slow
def test_slow():
    time.sleep(2)
    assert True


@pytest.mark.db
def test_db():
    assert "db" == "db"


@pytest.mark.db
@pytest.mark.slow
def test_db_slow():
    time.sleep(2)
    assert True