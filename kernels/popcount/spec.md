# popcount

Count the set bits of a 64-bit value.

- **In:** RDI = x (unsigned 64-bit).
- **Out:** RAX = number of 1-bits in x (0..64).
- Notes: hardware `popcnt` is NOT guaranteed available (baseline x86-64, SSE2
  only) — do not use it.
