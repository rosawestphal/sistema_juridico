# app/services/storage.py
import os
import hashlib
import aiofiles
from pathlib import Path
from typing import Tuple

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def save_upload(file, filename: str) -> Tuple[str, str]:
    """Save upload to disk, return (path, checksum)"""
    dest = UPLOAD_DIR / filename
    # save file async
    async with aiofiles.open(dest, "wb") as out:
        content = await file.read()
        await out.write(content)
    # checksum
    sha = hashlib.sha256()
    sha.update(content)
    checksum = sha.hexdigest()
    return str(dest), checksum
