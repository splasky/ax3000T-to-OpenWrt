#!/usr/bin/env python3
"""Enable SSH using the OpenWrt wiki's RD03 1.0.47 arn_switch method.

Run only after the stock 1.0.47 version and an isolated local link are verified.
The Xiaomi web UI stok is entered interactively and is never printed.
"""

import getpass
import json
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "http://192.168.31.1"


def request(path: str, data: bytes | None = None) -> dict:
    req = Request(BASE + path, data=data, method="POST" if data is not None else "GET")
    with urlopen(req, timeout=10) as response:
        return json.load(response)


info = request("/cgi-bin/luci/api/xqsystem/init_info")
if info.get("hardware") != "RD03" or info.get("romversion") != "1.0.47":
    raise SystemExit("STOP: router must report RD03, stock 1.0.47")

stok = getpass.getpass("Xiaomi web UI stok (input hidden): ").strip()
if not stok or any(ch not in "0123456789abcdefABCDEF" for ch in stok):
    raise SystemExit("STOP: invalid stok")

commands = (
    "nvram set ssh_en=1",
    "nvram commit",
    "sed -i 's/channel=.*/channel=\"debug\"/g' /etc/init.d/dropbear",
    "/etc/init.d/dropbear start",
    "passwd -d root",
)
for index, command in enumerate(commands, 1):
    payload = ("open=1&model=1&level=" + quote("\n" + command + "\n", safe="")).encode()
    result = request(f"/cgi-bin/luci/;stok={stok}/api/misystem/arn_switch", payload)
    if result.get("code") != 0:
        raise SystemExit(f"STOP: unlock stage {index} returned code {result.get('code')!r}")
    print(f"Unlock stage {index}/{len(commands)} accepted")
    time.sleep(1)

print("SSH enable requests accepted; verify SSH before proceeding.")
