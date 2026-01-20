"""
enum VKeyGenResultEx
{
  KGRE_Ok = 0,
  KGRE_BufferToSmall = 1,
  KGRE_SecurityLevelInvalid = 2,
  KGRE_VariantInvalid = 3,
  KGRE_UnspecifiedError = 4
};

// The client has to provide a keyArray buffer and has to transfer this buffer -
// including its size - to the GenerateKey method. The method checks, if the size is
// sufficient. The client can discover the required size by examining the service used
// transfer the key to the ECU.
// Returns false if the key could not be generated:
//  -> keyArraySize to small
//  -> generation for specified security level not possible
//  -> variant unknown
KEYGENALGO_API VKeyGenResultEx GenerateKeyEx(
   const unsigned char* ipSeedArray, unsigned int iSeedArraySize,
   const unsigned int iSecurityLevel, const char* ipVariant,
   unsigned char* iopKeyArray, unsigned int iMaxKeyArraySize,
   unsigned int& oActualKeyArraySize);
#endif // KEY_GEN_ALGO_INTERFACE_H
"""
import ctypes
from enum import Enum
from pathlib import Path
from typing import Optional


class VKeyGenResultExOpt(Enum):
    KGREO_Ok = 0,
    KGREO_BufferToSmall = 1,
    KGREO_SecurityLevelInvalid = 2,
    KGREO_VariantInvalid = 3,
    KGREO_UnspecifiedError = 4


class Generator(object):
    def __init__(self, dll_path: Optional[str] = None):
        self._dll_path = dll_path

        self.dll = ctypes.WinDLL(self._dll_path)

        self.dll.GenerateKeyExOpt.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),  # const unsigned char* ipSeedArray
            ctypes.c_uint,  # unsigned int iSeedArraySize
            ctypes.c_uint,  # const unsigned int iSecurityLevel
            ctypes.c_char_p,  # const char* ipVariant
            ctypes.c_char_p,  #const char * ipOptions,
            ctypes.POINTER(ctypes.c_ubyte),  # unsigned char* iopKeyArray
            ctypes.c_uint,  # unsigned int iMaxKeyArraySize
            ctypes.POINTER(ctypes.c_uint),  # unsigned int& oActualKeyArraySize
        ]

        self.dll.GenerateKeyExOpt.restype = ctypes.c_int  # VKeyGenResultExOpt

    def request_key(self, seed: str, security_level: int = 0x07, max_key_array_size: int = 16, variant=b"",option =b""):
        # seed = ''.join(f'{b:02x}' for b in eval(seed))
        seed_array = (ctypes.c_ubyte * len(seed))(*bytearray.fromhex(seed))
        seed_array_size = len(seed_array)
        actual_key_array_size = ctypes.c_uint()

        key_array = (ctypes.c_ubyte * max_key_array_size)()  # 创建用于存储密钥的数组

        result: VKeyGenResultExOpt = self.dll.GenerateKeyExOpt(
            ctypes.cast(seed_array, ctypes.POINTER(ctypes.c_ubyte)),
            seed_array_size,
            security_level,
            variant,
            option,
            ctypes.cast(key_array, ctypes.POINTER(ctypes.c_ubyte)),
            max_key_array_size,
            ctypes.byref(actual_key_array_size),
        )
        print()

        if result == VKeyGenResultExOpt.KGREO_Ok.value[0]:
            print('======')
            # GenerateKeyEx success!
            t = bytes(key_array[: actual_key_array_size.value])
            print(type(t.decode('iso-8859-1')))
            # return bytes(key_array[: actual_key_array_size.value])
            return key_array[: actual_key_array_size.value]
        # GenerateKeyEx failed!
        return ""


if __name__ == "__main__":
    # key = Generator((Path() / "IDCU_Vector.dll").absolute().as_posix()).request_key(seed="56afdb10")
    key = Generator((Path() / "D:/code/test_ark/test_ark/t1gc/IDCU_Vector.dll").absolute().as_posix()).request_key(seed="56afdb10")
    print(key,'=======')  # expect: 2a6bf73d315d3fcd594a2bedb47ed9f3
    # key = Generator((Path() / "FCM.dll").absolute().as_posix()).request_key(seed="0f8451342d55356d1fdf91444ae973c9")
    # print(key)  # expect: 43cae0d6eb7323f6cddb970db6eded1e