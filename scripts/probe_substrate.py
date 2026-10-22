"""Read-only probe of a Substrate node over HTTPS. No keys, no transactions.

Usage:
  python scripts/probe_substrate.py [--url https://test-node-v3.portaldot.dev] [--blocks 20] [--balance 5Abc...]

Shows best vs finalized block (finality lag), who produced each recent block (from the block header),
and optionally the free balance of any address (public information, no wallet needed).
Standard library only. Uses a descriptive User-Agent, because the public RPC rejects Python's default one.
"""
import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from collections import Counter

UA = "portal-sentinel-check/0.1 (read-only JSON-RPC health check)"
DEFAULT_URL = "https://test-node-v3.portaldot.dev"
DECIMALS = 14  # POT, confirmed by the node (tokenDecimals) and the console

# ---------------------------------------------------------------- hashing (needed to build storage keys)
_M = (1 << 64) - 1
_P1, _P2, _P3, _P4, _P5 = (
    11400714785074694791, 14029467366897019727, 1609587929392839161,
    9650029242287828579, 2870177450012600261,
)


def _rotl(x, r):
    return ((x << r) | (x >> (64 - r))) & _M


def _round(acc, value):
    return (_rotl((acc + value * _P2) & _M, 31) * _P1) & _M


def _merge(acc, value):
    return (((acc ^ _round(0, value)) * _P1) + _P4) & _M


def xxh64(data: bytes, seed: int = 0) -> int:
    """XXH64, implemented here so the script needs no packages. Checked against the reference library in tests."""
    n, i = len(data), 0
    u64 = lambda at: int.from_bytes(data[at:at + 8], "little")  # noqa: E731
    if n >= 32:
        v1, v2, v3, v4 = (seed + _P1 + _P2) & _M, (seed + _P2) & _M, seed & _M, (seed - _P1) & _M
        while i <= n - 32:
            v1, v2 = _round(v1, u64(i)), _round(v2, u64(i + 8))
            v3, v4 = _round(v3, u64(i + 16)), _round(v4, u64(i + 24))
            i += 32
        h = (_rotl(v1, 1) + _rotl(v2, 7) + _rotl(v3, 12) + _rotl(v4, 18)) & _M
        for v in (v1, v2, v3, v4):
            h = _merge(h, v)
    else:
        h = (seed + _P5) & _M
    h = (h + n) & _M
    while i <= n - 8:
        h = (_rotl(h ^ _round(0, u64(i)), 27) * _P1 + _P4) & _M
        i += 8
    if i <= n - 4:
        h = (_rotl(h ^ ((int.from_bytes(data[i:i + 4], "little") * _P1) & _M), 23) * _P2 + _P3) & _M
        i += 4
    while i < n:
        h = (_rotl(h ^ ((data[i] * _P5) & _M), 11) * _P1) & _M
        i += 1
    h ^= h >> 33
    h = (h * _P2) & _M
    h ^= h >> 29
    h = (h * _P3) & _M
    h ^= h >> 32
    return h


def twox128(data: bytes) -> bytes:
    return xxh64(data, 0).to_bytes(8, "little") + xxh64(data, 1).to_bytes(8, "little")


# ---------------------------------------------------------------- addresses
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def ss58_decode(address: str) -> bytes:
    """Returns the 32-byte public key, or raises ValueError for a mistyped address."""
    try:
        number = 0
        for ch in address:
            number = number * 58 + _B58.index(ch)
    except ValueError:
        raise ValueError("address contains characters that are not valid base58") from None
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    data = b"\x00" * (len(address) - len(address.lstrip("1"))) + raw
    if len(data) != 35 or data[0] >= 64:
        raise ValueError("not a standard single-byte-prefix SS58 address")
    prefix, key, checksum = data[:1], data[1:33], data[33:]
    if hashlib.blake2b(b"SS58PRE" + prefix + key, digest_size=64).digest()[:2] != checksum:
        raise ValueError("checksum does not match; the address has a typo")
    return key


def ss58_encode(pubkey: bytes, prefix: int = 42) -> str:
    """The reverse of ss58_decode: a 32-byte public key to a readable address."""
    if len(pubkey) != 32 or not 0 <= prefix < 64:
        raise ValueError("expected a 32-byte key and a one-byte prefix")
    body = bytes([prefix]) + pubkey
    data = body + hashlib.blake2b(b"SS58PRE" + body, digest_size=64).digest()[:2]
    number = int.from_bytes(data, "big")
    out = ""
    while number:
        number, remainder = divmod(number, 58)
        out = _B58[remainder] + out
    return "1" * (len(data) - len(data.lstrip(b"\x00"))) + out


