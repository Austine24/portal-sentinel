"""Independently recompute the hash of a Portal Sentinel evidence package.

Standard library only; it does not import any Portal Sentinel code.
Usage:  python scripts/verify_evidence.py evidence.json [expected_hash]
Prints the hash. With expected_hash, exits 0 on match and 1 on mismatch.
"""
import hashlib
import json
import sys


def normalize(value, depth=0):
    if depth > 8:
        raise ValueError("nested too deeply")
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, dict):
        return {str(k): normalize(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v, depth + 1) for v in value]
    raise TypeError(f"unsupported value: {type(value).__name__}")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/verify_evidence.py evidence.json [expected_hash]")
        return 2
    with open(sys.argv[1], encoding="utf-8") as handle:
        document = json.load(handle)
    package = document.get("package", document)  # accepts the API response or the bare package
    data = json.dumps(normalize(package), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    digest = "0x" + hashlib.sha256(data).hexdigest()
    print(digest)
    if len(sys.argv) > 2:
        match = digest.lower() == sys.argv[2].lower()
        print("MATCH" if match else "MISMATCH")
        return 0 if match else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
