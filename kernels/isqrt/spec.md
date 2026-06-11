# isqrt

Integer square root: floor(sqrt(x)) over the FULL unsigned 64-bit range.

- **In:** RDI = x (unsigned 64-bit, up to 2^64-1).
- **Out:** RAX = largest r such that r*r <= x (r fits in 32 bits).
- Beware: floating-point double has only 53 bits of mantissa — a naive
  cvtsi2sd/sqrtsd round-trip is off by one near large perfect squares. Exact
  integer results are required everywhere, including x = 2^64-1 (r =
  4294967295) and around perfect squares.
