import time
from pathlib import Path

from pcan_ext.callback import callback_tx_print
from pcan_ext.channel import Channel
from pcan_ext.utils import DBC, Tx
from PCANBasic import *  # noqa

if __name__ == "__main__":
    dbc_path = "BEV_E0X_OT_Car ADCC_CH Message list  V3.60 Draft _202308301702.dbc"
    dbc = DBC(dbc_path=Path(__file__).parent / dbc_path)

    ch = Channel()
    ch.initialize(channel_handle=PCAN_USBBUS2)

    threads = []
    for k, v in {
        "ACU_2": {
            "ACU_2_YawrateSigValidData": 0,
            "ACU_2_YawRate": 0.0,
            "ACU_2_LateralAccelerationSigVD": 0,
            "ACU_2_LateralAcceleration": 0.0,
        },
        "ACU_3": {
            "ACU_3_LongitudinalAccelerationVD": 0,
            "ACU_3_LongitudinalAcceleration": 0.0,
        },
        "ONEBOX_1": {
            "ESP1_VehicleSpeedVSOSigValidData": 0,
            "ABS_ESP_1_VehicleSpeedVSOSig": 39,
        },
        "SAS_1": {
            "SAM_1_SteeringAngleSpeed": 0,
            "SAM_1_SteeringAngleSpeedVD": 0,
            "SAM_1_SteeringAngle": 0,
            "SAM_1_SteeringAngleVD": 0,
        },
        "VCU_COM_10": {
            "VCU_ActualGear": 0x4,  # D档
            "VCU_ActualGearValidData": 1,
        },
        "EPS_1": {},
        "EPS_3": {},
    }.items():
        message = dbc.db.get_message_by_name(k)
        Tx().update({message.frame_id: dbc.encode(message, v)})

        threads.append(
            ch.threading_write_message(
                interval=message.cycle_time,
                frame_id=message.frame_id,
                callbacks=[
                    dbc.callback_crc8,
                    callback_tx_print,
                ],
            )
        )

    for thread in threads:
        thread.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        ...

    for thread in threads:
        thread.cancel()
    for thread in threads:
        thread.join()

    ch.release()
