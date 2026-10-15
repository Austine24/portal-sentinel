from datetime import timedelta

from app.data.simulated import SimulatedSource
from tests.factories import NOW


def test_simulated_source_is_deterministic_and_labelled():
    a = SimulatedSource(NOW).fetch_transactions(NOW - timedelta(days=8), NOW)
    b = SimulatedSource(NOW).fetch_transactions(NOW - timedelta(days=8), NOW)
    assert [t.tx_hash for t in a] == [t.tx_hash for t in b]
    assert {t.data_origin for t in a} == {"simulated"}
    assert all(t.tx_hash.startswith("demo-tx-") for t in a)
