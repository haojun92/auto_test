
def read_rsa(file_path):
    with open(file_path,'r') as f:
        temp = f.readlines()
    return temp[0]

def transfer_data_service(file_path=r'D:\ota\idcu.zip'):
    # with open(file_path, 'rb') as file:
    #     tmp = file.readlines()
    #     print(tmp)
    buffer_size = 262144  # 设置缓冲区大小
    with open(file_path, 'rb') as f:
    # while True:
        chunk = f.read(buffer_size)
        print(chunk.hex())
        print()
        # if not chunk:
        #     break




if __name__ == '__main__':
    file_path = 'D:/ota/idcu_20241010.zip'
    #
    # transfer_data_service()
    import os
    #
    # # zip_file_path = 'your_zip_file.zip'
    zip_length = os.path.getsize(file_path)
    # print(f"The length of the ZIP package is {zip_length} bytes.")
    # hex_num = '107D6D26'
    # print(int(hex_num,16))
    # parts = [hex_num[i:i + 2] for i in range(0, len(hex_num), 2)]
    # print(int(parts[0], 16))
    # print(bytes([int(parts[0], 16)]))
    # print(bytes([0x10]))
    # print(bytes(int(parts[0], 16)))
    # print(bytes([0x44, 0x00, 0x00, 0x00,0x00]))
    # tmp = hex(int(parts[3], 16))
    # print(tmp)
    # print(type(tmp))
    length = hex(zip_length)[2:].upper()
    print(f"The length of the ZIP package is {length}.")
    print(int(length,16))
    parts = [length[i:i + 2] for i in range(0, len(length), 2)]

    print(int(bytes([int(parts[0], 16), int(parts[1], 16), int(parts[2], 16),int(parts[3], 16)]).hex(), 16))