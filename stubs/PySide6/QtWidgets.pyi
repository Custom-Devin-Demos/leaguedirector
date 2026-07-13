from typing import Any

# See QtGui.pyi / QtCore.pyi. Exposed as ``Any`` to avoid depending on the
# incomplete/unparseable bundled Qt stubs.
def __getattr__(name: str) -> Any: ...
