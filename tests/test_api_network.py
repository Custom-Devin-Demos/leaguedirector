"""Tests for the network wiring in ``leaguedirector.api`` using a fake manager.

Verifies that ``Resource.update`` issues the right GET/POST, that the
``finished`` -> field-application path decodes JSON back onto fields, that the
``updated`` signal fires, and that ``Resource.connected`` tracks reply status.
"""

import json

import pytest
from PySide6.QtNetwork import QNetworkReply

from leaguedirector import api


def test_get_applies_fields_and_sets_connected(fake_manager, wait_signal):
    game = api.Game()
    fake_manager.queue({"processID": 4321})

    game.update()
    assert wait_signal(game.updated)

    method, url, body = fake_manager.requests[-1]
    assert method == "GET"
    assert url == "https://127.0.0.1:2999/replay/game"
    assert body is None
    assert game.processID == 4321
    assert api.Resource.connected is True


def test_post_sends_body_and_applies_response(fake_manager, wait_signal):
    recording = api.Recording()
    fake_manager.queue({"recording": True, "path": "/tmp/out.webm", "width": 1920})

    recording.recording = True  # triggers an async POST via __setattr__

    method, url, body = fake_manager.requests[-1]
    assert method == "POST"
    assert url == "https://127.0.0.1:2999/replay/recording"
    assert json.loads(body) == {"recording": True}

    assert wait_signal(recording.updated)
    assert recording.path == "/tmp/out.webm"
    assert recording.width == 1920
    assert api.Resource.connected is True


def test_connection_refused_sets_disconnected(fake_manager, wait_signal):
    api.Resource.connected = True
    game = api.Game()
    fake_manager.queue(error=QNetworkReply.NetworkError.ConnectionRefusedError)

    game.update()
    assert wait_signal(game.updated)
    assert api.Resource.connected is False


def test_other_error_keeps_connected_state(fake_manager, wait_signal):
    game = api.Game()
    fake_manager.queue(
        error=QNetworkReply.NetworkError.ContentNotFoundError,
        error_string="Not Found",
    )
    game.update()
    assert wait_signal(game.updated)
    # A non-connection error should not flip the connected flag.
    assert api.Resource.connected is False


def test_particles_apply_overrides_into_dict(fake_manager, wait_signal):
    particles = api.Particles()
    fake_manager.queue({"Explosion": True, "Smoke": False})

    particles.update()
    assert wait_signal(particles.updated)

    assert particles.hasParticle("Explosion")
    assert particles.getParticle("Smoke") is False
    assert particles.getParticle("Unknown") is True  # default


def test_setparticle_only_posts_known_particles(fake_manager):
    particles = api.Particles()
    particles.particles = {"Explosion": True}

    particles.setParticle("Explosion", False)
    assert fake_manager.requests[-1][0] == "POST"
    assert json.loads(fake_manager.requests[-1][2]) == {"Explosion": False}

    before = len(fake_manager.requests)
    particles.setParticle("Unknown", True)  # not present -> no request
    assert len(fake_manager.requests) == before


def test_unchanged_field_does_not_issue_request(fake_manager):
    render = api.Render()
    assert render.fieldOfView == 0
    render.fieldOfView = 0  # same value -> no update
    assert fake_manager.requests == []


def test_readonly_resource_rejects_writes(fake_manager):
    game = api.Game()
    with pytest.raises(AttributeError):
        game.processID = 99
    assert fake_manager.requests == []


def test_data_and_keys_reflect_fields(fake_manager):
    playback = api.Playback()
    assert set(playback.keys()) == set(api.Playback.fields)
    assert playback.data()["length"] == 1.0
