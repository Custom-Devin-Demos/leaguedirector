"""Pure-logic tests for ``leaguedirector.api`` resources.

These exercise the client-side computation (camera math, playback time,
move-back snapping) without hitting the network.  Mutating a field triggers
``Resource.update`` (an async POST), so a fake manager is installed to keep
those writes off the wire.
"""

import time

import pytest

from leaguedirector import api


@pytest.fixture
def render(fake_manager):
    return api.Render()


@pytest.fixture
def playback(fake_manager):
    return api.Playback()


def test_move_camera_offsets_position(render):
    render.apply({"cameraPosition": {"x": 1.0, "y": 2.0, "z": 3.0}})
    render.moveCamera(x=10, y=-1, z=0.5)
    assert render.cameraPosition == {"x": 11.0, "y": 1.0, "z": 3.5}


def test_move_camera_does_not_mutate_in_place(render):
    original = {"x": 0, "y": 0, "z": 0}
    render.apply({"cameraPosition": original})
    render.moveCamera(x=5)
    # A new dict must be assigned; the original object stays untouched.
    assert original == {"x": 0, "y": 0, "z": 0}
    assert render.cameraPosition == {"x": 5, "y": 0, "z": 0}


def test_rotate_camera_offsets_rotation(render):
    render.apply({"cameraRotation": {"x": 90, "y": 0, "z": 45}})
    render.rotateCamera(x=10, z=-45)
    assert render.cameraRotation == {"x": 100, "y": 0, "z": 0}


def test_camera_move_back_toggle_and_snap(render):
    render.apply({"cameraPosition": {"x": 5.0, "y": 6.0, "z": 7.0}})
    render.toggleCameraMoveBackX()
    assert render.cameraMoveBackX == 5.0

    # Move away, then let the "stopped moving" tick snap X back.
    render.moveCamera(x=100)
    assert render.cameraPosition["x"] == 105.0
    render.updateCameraMoveBack()  # records last position
    render.updateCameraMoveBack()  # position unchanged -> snap X back
    assert render.cameraPosition["x"] == 5.0

    render.toggleCameraMoveBackX()
    assert render.cameraMoveBackX is None


def test_playback_current_time_when_paused(playback):
    playback.apply({"paused": True, "time": 12.5, "speed": 1.0, "length": 100.0})
    assert playback.currentTime == 12.5


def test_playback_current_time_when_playing_advances(playback):
    playback.apply({"paused": False, "time": 0.0, "speed": 2.0, "length": 100.0})
    playback.timestamp = time.time() - 1.0  # pretend 1s elapsed
    # time + elapsed*speed ~= 0 + 1*2 = 2.0, capped at length
    assert playback.currentTime == pytest.approx(2.0, abs=0.2)


def test_playback_current_time_capped_at_length(playback):
    playback.apply({"paused": False, "time": 0.0, "speed": 100.0, "length": 5.0})
    playback.timestamp = time.time() - 10.0
    assert playback.currentTime == 5.0


def test_playback_current_time_formatted(playback):
    playback.apply({"paused": True, "time": 65.0})
    assert playback.currentTimeFormatted == "01:05.00"


def test_toggle_play_flips_paused(playback):
    playback.apply({"paused": False})
    playback.togglePlay()
    assert playback.paused is True
    playback.togglePlay()
    assert playback.paused is False


def test_set_speed(playback):
    playback.setSpeed(3.5)
    assert playback.speed == 3.5


def test_adjust_time(playback):
    playback.apply({"paused": True, "time": 10.0, "length": 100.0})
    playback.adjustTime(5.0)
    assert playback.time == 15.0