def account_storage_key(pubkey: bytes) -> str:
    """System.Account(pubkey) as a hex storage key."""
    return "0x" + (
        twox128(b"System") + twox128(b"Account") + hashlib.blake2b(pubkey, digest_size=16).digest() + pubkey
    ).hex()


def decode_free_balance(value_hex: str | None) -> int:
    """Free balance in the smallest unit from a System.Account value (nonce, consumers, providers,
    sufficients as four u32, then free as a u128)."""
    if value_hex is None:
        return 0
    raw = bytes.fromhex(value_hex[2:])
    if len(raw) < 32:
        raise ValueError("unexpected account record length")
    return int.from_bytes(raw[16:32], "little")


# ---------------------------------------------------------------- block headers
def _compact(data: bytes, at: int) -> tuple[int, int]:
    mode = data[at] & 3
    if mode == 0:
        return data[at] >> 2, at + 1
    if mode == 1:
        return int.from_bytes(data[at:at + 2], "little") >> 2, at + 2
    if mode == 2:
        return int.from_bytes(data[at:at + 4], "little") >> 2, at + 4
    raise ValueError("compact integer too large")


def decode_author(logs: list[str]) -> dict:
    """Finds the block-production pre-runtime digest and reads the slot and, for BABE, the author index."""
    for log in logs:
        raw = bytes.fromhex(log[2:])
        if not raw or raw[0] != 6:                      # 6 = pre-runtime digest item
            continue
        engine = raw[1:5].decode("ascii", "replace")
        length, at = _compact(raw, 5)
        payload = raw[at:at + length]
        if engine == "BABE" and len(payload) >= 13 and payload[0] in (1, 2, 3):
            return {
                "engine": engine,
                "author_index": int.from_bytes(payload[1:5], "little"),
                "slot": int.from_bytes(payload[5:13], "little"),
            }
        if engine.lower() == "aura" and len(payload) == 8:
            return {"engine": engine, "author_index": None, "slot": int.from_bytes(payload, "little")}
        return {"engine": engine, "author_index": None, "slot": None}
    return {"engine": None, "author_index": None, "slot": None}


# ---------------------------------------------------------------- JSON-RPC
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


def header_at(url: str, number: int) -> dict:
    block_hash = rpc(url, "chain_getBlockHash", [number])
    header = rpc(url, "chain_getHeader", [block_hash])
    header["_hash"] = block_hash
    return header


def free_balance(url: str, address: str) -> int:
    key = account_storage_key(ss58_decode(address))
    return decode_free_balance(rpc(url, "state_getStorage", [key]))


# ---------------------------------------------------------------- command line
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--blocks", type=int, default=20)
    parser.add_argument("--balance", metavar="ADDRESS")
    args = parser.parse_args()
    if not 1 <= args.blocks <= 100:
        print("--blocks must be between 1 and 100")
        return 2

    try:
        best_header = rpc(args.url, "chain_getHeader")
        best = int(best_header["number"], 16)
        finalized_header = rpc(args.url, "chain_getHeader", [rpc(args.url, "chain_getFinalizedHead")])
        finalized = int(finalized_header["number"], 16)
        print(f"node          : {args.url}")
        print(f"chain         : {rpc(args.url, 'system_chain')}")
        print(f"best block    : {best}")
        print(f"finalized     : {finalized}   (finality lag {best - finalized} blocks)")

        authors, engines = Counter(), Counter()
        print(f"\nlast {args.blocks} blocks, newest first:")
        for number in range(best, best - args.blocks, -1):
            info = decode_author(header_at(args.url, number)["digest"]["logs"])
            engines[info["engine"]] += 1
            authors[info["author_index"]] += 1
            print(f"  #{number}  engine={info['engine']}  author_index={info['author_index']}  slot={info['slot']}")

        print(f"\nblock production engine(s): {dict(engines)}")
        known = {k: v for k, v in authors.items() if k is not None}
        if known:
            top_index, top_count = max(known.items(), key=lambda kv: kv[1])
            print(f"distinct block authors    : {len(known)} in the last {args.blocks} blocks")
            print(f"most active author index  : {top_index} produced {top_count} of {args.blocks} ({100 * top_count / args.blocks:.0f}%)")
            print("(a short sample; do not over-read it)")
        else:
            print("author index not available for this engine")

        if args.balance:
            try:
                amount = free_balance(args.url, args.balance)
            except ValueError as exc:
                print(f"\nbalance check: {exc}")
                return 1
            print(f"\nfree balance of {args.balance}: {amount / 10 ** DECIMALS:.4f} tPOT ({amount} smallest units)")
            if amount == 0:
                print("(zero, or the account has never been used on this chain)")
    except urllib.error.HTTPError as exc:
        print(f"FAIL: server answered HTTP {exc.code}")
        return 1
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"FAIL: {getattr(exc, 'reason', exc)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
