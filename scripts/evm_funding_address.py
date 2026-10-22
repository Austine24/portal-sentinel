"""Works out which Substrate account holds the funds of an Ethereum-style (0x) address, and checks both views.

Usage:
  python scripts/evm_funding_address.py 0xYourDeployerAddress [--check]

On chains built on pallet-revive, an 0x address that has never been mapped lives in a "fallback" account:
its 20 bytes followed by twelve 0xEE bytes. Sending tPOT to that account's normal (5...) address funds the 0x address.
THIS IS GENERAL pallet-revive BEHAVIOUR AND IS NOT YET CONFIRMED FOR PORTALDOT. That is what --check is for:
after a small test transfer it reads the balance through BOTH the Ethereum RPC and the Substrate node.
Read-only. Never asks for a key or phrase.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_substrate as chain  # noqa: E402

EVM_RPC = "https://test-evm-rpc-v3.portaldot.dev"
SUBSTRATE_HTTP = "https://test-node-v3.portaldot.dev"
PADDING = b"\xee" * 12


def fallback_account(evm_address: str) -> bytes:
    """The 32-byte account id that owns an unmapped Ethereum address."""
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", evm_address):
        raise ValueError("expected an address like 0x followed by 40 hex characters")
    return bytes.fromhex(evm_address[2:]) + PADDING


def evm_balance(url: str, evm_address: str) -> int:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [evm_address, "latest"]}).encode()
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": chain.UA})
    with urllib.request.urlopen(request, timeout=15) as response:
        body = json.loads(response.read())
    if "error" in body:
        raise RuntimeError(body["error"].get("message", str(body["error"])))
    return int(body["result"], 16)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evm_address")
    parser.add_argument("--check", action="store_true", help="read the balance through both the EVM and Substrate RPCs")
    args = parser.parse_args()

    try:
        account = fallback_account(args.evm_address)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    ss58 = chain.ss58_encode(account, 42)

    print(f"Ethereum address              : {args.evm_address}")
    print(f"Fallback account (hex)        : 0x{account.hex()}")
    print(f"Send tPOT to this 5... address: {ss58}")
    print()
    print("Start with a SMALL test amount (for example 5 tPOT), then run this again with --check.")
    print("If the EVM balance below stays zero after the transfer, STOP and do not send more:")
    print("the 0xEE assumption would be wrong for Portaldot.")

    if not args.check:
        return 0
    print()
    try:
        substrate = chain.free_balance_of_key(SUBSTRATE_HTTP, account) if hasattr(chain, "free_balance_of_key") else None
        if substrate is None:
            key = chain.account_storage_key(account)
            substrate = chain.decode_free_balance(chain.rpc(SUBSTRATE_HTTP, "state_getStorage", [key]))
        evm = evm_balance(EVM_RPC, args.evm_address)
    except (urllib.error.URLError, OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"check failed: {getattr(exc, 'reason', exc)}")
        return 1
    print(f"Substrate view of that account: {substrate / 10 ** chain.DECIMALS:.4f} tPOT ({substrate} smallest units)")
    print(f"Ethereum RPC view (raw)       : {evm}   (the scale of this number is not confirmed)")
    if substrate > 0 and evm > 0:
        print("RESULT: both views see funds. The fallback-account assumption holds.")
    elif substrate > 0 and evm == 0:
        print("RESULT: Substrate sees the funds but the Ethereum RPC does not. Stop and report this output.")
    else:
        print("RESULT: no funds seen yet. Wait a few blocks (about 30 seconds) and check again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
