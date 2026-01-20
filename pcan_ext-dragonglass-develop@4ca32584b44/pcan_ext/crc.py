def crc8(
    data: bytes,
    polynomial: int = 0x1D,
    initial_value: int = 0x00,
    final_xor_value: int = 0x00,
) -> int:
    crc = initial_value
    crc &= 0xFF

    for byte in data:
        crc ^= byte
        crc &= 0xFF
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ polynomial
                crc &= 0xFF
            else:
                crc <<= 1
                crc &= 0xFF
    crc ^= final_xor_value
    crc &= 0xFF

    return crc


def crc16(
    data: bytes,
    polynomial: int = 0x1021,
    initial_value: int = 0xFFFF,
    final_xor_value: int = 0x0000,
) -> int:
    crc = initial_value

    for byte in data:
        crc ^= byte << 8
        crc &= 0xFFFF
        for _ in range(8):
            if (crc & 0x8000) != 0:
                crc = (crc << 1) ^ polynomial
                crc &= 0xFFFF
            else:
                crc <<= 1
                crc &= 0xFFFF

    crc ^= final_xor_value
    crc &= 0xFFFF

    return crc
