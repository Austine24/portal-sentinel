"""Tests for scripts/evm_funding_address.py, scripts/check_registry.py and the SS58 encoder."""
import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from app.portaldot import registry

ROOT = Path(__file__).resolve().parents[2]
FIX = json.loads((ROOT / "contracts" / "fixtures" / "registry_fixtures.json").read_text())


def load(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


probe = load("probe_substrate")
funding = load("evm_funding_address")
check = load("check_registry")

ALICE = "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"
DEPLOYER = "0x" + "12" * 20


# ---- SS58 encoding ---------------------------------------------------------

def test_ss58_encode_is_the_inverse_of_decode():
    assert probe.ss58_encode(probe.ss58_decode(ALICE)) == ALICE
    for seed in range(40):
        key = bytes((seed * 7 + i * 13) % 256 for i in range(32))
        assert probe.ss58_decode(probe.ss58_encode(key)) == key


@pytest.mark.parametrize("prefix", [0, 2, 42, 63])
def test_ss58_encode_honours_the_prefix(prefix):
    key = bytes(range(32))
    address = probe.ss58_encode(key, prefix)
    assert probe.ss58_decode(address) == key


def test_ss58_encode_refuses_bad_input():
    with pytest.raises(ValueError):
        probe.ss58_encode(b"short")
    with pytest.raises(ValueError):
        probe.ss58_encode(bytes(32), 64)


# ---- fallback account -------------------------------------------------------

def test_fallback_account_is_the_address_followed_by_twelve_ee_bytes():
    account = funding.fallback_account(DEPLOYER)
    assert len(account) == 32 and account[:20] == bytes.fromhex("12" * 20) and account[20:] == b"\xee" * 12


@pytest.mark.parametrize("bad", ["0x1234", "12" * 20, "0x" + "zz" * 20, ""])
def test_fallback_account_rejects_malformed_addresses(bad):
    with pytest.raises(ValueError):
        funding.fallback_account(bad)


# ---- a tiny JSON-RPC server for the --check paths ----------------------------

def serve(handler):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = {"jsonrpc": "2.0", "id": body.get("id", 1), "result": handler(body["method"], body.get("params", []))}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}", server.shutdown


def account_record(units: int) -> str:
    return "0x" + (b"\x01\x00\x00\x00" * 4 + units.to_bytes(16, "little") + bytes(48)).hex()


def run(module, monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", [module.__name__, *argv])
    code = module.main()
    return code, capsys.readouterr().out


# ---- funding script ---------------------------------------------------------

def test_funding_script_prints_the_address_that_decodes_to_the_fallback_account(monkeypatch, capsys):
    code, out = run(funding, monkeypatch, capsys, DEPLOYER)
    assert code == 0
    printed = next(line for line in out.splitlines() if line.startswith("Send tPOT")).split(": ")[1]
    assert printed.startswith("5") and probe.ss58_decode(printed) == funding.fallback_account(DEPLOYER)


def test_funding_script_rejects_a_bad_address(monkeypatch, capsys):
    code, out = run(funding, monkeypatch, capsys, "0xnope")
    assert code == 2 and out.startswith("error:")


@pytest.mark.parametrize("substrate_units, evm_wei, expected", [
    (5 * 10**14, 5 * 10**18, "both views see funds"),
    (5 * 10**14, 0, "Substrate sees the funds but the Ethereum RPC does not"),
    (0, 0, "no funds seen yet"),
])
def test_funding_check_reports_each_outcome(monkeypatch, capsys, substrate_units, evm_wei, expected):
    url, stop = serve(lambda m, p: {"state_getStorage": account_record(substrate_units) if substrate_units else None,
                                    "eth_getBalance": hex(evm_wei)}[m])
    monkeypatch.setattr(funding, "EVM_RPC", url)
    monkeypatch.setattr(funding, "SUBSTRATE_HTTP", url)
    try:
        code, out = run(funding, monkeypatch, capsys, DEPLOYER, "--check")
    finally:
        stop()
    assert code == 0 and expected in out


def test_funding_check_fails_cleanly_when_the_node_is_down(monkeypatch, capsys):
    monkeypatch.setattr(funding, "EVM_RPC", "http://127.0.0.1:9")
    monkeypatch.setattr(funding, "SUBSTRATE_HTTP", "http://127.0.0.1:9")
    code, out = run(funding, monkeypatch, capsys, DEPLOYER, "--check")
    assert code == 1 and "check failed" in out


# ---- registry checker (answers replayed from REAL EVM output) ----------------

ID, HASH = FIX["incident_id"], FIX["evidence_hash"]


def evm_handler(has_code=True):
    answers = {
        registry.SELECTORS["owner"]: FIX["calls"]["owner"],
        registry.SELECTORS["totalRecords"]: FIX["calls"]["total"],
        registry.encode_verify(ID, HASH): FIX["calls"]["verify_true"],
        FIX["calldata"]["get"]: FIX["calls"]["get"],
    }

    def handle(method, params):
        if method == "eth_getCode":
            return "0x6080604052" if has_code else "0x"
        if method == "eth_call":
            return answers.get(params[0]["data"], FIX["calls"]["verify_wrong_hash"])
        raise AssertionError(method)

    return handle


def test_registry_check_shows_owner_count_and_a_verified_record(monkeypatch, capsys):
    url, stop = serve(evm_handler())
    try:
        code, out = run(check, monkeypatch, capsys, FIX["contract_address"], "--rpc", url, "--incident", ID, "--hash", HASH)
    finally:
        stop()
    assert code == 0
    assert FIX["owner"].lower() in out.lower() and "records stored   : 1" in out
    assert "verify(id, hash) : True" in out and "risk score     : 96" in out and HASH in out


def test_registry_check_reports_false_for_a_wrong_hash(monkeypatch, capsys):
    url, stop = serve(evm_handler())
    try:
        code, out = run(check, monkeypatch, capsys, FIX["contract_address"], "--rpc", url, "--incident", ID, "--hash", "0x" + "ab" * 32)
    finally:
        stop()
    assert code == 0 and "verify(id, hash) : False" in out and "stored hash" not in out


def test_registry_check_says_so_when_nothing_is_deployed(monkeypatch, capsys):
    url, stop = serve(evm_handler(has_code=False))
    try:
        code, out = run(check, monkeypatch, capsys, FIX["contract_address"], "--rpc", url)
    finally:
        stop()
    assert code == 1 and "Nothing is deployed there" in out


def test_registry_check_validates_its_inputs(monkeypatch, capsys):
    assert run(check, monkeypatch, capsys, "0x1234")[0] == 2
    url, stop = serve(evm_handler())
    try:
        code, out = run(check, monkeypatch, capsys, FIX["contract_address"], "--rpc", url, "--incident", "0x12", "--hash", HASH)
    finally:
        stop()
    assert code == 1 and "32-byte" in out


def test_registry_check_constants_match_the_compiled_contract():
    selectors = json.loads((ROOT / "contracts" / "selectors.json").read_text())["functions"]
    assert (check.OWNER, check.TOTAL, check.VERIFY, check.GET) == tuple(
        selectors[n]["selector"] for n in ("owner", "totalRecords", "verify", "get"))
