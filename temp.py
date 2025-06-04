#!/usr/bin/env python3
"""
encode_for_print.py  <input‑file>  [group‑size]

• Base‑32‑encodes any binary file (A‑Z + 2‑7 only, OCR‑friendly).
• Breaks it into WIDTH‑character lines (default 60).
• Adds
     1. 6‑digit line number
     2. the data block
     3. 8‑digit CRC‑32 of that block
• After every <group‑size> data lines it emits ONE XOR‑parity line
  that lets the decoder reconstruct any single bad/missing line
  in that group.

The default group‑size is 10 → ~10 % overhead (change it with argv 2).
"""

import sys, base64, zlib, textwrap, functools, itertools

WIDTH       = 60
GROUP_SIZE  = int(sys.argv[2]) if len(sys.argv) > 2 else 10
PARITY_TAG  = "P"          # marks the parity lines

def crc32(bs: bytes) -> int:
    return zlib.crc32(bs) & 0xffffffff

def xor_bytes(a: bytes, b: bytes) -> bytes:
    """Return byte‑wise XOR of a and b, padding the shorter with zeros."""
    max_len = max(len(a), len(b))
    a = a.ljust(max_len, b'\0')
    b = b.ljust(max_len, b'\0')
    return bytes(x ^ y for x, y in zip(a, b))

with open(sys.argv[1], 'rb') as fh:
    raw = fh.read()

b32 = base64.b32encode(raw).decode('ascii')
blocks = textwrap.wrap(b32, WIDTH)

for group_start in range(0, len(blocks), GROUP_SIZE):
    group = blocks[group_start:group_start + GROUP_SIZE]

    # 1 · emit the data lines
    for offset, blk in enumerate(group, 1):
        num = group_start + offset               # 1‑based global line number
        print(f"{num:06d} {blk:<{WIDTH}} {crc32(blk.encode()):08x}")

    # 2 · compute XOR of the RAW BYTES for the whole group
    raw_group = [base64.b32decode(b + '=' * (-len(b) % 8)) for b in group]
    parity    = functools.reduce(xor_bytes, raw_group)
    parity_b32 = base64.b32encode(parity).decode('ascii').rstrip('=')
    print(f"{PARITY_TAG}{group_start//GROUP_SIZE:05d} "
          f"{parity_b32:<{WIDTH}} {crc32(parity_b32.encode()):08x}")
