"""Read-only connectivity check for an EVM JSON-RPC endpoint.

Sends two read-only requests (eth_chainId, eth_blockNumber). No keys, no transactions.
Usage:  python scripts/check_chain.py https://<rpc-url> [expected_chain_id]
Standard library only, so it needs no installs.

If the server refuses the request (HTTP 403), the script retries with a descriptive
User-Agent, because some firewalls reject Python's default one, and reports what it saw.
"""
import json
import sys
import urllib.error
import urllib.request

DEFAULT_UA = None  # urllib's own default ("Python-urllib/3.x")
DESCRIPTIVE_UA = "portal-sentinel-check/0.1 (read-only JSON-RPC health check)"


class HttpRefused(Exception):
    def __init__(self, code: int, server: str, body: str):
        super().__init__(f"HTTP {code}")
        self.code, self.server, self.body = code, server, body


def rpc_call(url: str, method: str, user_agent: str | None, timeout: float = 10.0):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": []}).encode()
    headers = {"Content-Type": "application/json"}
    if user_agent:
        headers["User-Agent"] = user_agent
    request = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        snippet = exc.read(300).decode("utf-8", "replace").replace("\n", " ")
        raise HttpRefused(exc.code, exc.headers.get("Server", "unknown"), snippet) from exc
    if "error" in body:
        raise RuntimeError(f"RPC error from node: {body['error']}")
    return body["result"]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/check_chain.py <rpc-url> [expected_chain_id]")
        return 2
    url = sys.argv[1]
    expected = int(sys.argv[2]) if len(sys.argv) > 2 else None

    chosen = None
    for label, ua in (("default Python User-Agent", DEFAULT_UA), ("descriptive User-Agent", DESCRIPTIVE_UA)):
        try:
            chain_id = int(rpc_call(url, "eth_chainId", ua), 16)
            chosen = (label, ua, chain_id)
            break
        except HttpRefused as exc:
            print(f"[{label}] server answered HTTP {exc.code} (Server: {exc.server})")
            print(f"    body: {exc.body[:200]}")
            if exc.code != 403:
                return 1
        except OSError as exc:  # includes URLError, timeouts and dropped connections
            print(f"FAIL: could not reach the endpoint: {getattr(exc, 'reason', exc)}")
            return 1
        except (RuntimeError, ValueError, KeyError) as exc:
            print(f"FAIL: unexpected response: {exc}")
            return 1

    if chosen is None:
        print("\nFAIL: the server refuses both requests (HTTP 403).")
        print("This is NOT a Python problem. Likely causes: a firewall/bot filter, an IP or region")
        print("restriction, or an allowlist. Ask the Portaldot team and include the 'Server' value above.")
        return 1

    label, ua, chain_id = chosen
    try:
        block = int(rpc_call(url, "eth_blockNumber", ua), 16)
    except (HttpRefused, RuntimeError, ValueError, KeyError, OSError) as exc:
        print(f"chain id read OK ({chain_id}) but eth_blockNumber failed: {exc}")
        return 1

    print(f"worked with   : {label}")
    print(f"chain id      : {chain_id}")
    print(f"latest block  : {block}")
    if expected is not None:
        print("chain id matches expected" if chain_id == expected else f"MISMATCH: expected {expected}")
        return 0 if chain_id == expected else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
