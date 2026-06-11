typedef unsigned long long u64;

u64 kernel(u64 x) {
    /* digit-by-digit method: exact over the full u64 range, no overflow */
    u64 r = 0, bit = 1ULL << 62;
    while (bit > x) bit >>= 2;
    while (bit) {
        if (x >= r + bit) { x -= r + bit; r = (r >> 1) + bit; }
        else r >>= 1;
        bit >>= 2;
    }
    return r;
}
