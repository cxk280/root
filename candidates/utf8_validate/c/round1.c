typedef unsigned long long u64;
typedef unsigned char u8;

u64 kernel(const u8 *p, u64 len) {
    u64 i = 0;
    while (i < len) {
        u8 c = p[i];
        if (c < 0x80) { i++; continue; }
        u64 n;          /* continuation bytes */
        u8 lo = 0x80, hi = 0xBF;  /* bounds for the FIRST continuation byte */
        if (c >= 0xC2 && c <= 0xDF) n = 1;
        else if (c == 0xE0) { n = 2; lo = 0xA0; }            /* no overlongs */
        else if (c >= 0xE1 && c <= 0xEC) n = 2;
        else if (c == 0xED) { n = 2; hi = 0x9F; }            /* no surrogates */
        else if (c >= 0xEE && c <= 0xEF) n = 2;
        else if (c == 0xF0) { n = 3; lo = 0x90; }            /* no overlongs */
        else if (c >= 0xF1 && c <= 0xF3) n = 3;
        else if (c == 0xF4) { n = 3; hi = 0x8F; }            /* <= U+10FFFF */
        else return 0;   /* 0x80..0xC1, 0xF5..0xFF */
        if (len - i - 1 < n) return 0;
        u8 c1 = p[i + 1];
        if (c1 < lo || c1 > hi) return 0;
        for (u64 k = 2; k <= n; k++) {
            u8 ck = p[i + k];
            if (ck < 0x80 || ck > 0xBF) return 0;
        }
        i += n + 1;
    }
    return 1;
}
