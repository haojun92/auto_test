import argparse
import configparser
import math
import re
from pathlib import Path

import cantools


def safe_str(value):
    """将 None 转成空字符串，其他转成字符串。"""
    if value is None:
        return ""
    return str(value)


def safe_num(value):
    """数字转字符串；None 为空。"""
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isfinite(value):
            return format(value, "g")
        return ""
    return str(value)


def guess_tx_type(msg):
    """
    粗略推断发送类型。
    优先使用 cycle_time；如果没有，可继续扩展属性读取。
    """
    cycle_time = getattr(msg, "cycle_time", None)
    if cycle_time is not None:
        return "cyclic"
    return "unknown"


def guess_special_signal_name(signal_name, candidates):
    """
    根据命名规则识别特殊信号，如 checksum / rc。
    """
    s = signal_name.lower()
    for pattern in candidates:
        if re.search(pattern, s):
            return True
    return False


def get_signal_initial(signal):
    """
    尝试读取信号初始值。
    cantools 对不同 dbc/属性兼容性存在差异，所以这里做保守处理。
    """
    # 一些数据库中可能有 raw_initial / initial 之类属性
    for attr_name in ("initial", "raw_initial", "gen_sig_start_value"):
        if hasattr(signal, attr_name):
            value = getattr(signal, attr_name)
            if value is not None:
                return value
    return None


def get_signal_invalid(signal):
    """
    尝试读取无效值。
    不同 DBC 工具链的属性名不统一，这里先做兼容尝试。
    """
    for attr_name in ("invalid", "raw_invalid", "gen_sig_invalid_value"):
        if hasattr(signal, attr_name):
            value = getattr(signal, attr_name)
            if value is not None:
                return value
    return None


def export_dbc_to_ini(dbc_path, ini_path):
    db = cantools.database.load_file(dbc_path)
    # config = configparser.ConfigParser()
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str

    message_index = 0

    for msg in db.messages:
        message_index += 1
        msg_section = f"Message_{message_index}"

        checksum_signal = ""
        rc_signal = ""

        # 先通过命名规则识别 checksum / rc
        for sig in msg.signals:
            if not checksum_signal and guess_special_signal_name(
                sig.name,
                [r"checksum", r"\bcrc\b", r"crc\d*", r"chk", r"cs"]
            ):
                checksum_signal = sig.name

            if not rc_signal and guess_special_signal_name(
                sig.name,
                [r"rolling.*counter", r"alive.*counter", r"\brc\b", r"\bcounter\b", r"\balive\b"]
            ):
                rc_signal = sig.name

        msg_data = {
            "name": msg.name,
            "id": hex(msg.frame_id),
            "dlc": str(msg.length),
            "cycle_time": safe_num(getattr(msg, "cycle_time", None)),
            "tx_type": guess_tx_type(msg),
            "checksum_signal": checksum_signal,
            "rc_signal": rc_signal,
            "signal_count": str(len(msg.signals)),
        }
        config[msg_section] = msg_data

        signal_index = 0
        for sig in msg.signals:
            signal_index += 1
            sig_section = f"{msg_section}_Signal_{signal_index}"
            print(sig)

            sig_data = {
                "name": sig.name,
                "start_bit": str(sig.start),
                "length": str(sig.length),
                "byte_order": safe_str(sig.byte_order),
                "is_signed": "1" if sig.is_signed else "0",
                "scale": safe_num(sig.scale),
                "offset": safe_num(sig.offset),
                "minimum": safe_num(sig.minimum),
                "maximum": safe_num(sig.maximum),
                "unit": safe_str(sig.unit),
                "initial": safe_num(get_signal_initial(sig)),
                "invalid": safe_num(get_signal_invalid(sig)),
            }

            config[sig_section] = sig_data

    with open(ini_path, "w", encoding="utf-8") as f:
        config.write(f)


def main():
    parser = argparse.ArgumentParser(description="Parse DBC and generate CAPL-friendly INI file.")
    parser.add_argument("dbc", help="Input DBC file path")
    parser.add_argument("-o", "--output", help="Output INI file path", default="dbc_export.ini")
    args = parser.parse_args()

    dbc_path = Path(args.dbc)
    ini_path = Path(args.output)

    if not dbc_path.exists():
        raise FileNotFoundError(f"DBC file not found: {dbc_path}")

    export_dbc_to_ini(str(dbc_path), str(ini_path))
    print(f"INI generated: {ini_path}")


if __name__ == "__main__":
    main()