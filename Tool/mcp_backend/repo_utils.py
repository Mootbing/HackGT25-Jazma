import hashlib
from pathlib import Path
import time

def file_hash(file_path):
    content = Path(file_path).read_bytes()
    return hashlib.sha256(content).hexdigest()

def wait_for_file_change(file_path, last_hash, timeout = 60):
    start = time.time()
    while time.time() - start < timeout:
        new_hash = file_hash(file_path)
        if new_hash != last_hash:
            return new_hash
        time.sleep(0.5)
    raise TimeoutError("File did not change within timeout")
