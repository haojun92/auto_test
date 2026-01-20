
def crc8(
    data: bytes,
    polynomial: int = 0x1D,
    initial_value: int = 0xff,
    final_xor_value: int = 0xff,
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
    # crc &= 0xFF

    return crc



def crc8_j1850(data):
    crc = 0xFF  # 初始值
    polynomial = 0x1D  # CRC-8-SAE J1850 多项式

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if (crc & 0x80) != 0:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFF  # 保持 crc 在 8 位内

    return crc

# 数据输入
# data = [0x0, 0x0, 0x0, 0x60, 0x0, 0x0, 0x3]
data = [0x00, 0x00, 0x0, 0x0, 0x0, 0x0, 0x09]
crc_result = crc8(data)
print(f'CRC8: {crc_result:#04x}')
