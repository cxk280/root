typedef unsigned long long u64;
typedef unsigned char u8;

u64 kernel(const u8 *p, u64 len, u64 byte) {
    for (u64 i = 0; i < len; i++)
        if (p[i] == (u8)byte) return i;
    return (u64)-1;
}
