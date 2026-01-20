import time
from pathlib import Path
import click
import udsoncan
from loguru import logger
from udsoncan import services, MemoryLocation
from udsoncan.services import DiagnosticSessionControl

from test_ark.t1gc.doip import DoIP
from udsoncan.services import ECUReset

def get_zip_length(file_path):
    import os,binascii,codecs
    # zip_file_path = 'your_zip_file.zip'
    zip_length = os.path.getsize(file_path)
    length = hex(zip_length)[2:].upper()
    print(f"The length of the ZIP package is {length}.")
    parts = [length[i:i + 2] for i in range(0, len(length), 2)]
    return length,parts



def read_txt(file_path=r'D:\项目资料\规范\刷写规范\RSA_4096_20211110125231_test_public.txt'):
    with open(file_path,'r') as f:
        l = ''
        for line in f.readlines():
            temp = line.split('= ')[1]
            # print(temp)
            l = l+temp.strip()
        print(l)
        print(bytes.fromhex(l))


    return bytes.fromhex(temp)

def to_ascii(h):
    list_s = []
    for i in range(0, len(h), 2):
        list_s.append(chr(int(h[i:i + 2], 16)))
    return ''.join(list_s)

def main( rsa_file: str ='D:/ota/IDCU_11_22_ASW1_Full_UDS_20241010.rsa',zip_file :str = 'D:/ota/idcu_20241010.zip'):
    with DoIP() as doip:
        doip.client.change_session(DiagnosticSessionControl.Session.defaultSession) # 10 01

        # doip.client.read_data_by_identifier(0xF020)
        # doip.client.read_data_by_identifier(0xF191)
        # doip.client.read_data_by_identifier(0xF180)
        # doip.client.read_data_by_identifier(0xF187)
        # doip.client.read_data_by_identifier(0xF18A)
        # doip.client.read_data_by_identifier(0xF15B)
        # doip.client.read_data_by_identifier(0xF188)
        # doip.client.read_data_by_identifier(0xF013)
        # doip.client.read_data_by_identifier(0xF032)

        doip.client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession) # 10 03
        # doip.client.read_data_by_identifier(0xF191)
        # doip.client.read_data_by_identifier(0xF180)
        # doip.client.read_data_by_identifier(0xF187)
        # doip.client.read_data_by_identifier(0xF18A)
        # doip.client.read_data_by_identifier(0xF15B)
        # doip.client.read_data_by_identifier(0xF188)
        # doip.client.read_data_by_identifier(0xF013)
        # doip.client.read_data_by_identifier(0xF032)

        # response = doip.client.routine_control(
        #     0xD0_03, services.RoutineControl.ControlType.startRoutine
        # )  # 31 01 D0 03
        # doip.hard_reset()
        # if response.get_payload().hex() == '7101d00301':
        #     print("Condition not satisfied")
        #     raise RuntimeError("Condition not satisfied")
        # doip.client.control_dtc_setting(services.ControlDTCSetting.SettingType.off) # 85 03
        # doip.client.communication_control(0x01, 0x03) # 28 01 03
        doip.client.change_session(DiagnosticSessionControl.Session.programmingSession) # 10 02

        # doip.client.read_data_by_identifier(0xF191)
        # doip.client.read_data_by_identifier(0xF180)
        # doip.client.read_data_by_identifier(0xF187)
        # doip.client.read_data_by_identifier(0xF18A)
        # doip.client.read_data_by_identifier(0xF15B)
        # doip.client.read_data_by_identifier(0xF188)
        # doip.client.read_data_by_identifier(0xF013)
        # doip.client.read_data_by_identifier(0xF032)

        doip.client.unlock_security_access(0x07) # 27 07
        hex_data = 'A0B2B2C544BD1E85D2735B0AC02E6F4CF9A5E1424502E9C6C86D85831B7ED160CCF859027EDDB0C1558B77EB74A99797FB093F13AF45AB476058AAC6CA5ACC7139FE32A0BBC256B8044CDA31832CCEC1D52A75CC95C125E8F6A26069D05D01073BD8F93CF0EF845C09F2AF00AF27AFF5979BEFAF67CD0C82E50B56DE80C990AB7B18083F8F18CB1ED0ACA93ABB93222769C8142AAAC4E97348023EDA4C39E4085E55B1D85954B490F76710FF8AE830B171A994CEE7CDAB9CEDB0B35A5A7C89927EEE001190519DF59C9D77F9323C1254189A72B887352082895A2E5BA8479E6F13AB22FEDCA987B6F6F829F35C9729BB85F766D66B92F3EB27F47D428BA6E837A4F11DA67DA40B63C67C98B7A0DD2E396C6A8495DDABC191003FF1F5189DCBD99E86F03148E27794DF4B0875AF4B576A51112A398F5F05B79FEB9A8CA7F1883CE8D01B74E0329709E902114DAFE0E34432DFD68B7093E32CF3BA4AC5DAFB7AB86B14C519B3DFF8962BA90AC5C57CF890644DBD332C54E27D4224F11D38C64ADBAB8EC594ABB23986B75F0A906DEAF568147A45A6DC87962A78A73B601C06C67FFA5383517ED618423C3C50D9577B10A54E22C619B24AC094B8CF6FD502CE97165E853BA9023FDBE13DF0BDCF22905D03423C47882ED518A4F9D03BBB49617001176CC4B0D675EA1B3749F8ED7FA926CC06E4E4656805DC520B715E08C279CF5926F5'
        hex_data1 = 'B0B2B2C544BD1E85D2735B0AC02E6F4CF9A5E1424502E9C6C86D85831B7ED160CCF859027EDDB0C1558B77EB74A99797FB093F13AF45AB476058AAC6CA5ACC7139FE32A0BBC256B8044CDA31832CCEC1D52A75CC95C125E8F6A26069D05D01073BD8F93CF0EF845C09F2AF00AF27AFF5979BEFAF67CD0C82E50B56DE80C990AB7B18083F8F18CB1ED0ACA93ABB93222769C8142AAAC4E97348023EDA4C39E4085E55B1D85954B490F76710FF8AE830B171A994CEE7CDAB9CEDB0B35A5A7C89927EEE001190519DF59C9D77F9323C1254189A72B887352082895A2E5BA8479E6F13AB22FEDCA987B6F6F829F35C9729BB85F766D66B92F3EB27F47D428BA6E837A4F11DA67DA40B63C67C98B7A0DD2E396C6A8495DDABC191003FF1F5189DCBD99E86F03148E27794DF4B0875AF4B576A51112A398F5F05B79FEB9A8CA7F1883CE8D01B74E0329709E902114DAFE0E34432DFD68B7093E32CF3BA4AC5DAFB7AB86B14C519B3DFF8962BA90AC5C57CF890644DBD332C54E27D4224F11D38C64ADBAB8EC594ABB23986B75F0A906DEAF568147A45A6DC87962A78A73B601C06C67FFA5383517ED618423C3C50D9577B10A54E22C619B24AC094B8CF6FD502CE97165E853BA9023FDBE13DF0BDCF22905D03423C47882ED518A4F9D03BBB49617001176CC4B0D675EA1B3749F8ED7FA926CC06E4E4656805DC520B715E08C279CF5926F5'
        defaul_data = '9D91863318001E75AFBA2941C2FAE65190650172DE4810123790C0F2ACFF692258D8A65523D0270B16A462156C14928BFE6CF470496AE70F4729ADE2BCCB23A62DDA64F8083704428E5E01D4BF133E3312034DA4F4068FCFCB43C0E4D57E2865924822BA75F837DB3787554DE4E3792813694322BC5D143617AB52FF5833F2D1B1FCA0E2AAAA6A813584CD0447CE4441BCE649FAABF987E946A9AA2FC22DB9D4E6472AEF4D9D9DB5F6774E1CB51780314CF206B59902467D47CB56DACA0FF22FB6FEA64FE0321BC2C50673B078CA23200944F611F606C1DDBD60F9C733A6FFC135758BC6A0110A5E2CAB3985B90250757244F83BD3F427FD35E37F1CCEED37AA6909B80F8A5A952F83E7912CDE2D931FB03FCEBEE6F67F6EA84C533D4A75196808C9DF35233A61275AA250A9EBD7DC46B725BB07059DE2D47E301B429831F80BFDF6485D80D54B49C1733AC07C04E79C86B7F8F3FE8FA48CAE8E713100C9959B5060D33AC166AB46DDA8F6DE197FFEDC322517D20CB9591B3E4E8B36724265D5CFA9B7D5E651E7D655081F41B6119F2DE9A545B0F231BC1B5EA59DF5898201506F26496B1076AED230506BD056FA89D6926057174B0DA255AF2795E8B2F636A649566DC04E957159CE40BBC93C72502379AB6A4D5D0DEE4568B267A6D56072FE327EB28B5497D8F62765AAC88ECC594338B9B719CFE0663503C79E0A5D3F4D0926F5'
        # #
        doip.client.read_data_by_identifier(0xF020)
        doip.client.write_data_by_identifier(0xF022,defaul_data)
        doip.client.read_data_by_identifier(0xF020)
        # doip.client.write_data_by_identifier(0xF021,defaul_data)
        # doip.client.read_data_by_identifier(0xF020)
        #


        # doip.client.write_data_by_identifier(0xF021,hex_data)
        # doip.client.read_data_by_identifier(0xF020)

        # doip.client.routine_control(0xD0_04,services.RoutineControl.ControlType.startRoutine,data=read_rsa(rsa_file)) # 31 01 D0 04
        # length,parts = get_zip_length(zip_file)
        # doip.client.routine_control(
        #     0xFF_00,
        #     services.RoutineControl.ControlType.startRoutine,
        #     data=bytes([0x44, 0x00, 0x00, 0x00,0x00,int(parts[0], 16),int(parts[1], 16),int(parts[2], 16),int(parts[3], 16)]),
        # )  # 31 01 FF 00
        #
        # # memory_location = MemoryLocation(address=int(bytes([0x00, 0x00, 0x00, 0x00]).hex(), 16),
        # #                                  memorysize=int(bytes([int(length[0], 16),int(length[1], 16),int(length[2], 16),
        # #                                                        int(length[3], 16)]).hex(), 16),
        # #                                  address_format=32, memorysize_format=32)
        # memory_location = MemoryLocation(address=int(bytes([0x00, 0x00, 0x00, 0x00]).hex(), 16),
        #                                  memorysize=int(length,16),
        #                                  address_format=32, memorysize_format=32)
        # doip.client.request_download(memory_location=memory_location)  # 34 00 44 00
        # doip.transfer_data_service() # 36 01
        # doip.client.request_transfer_exit()  # 37
        # res = doip.client.routine_control(0xD0_02, services.RoutineControl.ControlType.startRoutine, data=read_rsa(rsa_file)) # 31 01 D0 02
        # if res.get_payload().hex() == '7101d00201':
        #     logger.info("incorrectResult")
        #
        # res = doip.client.routine_control(0xff_01, services.RoutineControl.ControlType.startRoutine,
        #                                   )  # 31 01 ff 01
        # if res.get_payload().hex() == '7101ff0101':
        #     logger.info("incorrectResult")
        # doip.client.routine_control(0xd0_05, services.RoutineControl.ControlType.startRoutine)  # 31 01 d0 05
        # while True:
        #     res = doip.client.routine_control(0xd0_05, services.RoutineControl.ControlType.requestRoutineResults) # 31 03 d0 05
        #     if '7103D00502' in res.get_payload().hex():
        #         logger.info('install completed')
        #         break
        #     elif '7103D00503' in res.get_payload().hex():
        #         continue
        #     elif '7103D00505' in res.get_payload().hex():
        #         logger.error('install failure')
        #         break
        #     time.sleep(1)
        # doip.client.tester_present()
        # doip.client.tester_present()
        # doip.client.tester_present()
        # doip.client.tester_present()
        # doip.client.tester_present()
        # doip.client.change_session(DiagnosticSessionControl.Session.defaultSession) # 10 81
        # doip.client.tester_present()
        # doip.client.tester_present()
        # doip.client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)  # 10 03
        # time.sleep(10)
        # doip.client.clear_dtc() # 14
        # time.sleep(1)
        #
        # response = doip.client.routine_control(
        #     0xD0_03, services.RoutineControl.ControlType.startRoutine
        # )
    #     time.sleep(13)
    # with DoIP() as doip:
    #     doip.client.change_session(DiagnosticSessionControl.Session.defaultSession)
    #     doip.client.clear_dtc()




@click.command()
@click.option(
    "--data-file",
    type=str,
    help="ota test",
)
def cli(data_file: str) -> None:
    """ota test"""
    main()

if __name__ == "__main__":
   cli()
   # a = 'B0B2B2C544BD1E85D273083F6A8495DDABC19100111111113FF1F5189DCBD99E86F03148E27794DF4B0875AF4B576A51112A398F5F05B79FEB9A8CA7F1883CE8D01B74E0329709E902114DAFE0E34432DFD68B7093E32CF3BA4AC5DAFB7AB86B14C519B3DFF8962BA90AC5C57CF890644DBD332C54E27D4224F11D38C64ADBAB8EC594ABB23986B75F0A906DEAF568147A45A6DC87962A78A73B601C06C67FFA5383517ED618423C3C50D9577B10A54E22C619B24AC094B8CF6FD502CE97165E853BA9023FDBE13DF0BDCF22905D03423C47882ED518A4F9D03BBB49617001176CC4B0D675EA1B3749F8ED7FA926CC06E4E4656805DC520B715E08C279CF5926F5'
   # print(len(a))

