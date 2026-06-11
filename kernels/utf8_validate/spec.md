# utf8_validate

Validate that a byte buffer is well-formed UTF-8 (RFC 3629).

- **In:** RDI = pointer to buffer, RSI = length in bytes (may be 0).
- **Out:** RAX = 1 if valid, 0 if invalid.
- Must reject: stray continuation bytes; truncated sequences (including at end
  of buffer); overlong encodings (e.g. C0 80, E0 80 AF, C1 BF); surrogates
  U+D800..U+DFFF (ED A0 80 .. ED BF BF); code points above U+10FFFF
  (F4 90 80 80 and anything F5..FF leading).
- Empty buffer is valid.
