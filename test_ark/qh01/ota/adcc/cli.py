import json
import time

import click
from loguru import logger

from test_ark.qh01.ssh import TDA4

REMOTE_FILE_RSA = "/ota/ota.rsa"
REMOTE_FILE_ZIP = "/ota/ota.zip"
REMOTE_FILE_TXT = "/ota/ota.txt"


class OTA(TDA4):
    def update_txt(self):
        cmd = f"export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib && cd /opt/qh01/target && source ./envsetup.sh && ./bin/holo_ota/upgradeTool -w {REMOTE_FILE_TXT}"  # noqa: E504
        self.exec_command(cmd)

    def request_ota(self):
        url = "http://192.168.1.135:20023/ecuupgrade?dev=adcc"  # 必须是192.168.1.135，不能用127.0.0.1
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "cdts": [
                {"key": "Speed", "operator": "<", "value": "3"},
                {"key": "Gear", "operator": "=", "value": "P"},
                {"key": "Battery", "operator": ">", "value": "80"},
            ],
            "config": REMOTE_FILE_ZIP,
            "rsa": REMOTE_FILE_RSA,
        }
        result = self.exec_command(
            f"curl -X POST -H '{json.dumps(headers)}' -d '{json.dumps(data)}' {url} --fail --silent --show-error"
        )
        return result

    def request_ota_progress(self) -> dict:
        url = "http://192.168.1.135:20023/ecuupgraderesult?dev=adcc"  # 必须是192.168.1.135，不能用127.0.0.1
        result = self.exec_command(f"curl {url} --fail --silent --show-error")
        return json.loads(result[1])


@logger.catch
def main(rsa_file: str, zip_file: str, txt_file: str):
    logger.debug(f"{rsa_file=}")
    logger.debug(f"{zip_file=}")
    logger.debug(f"{txt_file=}")
    with OTA() as ota:
        logger.info("获取当前分区定义")
        partition = ota.get_partition()
        logger.info(f"当前分区: {partition}")

        logger.info("上传文件")
        ota.upload_file(local_file=rsa_file, remote_file=REMOTE_FILE_RSA)
        ota.upload_file(local_file=zip_file, remote_file=REMOTE_FILE_ZIP)
        if txt_file:
            ota.upload_file(local_file=txt_file, remote_file=REMOTE_FILE_TXT)
            logger.info("更新签名文件")
            ota.update_txt()

        logger.info("请求OTA")
        ota.request_ota()

        logger.info("查询OTA进度")
        while True:
            result: dict = ota.request_ota_progress()
            if result["err"]:
                e = f"OTA 升级失败，错误码：{result['err']}，参见：https://holomatic.feishu.cn/sheets/AwVGspCimh3phxtB2c6ckgvsndf/"
                raise RuntimeError(e)
            if result["progress"] >= 99:
                break
            time.sleep(5)

    logger.info("等待重启...")
    time.sleep(60)

    logger.info("查询OTA结果")
    with OTA() as ota:
        if partition != ota.get_partition():
            logger.success("OTA 升级成功")
        else:
            logger.error("OTA 升级失败")


@click.command()
@click.option("--rsa-file", type=click.Path(exists=True), required=True, help="RSA 文件路径")
@click.option("--zip-file", type=click.Path(exists=True), required=True, help="ZIP 文件路径")
@click.option("--txt-file", type=click.Path(exists=True), help="TXT 文件路径")
@click.option("--count", type=int, default=1, help="升级次数")
def cli(rsa_file: str, zip_file: str, txt_file: str, count: int):
    """ADCC OTA 命令行工具"""
    for i in range(1, count + 1):
        logger.info("*" * 80)
        logger.info(f"开始第 {i} 次升级")
        logger.info("*" * 80)
        main(rsa_file=rsa_file, zip_file=zip_file, txt_file=txt_file)


if __name__ == "__main__":
    cli()
