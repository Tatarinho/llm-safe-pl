"""Rough throughput benchmark: docs/second through Shield.anonymize.

Generates a synthetic document with realistic Polish PII density, runs
Shield.anonymize over it N times, reports docs/second and bytes/second.

Run: python benchmarks/throughput.py [--iterations N] [--size BYTES]

Not a scientific benchmark — numbers depend on machine, Python version, and
cache state. Use as a relative baseline for regression detection, not for
marketing claims.
"""

from __future__ import annotations

import argparse
import time

from llm_safe_pl import Shield

SAMPLE_DOCUMENT_BLOCK = """
Klient: Anna Nowak
PESEL: 44051401359
NIP: 526-000-12-46
REGON: 123456785
Tel: +48 600 123 456
Email: anna@example.pl
Karta: 4532 0151 1283 0366
Konto: PL61109010140000071219812874

Klient: Piotr Kowalski
PESEL: 92010100003
NIP: 7272445205
Tel: 600 987 654
Email: piotr@example.com
"""


def _make_document(target_bytes: int) -> str:
    block_bytes = len(SAMPLE_DOCUMENT_BLOCK.encode("utf-8"))
    repetitions = max(1, target_bytes // block_bytes)
    return SAMPLE_DOCUMENT_BLOCK * repetitions


def benchmark(iterations: int, size_bytes: int) -> None:
    document = _make_document(size_bytes)
    actual_bytes = len(document.encode("utf-8"))

    # Warm up so import/JIT-ish costs don't skew the first iteration.
    shield = Shield()
    shield.anonymize(document)

    start = time.perf_counter()
    for _ in range(iterations):
        fresh_shield = Shield()  # fresh mapping each iteration
        fresh_shield.anonymize(document)
    elapsed = time.perf_counter() - start

    docs_per_sec = iterations / elapsed
    bytes_per_sec = (iterations * actual_bytes) / elapsed
    mb_per_sec = bytes_per_sec / (1024 * 1024)

    print(f"Document size:        {actual_bytes:>10,d} bytes")
    print(f"Iterations:           {iterations:>10,d}")
    print(f"Total time:           {elapsed:>10.3f} s")
    print(f"Throughput (docs):    {docs_per_sec:>10.1f} docs/s")
    print(f"Throughput (bytes):   {mb_per_sec:>10.2f} MiB/s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iterations",
        type=int,
        default=200,
        help="Number of anonymize() calls to time (default: 200).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=16 * 1024,
        help="Target document size in bytes (default: 16384).",
    )
    args = parser.parse_args()
    benchmark(iterations=args.iterations, size_bytes=args.size)


if __name__ == "__main__":
    main()
