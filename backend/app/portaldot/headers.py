"""Reading block production details out of a Substrate block header.

Confirmed on the live Portaldot testnet (2026-10-18): the engine is BABE, each header carries
the author's index in the validator set and a slot number that rises by 1 per block.
"""
from typing import TypedDict

# A slot is 6 seconds on this chain: the average block time is 6.000 s and a block's slot
# times 6 s matched wall-clock time within minutes. This is DERIVED, not read from the runtime.
SLOT_DURATION_S = 6

_PRE_RUNTIME = 6  # SCALE discriminant of a pre-runtime digest item


class BlockProduction(TypedDict):
    engine: str | None
    author_index: int | None
    slot: int | None


def _compact(data: bytes, at: int) -> tuple[int, int]:
    mode = data[at] & 3
    if mode == 0:
        return data[at] >> 2, at + 1
    if mode == 1:
        return int.from_bytes(data[at:at + 2], "little") >> 2, at + 2
    if mode == 2:
        return int.from_bytes(data[at:at + 4], "little") >> 2, at + 4
    raise ValueError("compact integer too large")


def decode_block_production(logs: list[str]) -> BlockProduction:
    for log in logs:
        raw = bytes.fromhex(log[2:])
        if not raw or raw[0] != _PRE_RUNTIME:
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


def slot_time(slot: int) -> int:
    """Derived unix time of a slot, in seconds."""
    return slot * SLOT_DURATION_S
