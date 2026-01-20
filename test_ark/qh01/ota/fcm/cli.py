import json
import time

import click
from loguru import logger

from test_ark.qh01.ssh import J3A

REMOTE_FILE_RSA = "/userdata/carota/slave/ota.rsa"
REMOTE_FILE_ZIP = "/userdata/carota/slave/ota_update.zip"


class OTA(J3A):
    def request_ota(self):
        url = "http://127.0.0.1:20003/ecuupgrade?dev=fcm"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "cdts": [],
            "config": REMOTE_FILE_ZIP,
            "rsa": REMOTE_FILE_RSA,
        }
        result = self.exec_command(
            f"curl -X POST -H '{json.dumps(headers)}' -d '{json.dumps(data)}' {url} --fail --silent --show-error"
        )
        return result

    def request_ota_progress(self) -> dict:
        url = "http://127.0.0.1:20003/ecuupgraderesult?dev=fcm"
        result = self.exec_command(f"curl {url} --fail --silent --show-error")
        return json.loads(result[1])


@logger.catch
def main(rsa_file: str, zip_file: str):
    logger.debug(f"{rsa_file=}")
    logger.debug(f"{zip_file=}")
    with OTA() as ota:
        logger.info("上传文件")
        ota.upload_file(local_file=rsa_file, remote_file=REMOTE_FILE_RSA)
        ota.upload_file(local_file=zip_file, remote_file=REMOTE_FILE_ZIP)

        logger.info("请求OTA")
        ota.request_ota()

    logger.info("查询OTA进度")
    with OTA() as ota:
        while True:
            try:
                result: dict = ota.request_ota_progress()
            except ConnectionError:
                break
            if result["err"]:
                e = f"OTA 升级失败，错误码：{result['err']}，参见：https://holomatic.feishu.cn/sheets/AwVGspCimh3phxtB2c6ckgvsndf/"
                raise RuntimeError(e)
            if result["progress"] >= 99:
                break
            time.sleep(5)

    logger.info("等待重启...")
    time.sleep(10)
    while not J3A.is_online():
        time.sleep(10)

    logger.info("查询OTA结果")
    with OTA() as ota:
        result: dict = ota.request_ota_progress()
    if result["err"]:
        e = f"OTA 升级失败，错误码：{result['err']}，参见：https://holomatic.feishu.cn/sheets/AwVGspCimh3phxtB2c6ckgvsndf/"
        raise RuntimeError(e)
    if result["progress"] == 100:
        logger.success("OTA 升级成功")


@click.command()
@click.option("--rsa-file", type=click.Path(exists=True), required=True, help="RSA 文件路径")
@click.option("--zip-file", type=click.Path(exists=True), required=True, help="ZIP 文件路径")
@click.option("--count", type=int, default=1, help="升级次数")
def cli(rsa_file: str, zip_file: str, count: int):
    """FCM OTA 命令行工具"""
    for i in range(1, count + 1):
        logger.info("*" * 80)
        logger.info(f"开始第 {i} 次升级")
        logger.info("*" * 80)
        main(rsa_file=rsa_file, zip_file=zip_file)


if __name__ == "__main__":
    cli()
