import os

from pythonping import ping

from test_ark.ssh import SSH


class TDA4(SSH):
    hostname: str = os.getenv("IP_QH01_TDA4", "192.168.1.135")
    port: int = 22
    username: str = "root"
    password: str = "Holo@91320"

    def __init__(self) -> None:
        super().__init__(self.hostname, self.port, self.username, self.password)

    @classmethod
    def is_online(cls) -> bool:
        return ping(cls.hostname).success()

    def now(self) -> str:
        _, now, _ = self.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
        return now

    def get_partition(self) -> str:
        cmd = "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib && cd /opt/qh01/target && source ./envsetup.sh && ./bin/holo_ota/upgradeTool -g"  # noqa: E504
        _, output, _ = self.exec_command(cmd)
        partition = output.strip()[-1]
        if partition in ["A", "B"]:
            return partition
        raise ValueError(f"{output=}")

    def download_logs(self, local_dir: str):
        return self.download_dir("/userdata/log", f"{local_dir}_tda4_userdata_log")


class J3B(SSH):
    hostname: str = os.getenv("IP_QH01_J3B", "192.168.1.11")
    port: int = 22
    username: str = "root"
    password: str = "Holo@91320"

    def __init__(self) -> None:
        super().__init__(self.hostname, self.port, self.username, self.password)

    @classmethod
    def is_online(cls) -> bool:
        return ping(cls.hostname).success()

    def now(self) -> str:
        _, now, _ = self.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
        return now

    def download_logs(self, local_dir: str):
        return self.download_dir("/userdata/log", f"{local_dir}_j3b_userdata_log")


class J3A(SSH):
    hostname: str = os.getenv("IP_QH01_J3A", "192.168.1.10")
    port: int = 22
    username: str = "root"
    password: str = "qDSYGw&2HLukJR8$"

    def __init__(self) -> None:
        super().__init__(self.hostname, self.port, self.username, self.password)

    @classmethod
    def is_online(cls) -> bool:
        return ping(cls.hostname).success()

    def now(self) -> str:
        _, now, _ = self.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
        return now

    def download_logs(self, local_dir: str):
        return self.download_dir("/userdata/log", f"{local_dir}_j3a_userdata_log")


class J3Mono(SSH):
    hostname: str = os.getenv("J3Mono", "192.168.2.11")
    port: int = 22
    username: str = "root"
    # password: str = "qDSYGw&2HLukJR8$"
    password: str = " "

    def __init__(self) -> None:
        # super().__init__(self.hostname, self.port, self.username)
        super().__init__(self.hostname, self.port, self.username, self.password)

    @classmethod
    def is_online(cls) -> bool:
        return ping(cls.hostname).success()

    def now(self) -> str:
        _, now, _ = self.exec_command("date +'%Y-%m-%d %H:%M:%S.%N'")
        return now

    def download_logs(self, local_dir: str):
        return self.download_dir("/userdata/log", f"{local_dir}_j3mono_userdata_log")
