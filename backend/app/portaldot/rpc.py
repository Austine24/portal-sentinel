"""Minimal read-only JSON-RPC client for a Portaldot (Substrate) node over HTTPS.

Standard library only. Always sends a descriptive User-Agent, because the public RPC
sits behind Cloudflare and rejects Python's default one. Never signs or sends transactions.
"""
import json
import urllib.error
import urllib.request

USER_AGENT = "portal-sentinel/0.1 (read-only monitoring)"


class RpcError(Exception):
    """The node answered, but with a JSON-RPC error."""


class RpcUnavailable(Exception):
    """The node could not be reached, timed out, or refused the request (for example HTTP 403)."""


class JsonRpcClient:
    def __init__(self, url: str, timeout: float = 10.0, user_agent: str = USER_AGENT, max_batch: int = 50):
        self.url = url
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_batch = max_batch

    def _post(self, payload):
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "User-Agent": self.user_agent},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raise RpcUnavailable(f"HTTP {exc.code}") from exc
        except (OSError, ValueError) as exc:  # includes timeouts, refused connections, bad JSON
            raise RpcUnavailable(str(getattr(exc, "reason", exc))) from exc

    def call(self, method: str, params: list | None = None):
        body = self._post({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []})
        if not isinstance(body, dict):
            raise RpcUnavailable("unexpected response shape")
        if "error" in body:
            raise RpcError(str(body["error"].get("message", body["error"])))
        return body.get("result")

    def batch(self, calls: list[tuple[str, list]], tolerate_errors: bool = False) -> list:
        """Runs many calls. Uses one HTTP request per chunk when the node supports batching,
        and falls back to one request per call when it does not. With tolerate_errors, a failed
        call yields an RpcError object in its slot instead of raising."""
        results: list = []
        for start in range(0, len(calls), self.max_batch):
            results.extend(self._chunk(calls[start:start + self.max_batch], tolerate_errors))
        return results

    def _chunk(self, chunk: list[tuple[str, list]], tolerate_errors: bool) -> list:
        payload = [{"jsonrpc": "2.0", "id": i, "method": m, "params": p} for i, (m, p) in enumerate(chunk)]
        body = None
        try:
            body = self._post(payload)
        except RpcUnavailable:
            body = None  # fall back below; a truly dead node fails again immediately

        if isinstance(body, list):
            by_id = {item.get("id"): item for item in body if isinstance(item, dict)}
            if all(i in by_id for i in range(len(chunk))):
                out = []
                for i in range(len(chunk)):
                    item = by_id[i]
                    if "error" in item:
                        error = RpcError(str(item["error"].get("message", item["error"])))
                        if not tolerate_errors:
                            raise error
                        out.append(error)
                    else:
                        out.append(item.get("result"))
                return out

        out = []
        for method, params in chunk:
            try:
                out.append(self.call(method, params))
            except RpcError as error:
                if not tolerate_errors:
                    raise
                out.append(error)
        return out
