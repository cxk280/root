# clamp

Clamp a signed 64-bit value into an inclusive range.

- **In:** RDI = v, RSI = lo, RDX = hi (all signed 64-bit; lo <= hi guaranteed).
- **Out:** RAX = lo if v < lo, hi if v > hi, else v. Signed comparisons.
- Full i64 range may appear, including INT64_MIN and INT64_MAX.
