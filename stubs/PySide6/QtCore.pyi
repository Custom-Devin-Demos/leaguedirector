from typing import Any

# PySide6 ships .pyi stubs, but the bundled QtGui.pyi has a syntax error that
# mypy cannot parse. Rather than depend on the (incomplete) Qt stubs, the Qt
# names used by the annotated modules are exposed here as ``Any`` so that
# ``from PySide6.QtCore import *`` resolves without pulling in the broken stubs.
QObject: Any
Signal: Any
QTimer: Any
QSettings: Any
QCoreApplication: Any
QUrl: Any
QByteArray: Any

def __getattr__(name: str) -> Any: ...
