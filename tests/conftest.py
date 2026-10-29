import pytest
import requests

from weather_odds.sources import era5


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Tests never use the network (requirement N3): real sessions and the real bucket fail."""

    def blocked(*args, **kwargs):
        raise RuntimeError("tests must not use the network")

    monkeypatch.setattr(requests.Session, "request", blocked)
    monkeypatch.setattr(era5, "open_bucket", blocked)
