"""Tests for ``leaguedirector.settings`` (pure JSON config, no Qt)."""

import json
import os

import pytest

from leaguedirector import settings


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    """Point ``Settings`` at a temporary config file instead of the user's home."""
    path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "userpath", lambda *args: str(path))
    return path


def test_defaults_when_no_file(settings_path):
    s = settings.Settings()
    assert s.data == {}
    assert s.value("missing") is None
    assert s.value("missing", "fallback") == "fallback"


def test_set_value_persists_to_disk(settings_path):
    s = settings.Settings()
    s.setValue("window", {"x": 10, "y": 20})
    s.setValue("name", "clip")

    assert os.path.isfile(settings_path)
    with open(settings_path) as f:
        on_disk = json.load(f)
    assert on_disk == {"window": {"x": 10, "y": 20}, "name": "clip"}


def test_round_trip_reload(settings_path):
    first = settings.Settings()
    first.setValue("volume", 0.5)
    first.setValue("paths", ["a", "b"])

    second = settings.Settings()
    assert second.value("volume") == 0.5
    assert second.value("paths") == ["a", "b"]


def test_set_value_overwrites(settings_path):
    s = settings.Settings()
    s.setValue("key", 1)
    s.setValue("key", 2)
    assert s.value("key") == 2
    assert settings.Settings().value("key") == 2
