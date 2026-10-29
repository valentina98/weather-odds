import pytest
import requests
from fakes import FakeSession

from weather_odds.download import Downloader, DownloadError

URL = "https://example.org/data.csv"


def downloader(routes) -> tuple[Downloader, FakeSession]:
    session = FakeSession(routes)
    return Downloader(session, retries=2, pause=0), session


def test_fetches_once_then_uses_the_cache(tmp_path):
    dl, session = downloader({URL: b"a,b\n"})
    path = tmp_path / "raw" / "data.csv"
    assert dl.fetch(URL, path) is True
    assert path.read_bytes() == b"a,b\n"
    assert dl.fetch(URL, path) is False
    assert len(session.calls) == 1


def test_refresh_downloads_again(tmp_path):
    dl, session = downloader({URL: [b"old", b"new"]})
    path = tmp_path / "data.csv"
    dl.fetch(URL, path)
    assert dl.fetch(URL, path, refresh=True) is True
    assert path.read_bytes() == b"new"


def test_missing_file_is_remembered(tmp_path):
    dl, session = downloader({})
    path = tmp_path / "data.csv"
    assert dl.fetch(URL, path) is False
    assert not path.exists()
    assert dl.fetch(URL, path) is False
    assert len(session.calls) == 1
    dl.fetch(URL, path, refresh=True)
    assert len(session.calls) == 2


def test_missing_current_file_is_asked_again(tmp_path):
    dl, session = downloader({})
    path = tmp_path / "data.csv"
    dl.fetch(URL, path, refresh=True)
    dl.fetch(URL, path, refresh=True)
    assert len(session.calls) == 2


def test_busy_server_is_retried(tmp_path):
    dl, session = downloader({URL: [503, requests.ConnectionError("reset"), b"ok"]})
    assert dl.fetch(URL, tmp_path / "data.csv") is True
    assert len(session.calls) == 3
    assert dl.retried == 2


def test_gives_up_after_the_retries(tmp_path):
    dl, session = downloader({URL: 503})
    with pytest.raises(DownloadError, match="503"):
        dl.fetch(URL, tmp_path / "data.csv")
    assert len(session.calls) == 3


def test_unreachable_host_raises_after_the_retries(tmp_path):
    dl, _ = downloader({URL: requests.ConnectionError("down")})
    with pytest.raises(requests.ConnectionError):
        dl.fetch(URL, tmp_path / "data.csv")


def test_rejected_content_is_not_saved(tmp_path):
    dl, _ = downloader({URL: b"<html>timeout</html>"})
    path = tmp_path / "data.csv"
    with pytest.raises(DownloadError, match="unexpected content"):
        dl.fetch(URL, path, check=lambda content: content.startswith(b"a,b"))
    assert not path.exists()
