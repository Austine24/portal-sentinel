from datetime import datetime
from typing import Protocol

from app.domain.models import DataOrigin, Transaction


class DataSource(Protocol):
    """Anything that can supply transactions. The rest of Sentinel only sees this."""

    origin: DataOrigin

    def fetch_transactions(self, since: datetime, until: datetime) -> list[Transaction]: ...
