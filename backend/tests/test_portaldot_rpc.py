import pytest

from app.portaldot.rpc import JsonRpcClient, RpcError, RpcUnavailable
from tests.mock_node import MockChain, start


@pytest.fixture()
def node():
    created = []

    def make(**kwargs):
        chain = MockChain(**kwargs)
        url, stop = start(chain)
        created.append(stop)
        return chain, JsonRpcClient(url, timeout=3)

    yield make
    for stop in created:
        stop()


def test_call_returns_the_result(node):
    _, client = node()
    assert client.call("system_chain") == "Mock Testnet"


def test_sends_a_descriptive_user_agent(node):
    chain, client = node()
    client.call("system_chain")
    assert chain.last_user_agent.startswith("portal-sentinel")
    assert "Python-urllib" not in chain.last_user_agent


def test_rpc_error_is_distinguished_from_unreachable(node):
    _, client = node()
    with pytest.raises(RpcError, match="Method not found"):
        client.call("no_such_method")


def test_refusal_becomes_unavailable_with_the_status(node):
    _, client = node(fail_status=403)
    with pytest.raises(RpcUnavailable, match="403"):
        client.call("system_chain")


def test_unreachable_node_becomes_unavailable():
    with pytest.raises(RpcUnavailable):
        JsonRpcClient("http://127.0.0.1:9", timeout=1).call("system_chain")


def test_batch_keeps_order_even_if_the_server_reorders(node):
    chain, client = node(reverse_batches=True)
    results = client.batch([("chain_getBlockHash", [n]) for n in (5, 6, 7)])
    assert results == ["0xhash5", "0xhash6", "0xhash7"]
    assert chain.http_requests == 1


def test_batch_falls_back_to_single_calls_when_unsupported(node):
    chain, client = node(batch=False)
    results = client.batch([("chain_getBlockHash", [n]) for n in (1, 2, 3)])
    assert results == ["0xhash1", "0xhash2", "0xhash3"]
    assert chain.http_requests == 1 + 3          # one rejected batch, then three single calls


def test_batch_is_split_into_chunks(node):
    chain, client = node()
    client.max_batch = 2
    client.batch([("chain_getBlockHash", [n]) for n in range(5)])
    assert chain.http_requests == 3


def test_tolerated_errors_appear_in_their_slot(node):
    _, client = node(health_enabled=False)
    chain_name, health = client.batch([("system_chain", []), ("system_health", [])], tolerate_errors=True)
    assert chain_name == "Mock Testnet" and isinstance(health, RpcError)


def test_untolerated_error_raises(node):
    _, client = node(health_enabled=False)
    with pytest.raises(RpcError):
        client.batch([("system_chain", []), ("system_health", [])])
