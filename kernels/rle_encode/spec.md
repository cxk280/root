# rle_encode

Run-length encode a byte buffer as (count, value) pairs.

- **In:** RDI = pointer to input, RSI = input length (may be 0),
  RDX = pointer to output buffer.
- **Out:** RAX = number of bytes written to the output buffer.
- Encoding: each maximal run of equal bytes becomes two bytes
  `(count, value)` with count in 1..255. Runs longer than 255 are split into
  consecutive pairs (count 255 first; e.g. 600 x 'a' -> (255,'a') (255,'a')
  (90,'a')). Empty input writes nothing and returns 0.
- Inputs up to ~1 KiB; the output buffer is large enough for worst case.
