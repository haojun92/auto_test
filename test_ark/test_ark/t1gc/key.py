from pathlib import Path

import colorama
from fastapi import FastAPI

from encryption import Generator

colorama.init()

app = FastAPI()


@app.get("/{seed}")
def t1gc(seed: str):
    return {"data": Generator((Path(__file__).parent / "IDCU_Vector.dll").absolute().as_posix()).request_key(seed)}