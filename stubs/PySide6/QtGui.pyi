from typing import Any

# The bundled PySide6 QtGui.pyi has a syntax error mypy cannot parse. The UI
# modules (followed only to resolve names, never type-checked here) star-import
# it, so expose everything as ``Any`` via this shim. See QtCore.pyi.
def __getattr__(name: str) -> Any: ...
