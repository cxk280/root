# memchr

Find the first occurrence of a byte value in a buffer.

- **In:** RDI = pointer to buffer, RSI = length in bytes (may be 0),
  RDX = byte value to find (0..255).
- **Out:** RAX = index of the first occurrence (0-based), or
  0xFFFFFFFFFFFFFFFF (i.e. -1) if not present.
