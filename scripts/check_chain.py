"""Read-only connectivity check for an EVM JSON-RPC endpoint.

Sends two read-only requests (eth_chainId, eth_blockNumber). No keys, no transactions.
Usage:  python scripts/check_chain.py https://<rpc-url> [expected_chain_id]
Standard library only, so it needs no installs.
"""
import json
import sys
import urllib.error
import urllib.request


def rpc_call(url: str, method: str, timeout: float = 10.0):
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": []}
    ).encode()
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read())
    if "error" in body:
        raise RuntimeError(f"RPC error from node: {body['error']}")
    return body["result"]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/check_chain.py <rpc-url> [expected_chain_id]")
        return 2
    url = sys.argv[1]
    expected = int(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        chain_id = int(rpc_call(url, "eth_chainId"), 16)
        block = int(rpc_call(url, "eth_blockNumber"), 16)
    except urllib.error.HTTPError as exc:
        print(f"FAIL: server answered HTTP {exc.code} (the endpoint is reachable but unhealthy)")
        return 1
    except urllib.error.URLError as exc:
        print(f"FAIL: could not reach the endpoint: {exc.reason}")
        return 1
    except (RuntimeError, ValueError, KeyError) as exc:
        print(f"FAIL: unexpected response: {exc}")
        return 1

    print(f"chain id     : {chain_id}")
    print(f"latest block : {block}")
    if expected is not None:
        print("chain id matches expected" if chain_id == expected
              else f"MISMATCH: expected {expected}")
        return 0 if chain_id == expected else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
