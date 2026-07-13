from typing import Any

# See QtCore.pyi for why these Qt names are exposed as ``Any``.
QNetworkAccessManager: Any
QNetworkRequest: Any
QNetworkReply: Any
QSslError: Any
QSslConfiguration: Any
QSslCertificate: Any

def __getattr__(name: str) -> Any: ...
