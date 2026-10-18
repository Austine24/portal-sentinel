"""Tests for scripts/probe_substrate.py (standard-library read-only probe)."""
import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "probe_substrate.py"
spec = importlib.util.spec_from_file_location("probe_substrate", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

ALICE = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"  # public well-known test address
ALICE_KEY = (
    "0x26aa394eea5630e07c48ae0c9558cef7b99d880ec681799c0cf30e8886371da9"
    "de1e86a9a8c739864cf3cc5ec2bea59fd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d"
)


# ---- hashing and keys -----------------------------------------------------

@pytest.mark.parametrize("data, seed0, seed1", [
    (b"", 0xef46db3751d8e999, 0xd5afba1336a3be4b),
    (b"abc", 0x44bc2cf5ad770999, 0xbea9ca8199328908),
    (b"System", 0xe03056ea4e39aa26, 0xf7ce58950cae487c),
    (b"x" * 100, 0x92f0de5a88a3c094, 0xa27aec103fa2bdae),
])
def test_xxh64_matches_reference_values(data, seed0, seed1):
    assert probe.xxh64(data, 0) == seed0
    assert probe.xxh64(data, 1) == seed1


def test_system_storage_prefix_is_the_famous_one():
    assert probe.twox128(b"System").hex() == "26aa394eea5630e07c48ae0c9558cef7"


def test_account_storage_key_matches_published_value():
    assert probe.account_storage_key(probe.ss58_decode(ALICE)) == ALICE_KEY


# ---- addresses ------------------------------------------------------------

def test_ss58_decodes_the_public_key():
    assert probe.ss58_decode(ALICE).hex() == "d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d"


def test_ss58_rejects_a_typo():
    typo = ALICE[:-1] + ("a" if ALICE[-1] != "a" else "b")
    with pytest.raises(ValueError, match="typo|base58|standard"):
        probe.ss58_decode(typo)


def test_ss58_rejects_garbage():
    with pytest.raises(ValueError):
        probe.ss58_decode("0xDEADBEEF")


# ---- balances -------------------------------------------------------------

def account_record(free: int) -> str:
    raw = (b"\x01\x00\x00\x00" * 4) + free.to_bytes(16, "little") + bytes(48)
    return "0x" + raw.hex()


def test_free_balance_decoding():
    assert probe.decode_free_balance(account_record(12_5 * 10**13)) == 125 * 10**13
    assert probe.decode_free_balance(None) == 0


def test_short_account_record_is_refused():
    with pytest.raises(ValueError):
        probe.decode_free_balance("0x0102")


# ---- block headers --------------------------------------------------------

def babe_log(variant: int, author: int, slot: int, extra: int = 0) -> str:
    payload = bytes([variant]) + author.to_bytes(4, "little") + slot.to_bytes(8, "little") + bytes(extra)
    length = len(payload)
    compact = bytes([length << 2]) if length < 64 else ((length << 2) | 1).to_bytes(2, "little")
    return "0x" + (bytes([6]) + b"BABE" + compact + payload).hex()


def test_decodes_babe_secondary_digest():
    info = probe.decode_author([babe_log(2, author=3, slot=123456)])
    assert info == {"engine": "BABE", "author_index": 3, "slot": 123456}


def test_decodes_babe_primary_digest_with_long_vrf_payload():
    info = probe.decode_author([babe_log(1, author=1, slot=99, extra=96)])   # length needs 2-byte compact
    assert info["author_index"] == 1 and info["slot"] == 99


def test_decodes_aura_digest_without_author_index():
    payload = (777).to_bytes(8, "little")
    log = "0x" + (bytes([6]) + b"aura" + bytes([len(payload) << 2]) + payload).hex()
    assert probe.decode_author([log]) == {"engine": "aura", "author_index": None, "slot": 777}


def test_ignores_other_digest_items_and_survives_unknown_engines():
    seal = "0x05" + "42414245" + "00"
    assert probe.decode_author([seal])["engine"] is None
    unknown = "0x06" + b"ZZZZ".hex() + "04" + "ff"
    assert probe.decode_author([unknown])["author_index"] is None


# ---- end to end against a mock node ---------------------------------------

BEST, FINALIZED = 1000, 998
AUTHORS = [0, 0, 0, 1]            # author 0 produces 3 of every 4 blocks
BALANCE_UNITS = 12 * 10**14 + 5 * 10**13   # 12.5 tPOT


class MockNode(BaseHTTPRequestHandler):
    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        method, params = request["method"], request.get("params", [])
        if method == "chain_getFinalizedHead":
            result = f"0xhash{FINALIZED}"
        elif method == "chain_getBlockHash":
            result = f"0xhash{params[0]}"
        elif method == "chain_getHeader":
            number = BEST if not params else int(params[0].removeprefix("0xhash"))
            result = {"number": hex(number),
                      "digest": {"logs": [babe_log(2, AUTHORS[number % 4], number * 3)]}}
        elif method == "system_chain":
            result = "Mock Testnet"
        elif method == "state_getStorage":
            result = account_record(BALANCE_UNITS) if params[0] == ALICE_KEY else None
        else:
            self._reply({"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "no such method"}})
            return
        self._reply({"jsonrpc": "2.0", "id": 1, "result": result})

    def _reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture()
def node_url():
    server = HTTPServer(("127.0.0.1", 0), MockNode)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def run_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["probe_substrate.py", *args])
    code = probe.main()
    return code, capsys.readouterr().out


def test_cli_reports_finality_authors_and_balance(node_url, monkeypatch, capsys):
    code, out = run_cli(monkeypatch, capsys, "--url", node_url, "--blocks", "20", "--balance", ALICE)
    assert code == 0
    assert "finality lag 2 blocks" in out
    assert "engine(s): {'BABE': 20}" in out
    assert "distinct block authors    : 2" in out
    assert "free balance" in out and "12.5000 tPOT" in out


def test_cli_reports_zero_for_unknown_account(node_url, monkeypatch, capsys):
    other = "5HbvLqQAFhBx21ijKxB8X4XdFXJzQASvjTgCe5WTjzhmUeAD"
    code, out = run_cli(monkeypatch, capsys, "--url", node_url, "--blocks", "3", "--balance", other)
    assert code == 0 and "0.0000 tPOT" in out


def test_cli_rejects_a_mistyped_address(node_url, monkeypatch, capsys):
    code, out = run_cli(monkeypatch, capsys, "--url", node_url, "--blocks", "2", "--balance", ALICE[:-1] + "x")
    assert code == 1 and "balance check:" in out


def test_cli_fails_cleanly_when_the_node_is_unreachable(monkeypatch, capsys):
    code, out = run_cli(monkeypatch, capsys, "--url", "http://127.0.0.1:9", "--blocks", "2")
    assert code == 1 and out.startswith("FAIL:")


def test_cli_rejects_bad_block_count(monkeypatch, capsys):
    code, _ = run_cli(monkeypatch, capsys, "--blocks", "0")
    assert code == 2
