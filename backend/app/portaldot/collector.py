"""Takes one read-only snapshot of the chain's health from a Substrate node."""
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from app.domain.network import NetworkSnapshot
from app.portaldot.headers import decode_block_production, slot_time
from app.portaldot.rpc import JsonRpcClient, RpcError


@dataclass(frozen=True)
class BlockInfo:
    number: int
    author_index: int | None
    slot: int | None


class HeaderCache:
    """Remembers decoded blocks so a refresh only downloads the blocks it has not seen yet.
    Block data below the finalized head never changes, so caching is safe for it, and a
    short reorg of the newest blocks would only be re-read after they fall out of the window."""

    def __init__(self, limit: int = 500):
        self.limit = limit
        self._blocks: dict[int, BlockInfo] = {}

    def get(self, number: int) -> BlockInfo | None:
        return self._blocks.get(number)

    def put(self, info: BlockInfo) -> None:
        self._blocks[info.number] = info
        if len(self._blocks) > self.limit:
            for number in sorted(self._blocks)[: len(self._blocks) - self.limit]:
                del self._blocks[number]


def _number(header: dict) -> int:
    return int(header["number"], 16)


def _fetch_missing(client: JsonRpcClient, numbers: Sequence[int], cache: HeaderCache) -> None:
    missing = [n for n in numbers if cache.get(n) is None]
    if not missing:
        return
    hashes = client.batch([("chain_getBlockHash", [n]) for n in missing])
    headers = client.batch([("chain_getHeader", [h]) for h in hashes])
    for number, header in zip(missing, headers):
        production = decode_block_production(header["digest"]["logs"])
        cache.put(BlockInfo(number, production["author_index"], production["slot"]))


def collect_snapshot(client: JsonRpcClient, cache: HeaderCache, window: int, now: datetime) -> NetworkSnapshot:
    best_header, finalized_hash, chain_name, health = client.batch(
        [("chain_getHeader", []), ("chain_getFinalizedHead", []), ("system_chain", []), ("system_health", [])],
        tolerate_errors=True,
    )
    for essential in (best_header, finalized_hash):
        if isinstance(essential, RpcError):
            raise essential
    finalized_header = client.call("chain_getHeader", [finalized_hash])

    best, finalized = _number(best_header), _number(finalized_header)
    numbers = list(range(max(0, best - window + 1), best + 1))
    _fetch_missing(client, numbers, cache)
    blocks = [b for b in (cache.get(n) for n in numbers) if b is not None]

    slots = [b.slot for b in blocks if b.slot is not None]
    missed = sum(max(0, later - earlier - 1) for earlier, later in zip(slots, slots[1:]))

    authors: dict[str, int] = {}
    for block in blocks:
        if block.author_index is not None:
            authors[str(block.author_index)] = authors.get(str(block.author_index), 0) + 1
    produced = sum(authors.values())

    newest_slot = blocks[-1].slot if blocks else None
    block_age = max(0.0, now.timestamp() - slot_time(newest_slot)) if newest_slot is not None else None

    return NetworkSnapshot(
        taken_at=now,
        chain_name=None if isinstance(chain_name, RpcError) else chain_name,
        best_block=best,
        finalized_block=finalized,
        finality_lag=max(0, best - finalized),
        window_blocks=len(blocks),
        missed_slots=missed,
        authors=authors,
        distinct_authors=len(authors),
        max_author_share=round(max(authors.values()) / produced, 4) if produced else None,
        block_age_s=round(block_age, 1) if block_age is not None else None,
        peers=health.get("peers") if isinstance(health, dict) else None,
    )
