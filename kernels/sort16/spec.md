# sort16

Sort exactly 16 unsigned 64-bit integers ascending.

- **In:** RDI = pointer to input array (16 little-endian u64 = 128 bytes),
  RSI = pointer to output buffer.
- **Out:** the 16 values written to the output buffer in ascending (unsigned)
  order, little-endian u64 each. RAX is ignored.
- Duplicates may appear. The input buffer may be modified freely.
