# base64_encode

Standard Base64 encoding (RFC 4648, with padding).

- **In:** RDI = pointer to input, RSI = input length (may be 0),
  RDX = pointer to output buffer.
- **Out:** RAX = number of bytes written ( = 4*ceil(len/3) ).
- Alphabet: A-Z a-z 0-9 + / with '=' padding. No line breaks. Empty input
  writes nothing and returns 0.
- Inputs up to ~2 KiB; the output buffer is large enough.
