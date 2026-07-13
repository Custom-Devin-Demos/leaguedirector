from __future__ import annotations

import os
import json
from typing import Any
from leaguedirector.widgets import userpath

class Settings(object):

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.path: str = userpath('config.json')
        self.loadFile()

    def value(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def setValue(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.saveFile()

    def saveFile(self) -> None:
        with open(self.path, 'w') as f:
            json.dump(self.data, f, sort_keys=True, indent=4)

    def loadFile(self) -> None:
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                self.data = json.load(f)
