from datetime import datetime, timezone

import pytest

from app.portaldot.collector import HeaderCache, collect_snapshot
from app.portaldot.headers import decode_block_production
from app.portaldot.rpc import JsonRpcClient, RpcError
from tests.mock_node import MockChain, babe_log, start


@pytest.fixture()
def node():
    stops = []

    def make(**kwargs):
        chain = MockChain(**kwargs)
        url, stop = start(chain)
        stops.append(stop)
        return chain, JsonRpcClient(url, timeout=3)

    yield make
    for stop in stops:
        stop()


def now(chain):
    return datetime.fromtimestamp(chain.now_ts, tz=timezone.utc)


def test_healthy_chain_snapshot(node):
    chain, client = node()
    snap = collect_snapshot(client, HeaderCache(), window=60, now=now(chain))
    assert (snap.best_block, snap.finalized_block, snap.finality_lag) == (1000, 997, 3)
    assert snap.window_blocks == 60 and snap.missed_slots == 0
    assert snap.authors == {"0": 30, "1": 30} and snap.distinct_authors == 2
    assert snap.max_author_share == 0.5
    assert snap.block_age_s == pytest.approx(12, abs=6)       # slot time is derived, within one slot
    assert snap.peers == 7 and snap.chain_name == "Mock Testnet"
    assert snap.data_origin == "live"


def test_missed_slots_are_counted(node):
    chain, client = node(gaps=(990, 995, 996))
    snap = collect_snapshot(client, HeaderCache(), window=60, now=now(chain))
    assert snap.missed_slots == 3


def test_single_author_is_reported_as_concentration(node):
    chain, client = node(authors=(0,))
    snap = collect_snapshot(client, HeaderCache(), window=30, now=now(chain))
    assert snap.distinct_authors == 1 and snap.max_author_share == 1.0


def test_cache_means_a_refresh_only_downloads_new_blocks(node):
    chain, client = node()
    cache = HeaderCache()
    collect_snapshot(client, cache, window=60, now=now(chain))
    assert chain.calls["chain_getBlockHash"] == 60
    chain.best += 1
    chain.finalized += 1
    collect_snapshot(client, cache, window=60, now=now(chain))
    assert chain.calls["chain_getBlockHash"] == 61            # exactly one more block fetched


def test_works_when_system_health_is_disabled(node):
    chain, client = node(health_enabled=False)
    snap = collect_snapshot(client, HeaderCache(), window=20, now=now(chain))
    assert snap.peers is None and snap.chain_name == "Mock Testnet"


def test_a_node_error_on_essential_data_is_raised(node):
    chain, client = node(header_error=True)
    with pytest.raises(RpcError):
        collect_snapshot(client, HeaderCache(), window=20, now=now(chain))


def test_cache_prunes_to_its_limit():
    cache = HeaderCache(limit=3)
    from app.portaldot.collector import BlockInfo
    for n in range(6):
        cache.put(BlockInfo(n, 0, n))
    assert cache.get(0) is None and cache.get(5) is not None


def test_backend_decoder_agrees_with_the_standalone_probe():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_substrate.py"
    spec = importlib.util.spec_from_file_location("probe_substrate", path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    for log in (babe_log(2, 1, 123), babe_log(1, 0, 5, extra=96)):
        assert decode_block_production([log]) == {
            k: v for k, v in probe.decode_author([log]).items()
        }
