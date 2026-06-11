# crc32

Standard CRC-32 (the zlib/PNG/gzip checksum) of a byte buffer, computed
WITHOUT a precomputed table (table-free, bitwise or equivalent).

- **In:** RDI = pointer to buffer, RSI = length in bytes (may be 0).
- **Out:** RAX = CRC-32 value (upper 32 bits of RAX must be 0).
- Definition: reflected CRC with polynomial 0xEDB88320, initial value
  0xFFFFFFFF, final XOR 0xFFFFFFFF. Check value: crc32("123456789") =
  0xCBF43926.
- Buffers up to ~2 KiB; instruction budget 2,000,000 — a bitwise loop fits
  easily.
