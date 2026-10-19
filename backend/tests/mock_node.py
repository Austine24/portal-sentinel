"""A configurable fake Substrate node for tests. Speaks the same JSON-RPC the real one does."""
import json
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def babe_log(variant: int, author: int, slot: int, extra: int = 0) -> str:
    payload = bytes([variant]) + author.to_bytes(4, "little") + slot.to_bytes(8, "little") + bytes(extra)
    length = len(payload)
    compact = bytes([length << 2]) if length < 64 else ((length << 2) | 1).to_bytes(2, "little")
    return "0x" + (bytes([6]) + b"BABE" + compact + payload).hex()


class MockChain:
    def __init__(self, best=1000, finalized=997, authors=(0, 1), gaps=(), batch=True, reverse_batches=False,
                 peers=7, fail_status=None, health_enabled=True, header_error=False, age_seconds=12):
        self.best, self.finalized, self.authors = best, finalized, tuple(authors)
        self.gaps = set(gaps)          # block numbers preceded by one empty slot
        self.batch, self.reverse_batches = batch, reverse_batches
        self.peers, self.fail_status = peers, fail_status
        self.health_enabled, self.header_error = health_enabled, header_error
        self.calls: Counter = Counter()
        self.http_requests = 0
        self.last_user_agent = None
        self.now_ts = time.time()
        total_gaps = len([g for g in self.gaps if g <= best])
        self.base_slot = int((self.now_ts - age_seconds) // 6) - best - total_gaps

    def slot_for(self, number: int) -> int:
        return self.base_slot + number + len([g for g in self.gaps if g <= number])

    def header(self, number: int) -> dict:
        return {"number": hex(number),
                "digest": {"logs": [babe_log(2, self.authors[number % len(self.authors)], self.slot_for(number))]}}

    def handle(self, request: dict) -> dict:
        method, params = request["method"], request.get("params", [])
        self.calls[method] += 1
        reply = {"jsonrpc": "2.0", "id": request.get("id", 1)}
        if method == "chain_getHeader":
            if self.header_error:
                return {**reply, "error": {"code": -1, "message": "internal node error"}}
            number = self.best if not params else int(str(params[0]).removeprefix("0xhash"))
            return {**reply, "result": self.header(number)}
        if method == "chain_getFinalizedHead":
            return {**reply, "result": f"0xhash{self.finalized}"}
        if method == "chain_getBlockHash":
            return {**reply, "result": f"0xhash{params[0]}"}
        if method == "system_chain":
            return {**reply, "result": "Mock Testnet"}
        if method == "system_health" and self.health_enabled:
            return {**reply, "result": {"peers": self.peers, "isSyncing": False}}
        return {**reply, "error": {"code": -32601, "message": "Method not found"}}


def start(chain: MockChain):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            chain.http_requests += 1
            chain.last_user_agent = self.headers.get("User-Agent")
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if chain.fail_status:
                self.send_response(chain.fail_status)
                self.end_headers()
                self.wfile.write(b"error code: 1010")
                return
            if isinstance(body, list):
                if not chain.batch:
                    out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "batch not supported"}}
                else:
                    out = [chain.handle(item) for item in body]
                    if chain.reverse_batches:
                        out.reverse()
            else:
                out = chain.handle(body)
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}", server.shutdown
