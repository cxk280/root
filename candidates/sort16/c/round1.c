typedef unsigned long long u64;

u64 kernel(const u64 *in, u64 *out) {
    for (int i = 0; i < 16; i++) out[i] = in[i];
    for (int i = 1; i < 16; i++) {
        u64 v = out[i];
        int j = i - 1;
        while (j >= 0 && out[j] > v) { out[j + 1] = out[j]; j--; }
        out[j + 1] = v;
    }
    return 0;
}
