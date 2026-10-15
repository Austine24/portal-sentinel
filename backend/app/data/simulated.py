"""DEMO / SIMULATED transaction generator. Nothing here comes from a blockchain."""
import math
import random
from datetime import datetime, timedelta, timezone

from app.domain.models import Transaction

BURST_ACCOUNT = "demo-wallet-A"


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth's algorithm; fine for small lambda."""
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


class SimulatedSource:
    origin = "simulated"

    def __init__(self, now: datetime, seed: int = 42, days: int = 7, accounts: int = 8):
        self.now = now
        self.seed = seed
        self.days = days
        self.accounts = accounts

    def fetch_transactions(self, since: datetime, until: datetime) -> list[Transaction]:
        return [t for t in self._generate() if since <= t.timestamp <= until]

    def _generate(self) -> list[Transaction]:
        rng = random.Random(self.seed)
        names = [BURST_ACCOUNT] + [f"demo-wallet-{chr(66 + i)}" for i in range(self.accounts - 1)]
        start = (self.now - timedelta(days=self.days)).replace(minute=0, second=0, microsecond=0)
        txs: list[Transaction] = []
        counter = 0

        for name in names:
            rate = rng.uniform(0.5, 2.0)         # normal transactions per hour
            typical = rng.uniform(5, 40)         # typical value
            peers = [f"demo-peer-{rng.randint(1, 50)}" for _ in range(5)]
            hour = start
            while hour < self.now - timedelta(hours=1):
                for _ in range(_poisson(rng, rate)):
                    counter += 1
                    txs.append(Transaction(
                        tx_hash=f"demo-tx-{counter:06d}",
                        sender=name,
                        recipient=rng.choice(peers),
                        value=round(rng.lognormvariate(math.log(typical), 0.35), 4),
                        timestamp=hour + timedelta(seconds=rng.randint(0, 3599)),
                        success=rng.random() > 0.03,
                        data_origin="simulated",
                    ))
                hour += timedelta(hours=1)

        # Injected scenario (SIMULATED): a burst in the final hour from one account.
        for i in range(60):
            counter += 1
            txs.append(Transaction(
                tx_hash=f"demo-tx-{counter:06d}",
                sender=BURST_ACCOUNT,
                recipient=f"demo-newpeer-{i}",
                value=round(rng.lognormvariate(math.log(300), 0.3), 4),
                timestamp=self.now - timedelta(minutes=rng.randint(1, 59)),
                success=rng.random() > 0.3,
                data_origin="simulated",
            ))
        return sorted(txs, key=lambda t: t.timestamp)
