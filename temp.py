#!/usr/bin/env python3
"""
encode_for_print.py  <input-file>  [group-size]

• Reads any binary file.
• Base‑32–encodes it (A–Z, 2–7 only).
• Breaks it into fixed‑width lines (60 chars by default).
• Adds:
     1. 6‑digit line number
     2. The block itself
     3. 8‑hex‑digit CRC‑32 of the block
• After every <group-size> data lines it emits one XOR‑parity line
  that lets the decoder recover ANY ONE bad/missing line in that group.
"""

import sys, base64, zlib, textwrap, itertools, functools, operator

WIDTH        = 60          # characters per data line
GROUP_SIZE   = int(sys.argv[2]) if len(sys.argv) > 2 else 10   # 10→parity = 10 % overhead
PARITY_TAG   = "P"         # first character of parity‑line number field

def crc32(s: bytes) -> int:
    return zlib.crc32(s) & 0xffffffff

def xor_bytes(a: bytes, b: bytes) -> bytes:
    # pad shorter side
    if len(a) < len(b):
        a += b'\0' * (len(b) - len(a))
    elif len(b) < len(a):
        b += a'\0' * (len(a) - len(b))
    return bytes(x ^ y for x, y in zip(a, b))

with open(sys.argv[1], 'rb') as fh:
    raw = fh.read()

b32 = base64.b32encode(raw).decode('ascii')
blocks = textwrap.wrap(b32, WIDTH)

for group_index in range(0, len(blocks), GROUP_SIZE):
    group = blocks[group_index:group_index + GROUP_SIZE]

    # emit data lines
    for offset, blk in enumerate(group, 1):
        num = group_index + offset                    # 1‑based overall line number
        crc = crc32(blk.encode('ascii'))
        print(f"{num:06d} {blk:<{WIDTH}} {crc:08x}")

    # compute XOR parity of raw *bytes* (not the text) for the group
    raw_group = [base64.b32decode(b + '=' * (-len(b) % 8)) for b in group]
    parity = functools.reduce(xor_bytes, raw_group)
    parity_b32 = base64.b32encode(parity).decode('ascii').rstrip('=')
    crc_parity = crc32(parity_b32.encode('ascii'))
    # parity line number = 'P'+group-start to keep it unique & sortable
    print(f"{PARITY_TAG}{group_index//GROUP_SIZE:05d} {parity_b32:<{WIDTH}} {crc_parity:08x}")
