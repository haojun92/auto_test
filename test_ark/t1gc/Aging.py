import time
from pathlib import Path
import click
import udsoncan
from loguru import logger
from udsoncan import services, MemoryLocation
from udsoncan.services import DiagnosticSessionControl

from test_ark.t1gc.doip import DoIP
from udsoncan.services import ECUReset

def test_aging():
    i = 1
    while i <= 41:
        logger.info(f'第{i}次测试')
        with DoIP() as doip:
            doip.client.change_session(DiagnosticSessionControl.Session.defaultSession) # 10 01
            res = doip.client.read_dtc_information(0x02, 0x09)
            for index, dtc in enumerate(doip.read_dtc(res.data[2:])):
                logger.warning(f"DTC{index}: {dtc.hex()}")
                if dtc[-1] == 0x09 and dtc[:-1].hex() == "630017":
                    raise Exception("故障状态，请检查！")
            doip.hard_reset()
            i += 1
        time.sleep(20)

def main():
    with DoIP() as doip:
        doip.client.change_session(DiagnosticSessionControl.Session.defaultSession)  # 10 01
        doip.client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession) # 10 03
        res = doip.client.read_dtc_information(0x02, 0x09)
        for index, dtc in enumerate(doip.read_dtc(res.data[2:])):
            logger.warning(f"DTC{index}: {dtc.hex()}")
        # doip.client.read_data_by_identifier(0x470f)
        # response = doip.client.routine_control(
        #     0xD0_03, services.RoutineControl.ControlType.startRoutine
        # )  # 31 01 D0 03
        # logger.info('Condition check')
        # if response.get_payload().hex() == '7101d00301':
        #     logger.info("Condition not satisfied")
        #     raise RuntimeError("Condition not satisfied")




if __name__ == '__main__':
    main()