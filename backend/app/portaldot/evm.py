"""Read-only Ethereum JSON-RPC calls against the Portaldot EVM endpoint."""
from app.portaldot.rpc import JsonRpcClient


class EvmClient:
    def __init__(self, rpc: JsonRpcClient):
        self.rpc = rpc

    def chain_id(self) -> int:
        return int(self.rpc.call("eth_chainId"), 16)

    def balance(self, address: str) -> int:
        return int(self.rpc.call("eth_getBalance", [address, "latest"]), 16)

    def call(self, to: str, data: str) -> str:
        return self.rpc.call("eth_call", [{"to": to, "data": data}, "latest"])

    def receipt(self, tx_hash: str) -> dict | None:
        return self.rpc.call("eth_getTransactionReceipt", [tx_hash])
