typedef unsigned long long u64;
typedef unsigned char u8;

u64 kernel(const u8 *in, u64 len, u8 *out) {
    u64 i = 0, o = 0;
    while (i < len) {
        u8 v = in[i];
        u64 run = 1;
        while (i + run < len && in[i + run] == v && run < 255) run++;
        out[o++] = (u8)run;
        out[o++] = v;
        i += run;
    }
    return o;
}
