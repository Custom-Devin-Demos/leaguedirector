"""Shared pytest fixtures and network fakes for the leaguedirector test suite.

The Replay API client in ``leaguedirector.api`` talks to a local HTTPS service
through a shared ``QNetworkAccessManager``.  For tests we never touch the real
network: we inject a fake manager (via the ``Resource.network`` class attribute,
which ``Resource.manager()`` returns as-is when already set) whose ``get``/``post``
return a fake reply that asynchronously fires ``finished`` with canned JSON,
exactly like the real ``QNetworkReply``.
"""

import json
import os
import sys

# Ensure Qt runs without a display; harmless for QCoreApplication and required
# should any pytest-qt QApplication fixture be pulled in.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Make the repo importable when invoked as bare `pytest` (which, unlike
# `python -m pytest`, does not add the working directory to sys.path).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest
from PySide6.QtCore import QByteArray, QCoreApplication, QEventLoop, QObject, QTimer, Signal
from PySide6.QtNetwork import QNetworkReply

from leaguedirector import api


@pytest.fixture(scope="session")
def qapp():
    """A single ``QCoreApplication`` for the whole session.

    Resources are ``QObject``s that emit signals and use ``QTimer``, so an
    application object with a running event loop must exist.  ``QCoreApplication``
    is enough (no GUI / display required).
    """
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


@pytest.fixture(autouse=True)
def reset_resource_state(qapp):
    """Reset the class-level state that ``Resource`` mutates between tests."""
    api.Resource.connected = False
    api.Resource.network = None
    yield
    api.Resource.connected = False
    api.Resource.network = None


class FakeReply(QObject):
    """Minimal stand-in for ``QNetworkReply``.

    Implements just the surface ``Resource.finished`` touches: ``finished``
    signal, ``error()``, ``readAll().data()`` and ``errorString()``.
    """

    finished = Signal()

    def __init__(self, payload=None, error=QNetworkReply.NetworkError.NoError, error_string=""):
        super().__init__()
        self._payload = payload if payload is not None else {}
        self._error = error
        self._error_string = error_string

    def emit_finished(self):
        self.finished.emit()

    def error(self):
        return self._error

    def errorString(self):
        return self._error_string

    def readAll(self):
        return QByteArray(json.dumps(self._payload).encode())


class FakeManager(QObject):
    """Fake ``QNetworkAccessManager`` recording requests and returning fakes.

    The next reply to hand out is configured via :meth:`queue`.  ``get``/``post``
    schedule the reply's ``finished`` signal on the event loop (``singleShot(0)``)
    so the async wiring in ``Resource.update`` is exercised for real.
    """

    def __init__(self):
        super().__init__()
        self.requests = []
        self._next = None
        self.last_reply = None

    def queue(self, payload=None, error=QNetworkReply.NetworkError.NoError, error_string=""):
        self._next = FakeReply(payload=payload, error=error, error_string=error_string)
        return self._next

    def _make_reply(self):
        reply = self._next if self._next is not None else FakeReply()
        self._next = None
        self.last_reply = reply
        QTimer.singleShot(0, reply.emit_finished)
        return reply

    def get(self, request):
        self.requests.append(("GET", request.url().toString(), None))
        return self._make_reply()

    def post(self, request, body):
        raw = bytes(body.data()) if isinstance(body, QByteArray) else bytes(body)
        self.requests.append(("POST", request.url().toString(), raw.decode() or None))
        return self._make_reply()


@pytest.fixture
def fake_manager():
    """Install a :class:`FakeManager` as the shared network manager."""
    manager = FakeManager()
    api.Resource.network = manager
    return manager


@pytest.fixture
def wait_signal():
    """Provide the :func:`_wait_signal` helper to tests."""
    return _wait_signal


def _wait_signal(signal, timeout=2000):
    """Spin the event loop until ``signal`` fires (or ``timeout`` ms elapses).

    Returns ``True`` if the signal fired, ``False`` on timeout.
    """
    loop = QEventLoop()
    fired = {"value": False}

    def on_signal(*args):
        fired["value"] = True
        loop.quit()

    signal.connect(on_signal)
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(timeout)
    loop.exec()
    timer.stop()
    try:
        signal.disconnect(on_signal)
    except (RuntimeError, TypeError):
        pass
    return fired["value"]
