typedef long long i64;

i64 kernel(i64 v, i64 lo, i64 hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}
