typedef unsigned long long u64;
typedef unsigned char u8;

static const char ALPHA[64] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

u64 kernel(const u8 *in, u64 len, u8 *out) {
    u64 i = 0, o = 0;
    while (i + 3 <= len) {
        u64 v = (u64)in[i] << 16 | (u64)in[i + 1] << 8 | in[i + 2];
        out[o++] = ALPHA[v >> 18];
        out[o++] = ALPHA[(v >> 12) & 63];
        out[o++] = ALPHA[(v >> 6) & 63];
        out[o++] = ALPHA[v & 63];
        i += 3;
    }
    u64 rem = len - i;
    if (rem == 1) {
        u64 v = (u64)in[i] << 16;
        out[o++] = ALPHA[v >> 18];
        out[o++] = ALPHA[(v >> 12) & 63];
        out[o++] = '=';
        out[o++] = '=';
    } else if (rem == 2) {
        u64 v = (u64)in[i] << 16 | (u64)in[i + 1] << 8;
        out[o++] = ALPHA[v >> 18];
        out[o++] = ALPHA[(v >> 12) & 63];
        out[o++] = ALPHA[(v >> 6) & 63];
        out[o++] = '=';
    }
    return o;
}
