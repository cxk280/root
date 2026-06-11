typedef unsigned long long u64;
typedef unsigned int u32;
typedef unsigned char u8;

u64 kernel(const u8 *p, u64 len) {
    u32 crc = 0xFFFFFFFFu;
    for (u64 i = 0; i < len; i++) {
        crc ^= p[i];
        for (int b = 0; b < 8; b++)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return crc ^ 0xFFFFFFFFu;
}
