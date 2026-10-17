"""Read-only look at a Portaldot testnet. Sends no transactions and uses no keys.

Usage:
  python scripts/inspect_chain.py [evm-rpc-url] [--blocks 30] [--substrate-http URL | --no-substrate]

Reports chain id, latest block, block time, how many transactions recent blocks contain,
and (if the node answers over HTTPS) the Substrate chain name, token properties and runtime version.
Standard library only. Uses a descriptive User-Agent, because the public RPC rejects Python's default one.
"""
import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
import urllib.error
import urllib.request

UA = "portal-sentinel-check/0.1 (read-only JSON-RPC health check)"
DEFAULT_EVM = "https://test-evm-rpc-v3.portaldot.dev"
DEFAULT_SUBSTRATE_HTTP = "https://test-node-v3.portaldot.dev"


def rpc(url: str, method: str, params=None, timeout: float = 15.0):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}).encode()
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json", "User-Agent": UA}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read())
    if "error" in body:
        raise RuntimeError(body["error"].get("message", str(body["error"])))
    return body["result"]


def try_rpc(url, method, params=None):
    try:
        return rpc(url, method, params), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        return None, str(getattr(exc, "reason", exc))


def inspect_evm(url: str, block_count: int) -> tuple[int, int | None]:
    print(f"== EVM JSON-RPC: {url}")
    for label, method in (("client", "web3_clientVersion"), ("network id", "net_version")):
        value, err = try_rpc(url, method)
        print(f"{label:<14}: {value if err is None else 'not available (' + err + ')'}")

    chain_hex, err = try_rpc(url, "eth_chainId")
    latest_hex, err2 = try_rpc(url, "eth_blockNumber")
    if err or err2:
        print(f"FAIL: cannot read chain id / latest block ({err or err2})")
        return 1, None
    latest = int(latest_hex, 16)
    print(f"{'chain id':<14}: {int(chain_hex, 16)}")
    print(f"{'latest block':<14}: {latest}")
    gas_price, err = try_rpc(url, "eth_gasPrice")
    print(f"{'gas price':<14}: {int(gas_price, 16) if err is None else 'not available'} (raw units; the token's decimals decide the real cost)")

    blocks = []
    for number in range(latest, max(-1, latest - block_count), -1):
        block, err = try_rpc(url, "eth_getBlockByNumber", [hex(number), True])
        if err or block is None:
            print(f"(stopped at block {number}: {err or 'empty answer'})")
            break
        blocks.append(block)
    if not blocks:
        print("no blocks could be read")
        return 1, latest

    genesis, _ = try_rpc(url, "eth_getBlockByNumber", ["0x0", False])
    if isinstance(genesis, dict):
        print(f"\nblock 0 hash (EVM view): {genesis.get('hash')}")
    newest = blocks[0]
    stamp = int(newest["timestamp"], 16)
    age = int(time.time()) - stamp
    when = datetime.fromtimestamp(stamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"\nnewest block      : #{int(newest['number'], 16)}  hash {newest.get('hash')}")
    print(f"newest block time : {when} ({age} s ago)")
    if age > 120:
        print("  WARNING: the newest block is more than 2 minutes old. The chain may be stalled, or this endpoint lags.")

    txs = [t for b in blocks for t in b.get("transactions", []) if isinstance(t, dict)]
    stamps = sorted(int(b["timestamp"], 16) for b in blocks)
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    print(f"\nlast {len(blocks)} blocks (#{int(blocks[-1]['number'], 16)} to #{int(blocks[0]['number'], 16)}):")
    if gaps:
        print(f"  block time        : about {statistics.median(gaps):.1f} s (median), {min(gaps)} to {max(gaps)} s")
    print(f"  transactions      : {len(txs)} total, {len(txs) / len(blocks):.2f} per block")
    print(f"  blocks with txs   : {sum(1 for b in blocks if b.get('transactions'))} of {len(blocks)}")
    senders = {t.get("from") for t in txs}
    print(f"  distinct senders  : {len(senders)}")
    if txs:
        t = txs[0]
        value = int(t.get("value", "0x0"), 16)
        print(f"  sample tx         : {t.get('hash')} from {t.get('from')} to {t.get('to')} value(raw)={value}")
    else:
        print("  (no transactions in this sample; a quiet chain means we must generate our own activity)")
    return 0, latest


def inspect_substrate(url: str) -> int | None:
    print(f"\n== Substrate node over HTTPS: {url}")
    chain, err = try_rpc(url, "system_chain")
    if err:
        print(f"not answering over HTTPS ({err}). The node may be WebSocket-only; that is fine.")
        return None
    print(f"{'chain name':<14}: {chain}")
    props, _ = try_rpc(url, "system_properties")
    print(f"{'properties':<14}: {json.dumps(props)}")
    runtime, _ = try_rpc(url, "state_getRuntimeVersion")
    if isinstance(runtime, dict):
        print(f"{'runtime':<14}: {runtime.get('specName')} spec {runtime.get('specVersion')}")
    genesis_hash, _ = try_rpc(url, "chain_getBlockHash", [0])
    if genesis_hash:
        print(f"{'genesis hash':<14}: {genesis_hash}")
    header, _ = try_rpc(url, "chain_getHeader")
    best = int(header["number"], 16) if isinstance(header, dict) and "number" in header else None
    if best is not None:
        print(f"{'best block':<14}: {best}")
    health, _ = try_rpc(url, "system_health")
    if isinstance(health, dict):
        print(f"{'health':<14}: peers={health.get('peers')} syncing={health.get('isSyncing')}")
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evm_url", nargs="?", default=DEFAULT_EVM)
    parser.add_argument("--blocks", type=int, default=30)
    parser.add_argument("--substrate-http", default=DEFAULT_SUBSTRATE_HTTP)
    parser.add_argument("--no-substrate", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.blocks <= 200:
        print("--blocks must be between 1 and 200")
        return 2
    code, evm_height = inspect_evm(args.evm_url, args.blocks)
    if not args.no_substrate:
        substrate_height = inspect_substrate(args.substrate_http)
        if evm_height is not None and substrate_height is not None and abs(evm_height - substrate_height) > 1000:
            print(f"\nWARNING: the EVM RPC reports block {evm_height} but the Substrate node reports {substrate_height}.")
            print("These may be DIFFERENT networks. Do not assume transactions sent through one appear on the other.")
    return code


if __name__ == "__main__":
    sys.exit(main())
