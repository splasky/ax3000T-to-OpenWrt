#!/usr/bin/env python3
"""Copy RD03 stock NAND partitions off-router and verify each transfer."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

HOST = "root@192.168.31.1"
OPTIONS = [
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=5",
    "-o", "StrictHostKeyChecking=yes",
    "-o", "UserKnownHostsFile=/tmp/rd03-known-hosts",
    "-o", "HostKeyAlgorithms=+ssh-rsa",
]
DEST = Path(__file__).resolve().parent / "nand-backup"
DEST.mkdir(mode=0o700, exist_ok=True)
DEST.chmod(0o700)


def run(argv: list[str], timeout: int = 180) -> str:
    result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise SystemExit(f"STOP: {' '.join(argv[:2])} failed: {result.stderr[-1000:]}")
    return result.stdout + result.stderr


def ssh(command: str) -> str:
    return run(["ssh", *OPTIONS, HOST, command])


mtd = ssh("cat /proc/mtd")
expected = {
    "BL2": "mtd1", "Nvram": "mtd2", "Bdata": "mtd3",
    "Factory": "mtd4", "FIP": "mtd5", "crash": "mtd6",
    "crash_log": "mtd7", "ubi": "mtd8", "ubi1": "mtd9",
    "overlay": "mtd10", "data": "mtd11", "KF": "mtd12",
}
found = {}
for index, size, erase, name in re.findall(r'^(mtd\d+): ([0-9a-f]+) ([0-9a-f]+) "([^"]+)"$', mtd, re.M):
    found[name] = (index, int(size, 16))
if any(found.get(name, (None,))[0] != index for name, index in expected.items()):
    raise SystemExit("STOP: unexpected partition map; inspect /proc/mtd manually")

manifest = {"router": "RD03 stock 1.0.47", "mtd": mtd, "partitions": {}}
for name, index in expected.items():
    local = DEST / f"{name}.bin"
    remote = f"/tmp/rd03-backup-{name}.bin"
    output = ssh(f"nanddump -f {remote} /dev/{index}")
    if "ECC failed: 0" not in output or "Number of bad blocks: 0" not in output:
        raise SystemExit(f"STOP: inspect nanddump output for {name}: {output[-1000:]}")
    remote_md5 = ssh(f"md5sum {remote}").split()[0]
    if not local.exists():
        run(["scp", "-O", *OPTIONS, f"{HOST}:{remote}", str(local)])
    data = local.read_bytes()
    size = len(data)
    md5 = hashlib.md5(data).hexdigest()
    if size != found[name][1] or md5 != remote_md5:
        raise SystemExit(f"STOP: size or transfer hash mismatch for {name}")
    sha256 = hashlib.sha256(data).hexdigest()
    manifest["partitions"][name] = {"mtd": index, "size": size, "sha256": sha256}
    ssh(f"rm -f {remote}")
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{name}: {size} bytes; SHA-256 {sha256}", flush=True)

print("All mapped partitions copied and verified off-router.")
