import shlex
import subprocess
from pathlib import Path

from loguru import logger


class FillBack:
    def __init__(self, log_file: str, fillback_exec_path: str, fillback_pack_path: str = "./pack"):
        """
        func: 回灌开启后的测试函数主体
        fillback_exec_path: 回灌进程所在目录
        fillback_pack_path: 回灌包所在目录
        """
        if not Path(log_file).parent.exists():
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Starting fillback, log file: {log_file}")
        with open(log_file, "w") as f:
            self.p = subprocess.Popen(
                shlex.split(f"adas-client-console.exe global_fcm.json fillback {fillback_pack_path}"),
                stdout=f,
                stderr=f,
                text=True,
                shell=True,
                cwd=Path(fillback_exec_path).absolute().as_posix(),
            )

    @staticmethod
    def stop():
        logger.info(f"Stop fillback...")
        subprocess.call(shlex.split("taskkill /F /im adas-client-console.exe"))
        logger.info(f"Stop fillback completed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.p.wait()
