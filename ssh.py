import enum
import os
import stat
from pathlib import Path
from typing import Any, Self

import click
import paramiko
from loguru import logger
from paramiko.sftp_client import SFTPClient


class SizeUnit(enum.Enum):
    B = 1
    KB = 2
    MB = 3
    GB = 4


def size_str(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024**2:
        return f"{size / 1024:.2f} KB"
    elif size < 1024**3:
        return f"{size / 1024**2:.2f} MB"
    return f"{size / 1024**3:.2f} GB"
import paramiko.auth_strategy

class AuthStrategy(paramiko.auth_strategy.AuthStrategy):

    def __init__(self, ssh_config, username):
        super().__init__(ssh_config)
        self.username = username

    def get_sources(self):
        yield paramiko.auth_strategy.NoneAuth(self.username)

class SSH(object):
    def __init__(
        self,
        hostname: str,
        port: int = 22,
        username: str = "root",
        password: str = None,
    ) -> None:
        logger.debug(f"Connect to {username}@{hostname}:{port}")
        self.client = paramiko.SSHClient()
        ssh_config = paramiko.SSHConfig()
        auth_strategy = AuthStrategy(ssh_config, username)
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # self.client.connect(hostname=hostname, port=port, username=username, password=password,allow_agent=False,look_for_keys=False)
        self.client.connect(hostname=hostname, auth_strategy=auth_strategy)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.client.close()

    def exec_command(self, command: str, *args, **kwargs) -> tuple[Any, str, str]:
        logger.debug(f"{command=}")
        stdin, stdout, stderr = self.client.exec_command(command, *args, **kwargs)
        # 读取输出（分块读取防止截断）
        channel = stdout.channel
        # 调整接收缓冲区大小，这里设置为一个较大的值
        channel.settimeout(None)
        channel.in_buffer_size = 6553600

        stdout = stdout.read().decode("utf-8")
        stderr = stderr.read().decode("utf-8")
        logger.debug(f"{stdout=}")
        if stderr:
            logger.error(f"{stderr=}")
        return stdin, stdout, stderr

    def upload_file(self, local_file: str, remote_file: str = None, remote_dir: str = None) -> None:
        remote_file: Path = Path(remote_file) if remote_file else Path(remote_dir) / Path(local_file).name
        self.exec_command(f"mkdir -p {remote_file.parent.as_posix()}")

        def callback(transferred: int, to_be_transferred: int):  # noqa
            progress_bar.update(transferred - progress_bar.pos)

        logger.info(f"Uploading {local_file}")
        with self.client.open_sftp() as sftp:
            size: int = os.stat(local_file).st_size
            with click.progressbar(
                length=size,
                label=f"{local_file}[{size_str(size)}]",
                show_percent=True,
            ) as progress_bar:
                sftp.put(local_file, remote_file.as_posix(), callback=callback)

    def upload_dir(self, local_dir: str, remote_dir: str) -> None:
        """
        example:
            local_dir: ./logs
            remote_dir: /userdata/log

            --> /userdata/log/logs
        """
        logger.info(f"Uploading {local_dir}")
        for local_file in Path(local_dir).rglob("*"):
            self.upload_file(local_file=local_file.as_posix(), remote_dir=remote_dir)
        logger.info(f"Upload finished -> {remote_dir}")

    def download_file(self, remote_file: str, local_file: str = None, local_dir: str = ".") -> None:
        local_file: Path = Path(local_file) if local_file else Path(local_dir) / Path(remote_file).name
        local_file.parent.mkdir(parents=True, exist_ok=True)

        def callback(transferred: int, to_be_transferred: int):  # noqa
            progress_bar.update(transferred - progress_bar.pos)

        logger.info(f"Downloading {remote_file}")
        with self.client.open_sftp() as sftp:
            size: int = sftp.stat(remote_file).st_size
            with click.progressbar(
                length=size,
                label=f"{remote_file}[{size_str(size)}]",
                show_percent=True,
            ) as progress_bar:
                sftp.get(remote_file, local_file.as_posix(), callback=callback)

    def remote_files(self, remote_dir: str) -> list[str]:
        def remote_files_of(_sftp: SFTPClient, _remote_dir: str) -> list[str]:
            out: list[str] = []
            for fo in _sftp.listdir_attr(_remote_dir):
                remote_file = (Path(_remote_dir) / fo.filename).as_posix()
                if stat.S_ISDIR(fo.st_mode):
                    out.extend(remote_files_of(_sftp, remote_file))
                else:
                    out.append(remote_file)
            return out

        with self.client.open_sftp() as sftp:
            return remote_files_of(sftp, remote_dir)

    def download_dir(self, remote_dir: str, local_dir: str = ".") -> None:
        """
        example:
            remote_dir: /userdata/log
            local_dir: ./logs

            --> ./logs/userdata/log
        """
        logger.info(f"Downloading {remote_dir}")
        for remote_file in self.remote_files(remote_dir):
            local_file = Path(local_dir) / Path(remote_dir).stem / Path(remote_file).relative_to(remote_dir)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            self.download_file(remote_file, local_file=local_file.as_posix())
        logger.info(f"Download finished -> {local_dir}")

    def print_exec_command(self, cmd: str) -> list[str]:
        _ = []
        i, o, e = self.exec_command(cmd)
        if e:
            for line in o.splitlines():
                logger.debug(line)
                _.append(line)
            for line in e.splitlines():
                logger.error(line)
                _.append(line)
        else:
            for line in o.splitlines():
                logger.success(line)
                _.append(line)
        return _
