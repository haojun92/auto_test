import json
import os
import sys
import time
from pathlib import Path

import click
import requests
from loguru import logger
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pythonping import ping

from test_ark.qh01.ssh import TDA4


def request_ota():
    headers = {
        "Content-Type": "application/json",
        "Content-Length": "<calculated when request is sent>",
    }
    data = {
        "cdts": [
            {"key": "Speed", "operator": "<", "value": "3"},
            {"key": "Gear", "operator": "=", "value": "P"},
            {"key": "Battery", "operator": ">", "value": "80"},
        ],
        "config": f"/ota/ota.zip",
        "rsa": f"/ota/ota.rsa",
    }
    response = requests.post(
        "http://192.168.1.135:20023/ecuupgrade?dev=adcc",
        headers=headers,
        json=data,
    )
    logger.info(response.text)
    response.raise_for_status()


def request_ota_progress() -> dict:
    response = requests.get("http://192.168.1.135:20023/ecuupgraderesult?dev=adcc")
    logger.info(response.text)
    response.raise_for_status()
    return response.json()


class OTAThread(QtCore.QThread):
    sig_response = QtCore.pyqtSignal(dict)

    def __init__(self, f_rsa, f_zip, f_txt, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.f_rsa: Path = f_rsa
        self.f_zip: Path = f_zip
        self.f_txt: Path = f_txt

        self._response: dict = {"err": 0, "name": "adcc", "progress": 0, "result": ""}

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response: dict):
        self._response.update(**response)

        if self.response["err"]:
            logger.error(self.response)
        else:
            logger.info(self.response)
        self.sig_response.emit(self.response)

    def get_partition(self) -> str:
        self.response = {"result": "分区检查中"}
        try:
            with TDA4() as ssh:
                partition = ssh.get_partition()
        except Exception as e:
            self.response = {"err": -1, "result": f"分区检查失败：{e}"}
        self.response = {"result": f"分区：{partition}"}
        return partition

    def update_txt(self):
        cmd = f"export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib && cd /opt/qh01/target && source ./envsetup.sh && ./bin/holo_ota/upgradeTool -w /mnt/config/ota/{self.f_txt.name}"  # noqa: E504
        try:
            with TDA4() as ssh:
                ssh.exec_command(cmd)
        except Exception as e:
            self.response = {"err": -1, "result": f"txt配置失败, {e}"}
        else:
            self.response = {"result": "txt配置成功"}

    def upload_file(self, local_file: Path, remote_file: str):
        self.response = {"result": f"{local_file.suffix}文件上传中"}
        try:
            with TDA4() as ssh:
                ssh.upload_file(local_file=local_file.absolute().as_posix(), remote_file=remote_file)
        except Exception as e:
            self.response = {"err": -1, "result": f"{local_file.suffix}文件上传失败, {e}"}
        else:
            self.response = {"result": f"{local_file.suffix}文件上传成功"}

    def run(self):
        # 查看分区
        last_partition: str = self.get_partition()

        # 文件上传
        self.upload_file(self.f_rsa, "/ota/ota.rsa")
        if self.f_txt.is_file():
            self.upload_file(self.f_txt, f"/mnt/config/ota/ota.txt")
            self.update_txt()
        self.upload_file(self.f_zip, "/ota/ota.zip")

        # 请求OTA
        request_ota()
        while True:
            # 查询OTA升级进度
            response: dict = request_ota_progress()
            self.response = response
            err: int = response["err"]
            progress: int = response["progress"]
            if err or progress >= 99:
                break
            time.sleep(5)
        time.sleep(30)  # 等待OTA自动重启

        t_wait = 60  # 等待OTA成功后重启完成，最多等待60s
        while not ping(os.getenv("IP_TDA4", "192.168.1.135")).success() and t_wait > 0:
            time.sleep(5)
            t_wait -= 5

        # 检查OTA升级结果
        current_partition: str = self.get_partition()
        if current_partition != last_partition:
            self.response = {"result": f"OTA成功，当前分区：{current_partition}", "progress": 100}
        else:
            self.response = {"err": -2, "result": f"OTA失败，当前分区：{current_partition}"}


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        self.setWindowTitle("OTA Tool")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.resize(400, 180)

        label = QLabel("<a href='https://holomatic.feishu.cn/sheets/AwVGspCimh3phxtB2c6ckgvsndf'>OTA错误码</a>")
        label.setOpenExternalLinks(True)
        h1 = QHBoxLayout()
        self.rsa_edit = QLineEdit(self)
        self.rsa_edit.setMinimumWidth(300)
        self.rsa_edit.setDisabled(True)
        h1.addWidget(self.rsa_edit)
        self.btn_choose_rsa = QPushButton("choose *.rsa...", self)
        self.btn_choose_rsa.clicked.connect(self.choose_rsa)
        h1.addWidget(self.btn_choose_rsa)

        h2 = QHBoxLayout()
        self.zip_edit = QLineEdit(self)
        self.zip_edit.setMinimumWidth(300)
        self.zip_edit.setDisabled(True)
        h2.addWidget(self.zip_edit)
        self.btn_choose_zip = QPushButton("choose *.zip...", self)
        self.btn_choose_zip.clicked.connect(self.choose_zip)
        h2.addWidget(self.btn_choose_zip)

        h3 = QHBoxLayout()
        self.txt_edit = QLineEdit(self)
        self.txt_edit.setMinimumWidth(300)
        self.txt_edit.setDisabled(True)
        h3.addWidget(self.txt_edit)
        self.btn_choose_txt = QPushButton("choose *.txt...", self)
        self.btn_choose_txt.clicked.connect(self.choose_txt)
        h3.addWidget(self.btn_choose_txt)

        h4 = QHBoxLayout()
        self.progress = QProgressBar(self)
        self.progress.setMinimumWidth(250)
        h4.addWidget(self.progress)
        self.btn_update = QPushButton("Update", self)
        self.btn_update.clicked.connect(self.update)
        h4.addWidget(self.btn_update)

        v1 = QVBoxLayout()
        v1.addWidget(label)
        v1.addLayout(h1)
        v1.addLayout(h2)
        v1.addLayout(h3)
        v1.addLayout(h4)

        self.main = QWidget(self)

        self.main.setLayout(v1)
        self.setCentralWidget(self.main)

        self.load_default_config()
        self.set_btn_update_state()

        self.statusBar().showMessage("ready")

        self.thread: OTAThread | None = None
        self._last_path: str | None = None

    def load_default_config(self):
        try:
            with open("config.json", mode="r") as f:
                config = json.load(f)
        except FileNotFoundError:
            ...
        else:
            self.rsa_edit.setText(config.get("rsa", ""))
            self.zip_edit.setText(config.get("zip", ""))
            self.txt_edit.setText(config.get("txt", ""))

    def set_btn_update_state(self):
        if self.rsa_edit.text():
            self.btn_choose_rsa.setText("...")
        else:
            self.btn_choose_rsa.setText("choose *.rsa...")
        if self.zip_edit.text():
            self.btn_choose_zip.setText("...")
        else:
            self.btn_choose_zip.setText("choose *.zip...")
        if self.txt_edit.text():
            self.btn_choose_txt.setText("...")
        else:
            self.btn_choose_txt.setText("choose *.txt...")
        if self.rsa_edit.text() and self.zip_edit.text():
            with open("config.json", mode="w") as f:
                json.dump(
                    {
                        "rsa": self.rsa_edit.text(),
                        "zip": self.zip_edit.text(),
                        "txt": self.txt_edit.text(),
                    },
                    f,
                    ensure_ascii=False,
                    indent=4,
                )
            self.btn_update.setDisabled(False)
        else:
            self.btn_update.setDisabled(True)

    def choose_rsa(self):
        file = QFileDialog.getOpenFileName(self, "Choose file...", self._last_path, "rsa files (*.rsa)")
        if file[0]:
            self.rsa_edit.setText(file[0])
        self.set_btn_update_state()

    def choose_zip(self):
        file = QFileDialog.getOpenFileName(self, "Choose file...", self._last_path, "zip files (*.zip)")
        if file[0]:
            self.zip_edit.setText(file[0])
        self.set_btn_update_state()

    def choose_txt(self):
        file = QFileDialog.getOpenFileName(self, "Choose file...", self._last_path, "txt files (*.txt)")
        self.txt_edit.setText(file[0])
        self.set_btn_update_state()

    def update(self):
        self.btn_update.setDisabled(True)
        self.btn_choose_rsa.setDisabled(True)
        self.btn_choose_zip.setDisabled(True)
        self.btn_choose_txt.setDisabled(True)
        self.progress.setValue(0)

        self.thread = OTAThread(
            Path(self.rsa_edit.text()),
            Path(self.zip_edit.text()),
            Path(self.txt_edit.text()),
        )
        self.thread.start()
        self.thread.sig_response.connect(self.update_progress)

    def update_progress(self, response: dict):
        result: str = response.get("result", "")
        if result:
            self.statusBar().showMessage(result)

        progress: int = response.get("progress", 0)
        self.progress.setValue(progress)

        err: int = response.get("err", 0)
        if err:
            self.statusBar().showMessage(f"{err=}, see ./log/ota.log")

        if progress == 100 or err:
            self.thread.sig_response.disconnect()
            self.thread = None

            self.btn_choose_rsa.setDisabled(False)
            self.btn_choose_zip.setDisabled(False)
            self.btn_choose_txt.setDisabled(False)
            self.btn_update.setDisabled(False)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if not self.thread:
            event.accept()
            return
        close = QMessageBox.warning(self, "", "Exit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if close == QMessageBox.No:
            event.ignore()
        else:
            event.accept()


def main():
    # 设置应用程序的缩放因子
    QGuiApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QGuiApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)

    window = Window()
    window.show()
    sys.exit(app.exec())


@click.command()
def cli() -> None:
    """ADCC OTA 图形化工具"""
    main()


if __name__ == "__main__":
    cli()
