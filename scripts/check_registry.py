"""Read-only check of a deployed SentinelEvidenceRegistry.

Usage:
  python scripts/check_registry.py 0xContractAddress [--incident 0xID --hash 0xHASH]

Shows whether code exists at the address, the owner, how many records exist, and (optionally) whether a given
incident id and evidence hash are recorded. Sends nothing, signs nothing. Standard library only.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request

EVM_RPC = "https://test-evm-rpc-v3.portaldot.dev"
UA = "portal-sentinel-check/0.1 (read-only JSON-RPC health check)"
OWNER, TOTAL, VERIFY, GET = "0x8da5cb5b", "0x125f8974", "0x4e8fee00", "0x8eaa6ac0"  # see contracts/selectors.json


def rpc(url: str, method: str, params: list):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(request, timeout=15) as response:
        body = json.loads(response.read())
    if "error" in body:
        raise RuntimeError(body["error"].get("message", str(body["error"])))
    return body["result"]


def eth_call(url: str, to: str, data: str) -> bytes:
    return bytes.fromhex(rpc(url, "eth_call", [{"to": to, "data": data}, "latest"])[2:])


def word(value: str) -> str:
    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
        raise ValueError("expected a 32-byte hex value (0x and 64 hex characters)")
    return value[2:].lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    parser.add_argument("--rpc", default=EVM_RPC)
    parser.add_argument("--incident")
    parser.add_argument("--hash")
    args = parser.parse_args()
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", args.address):
        print("error: the contract address must be 0x followed by 40 hex characters")
        return 2
    try:
        code = rpc(args.rpc, "eth_getCode", [args.address, "latest"])
        print(f"contract address : {args.address}")
        print(f"code at address  : {'yes (' + str((len(code) - 2) // 2) + ' bytes)' if code not in ('0x', '0x0') else 'NO. Nothing is deployed there.'}")
        if code in ("0x", "0x0"):
            return 1
        owner = eth_call(args.rpc, args.address, OWNER)
        total = eth_call(args.rpc, args.address, TOTAL)
        print(f"owner            : 0x{owner[-20:].hex()}")
        print(f"records stored   : {int.from_bytes(total, 'big')}")
        if args.incident and args.hash:
            ok = eth_call(args.rpc, args.address, VERIFY + word(args.incident) + word(args.hash))
            print(f"verify(id, hash) : {int.from_bytes(ok, 'big') == 1}")
            record = eth_call(args.rpc, args.address, GET + word(args.incident)) if int.from_bytes(ok, "big") == 1 else b""
            if len(record) == 128:
                print(f"  stored hash    : 0x{record[0:32].hex()}")
                print(f"  risk score     : {int.from_bytes(record[32:64], 'big')}")
                print(f"  recorded at    : {int.from_bytes(record[64:96], 'big')} (unix time)")
                print(f"  recorded by    : 0x{record[108:128].hex()}")
        elif args.incident or args.hash:
            print("give both --incident and --hash to check a record")
    except (urllib.error.URLError, OSError, RuntimeError, ValueError) as exc:
        print(f"FAIL: {getattr(exc, 'reason', exc)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
