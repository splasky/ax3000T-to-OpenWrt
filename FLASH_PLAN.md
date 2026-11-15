# Xiaomi AX3000T RD03 → OpenWrt

User-confirmed router address: `192.168.31.1`. User ran a read-only stock API request from the host and reported `code=0`, `hardware=RD03`, `romversion=1.0.106`, `countrycode=CN`, `model=xiaomi.router.rd03`, `newEncryptMode=1`, `inited=1`, `bound=0`.

## Source-verified path

The official OpenWrt device page identifies RD03/RD23 as the MediaTek MT7981B AX3000T platform, recommends the latest 25.12 series, and says RD03 stock 1.0.106 has no listed API RCE (`no - downgrade required`). The same page documents a stock-bootloader TFTP downgrade path and lists `miwifi_rd03_firmware_ef0ee_1.0.47.bin` from Xiaomi's CDN. One TFTP example uses the PC at `192.168.31.100`, router at `192.168.31.2`, and requested file name `C0A81F02.img`; the actual TFTP request must be observed because the guide notes hardware can request a different address/file name.

Sources:

- [OpenWrt Wiki: Xiaomi AX3000T](https://openwrt.org/toh/xiaomi/ax3000t)
- [Xiaomi CDN: RD03 1.0.47 stock firmware](https://cdn.cnbj1.fds.api.mi-img.com/xiaoqiang/rom/rd03/miwifi_rd03_firmware_ef0ee_1.0.47.bin)
- OpenWrt release metadata: [25.12 stable releases](https://downloads.openwrt.org/releases/)

The local RD03v2/Qualcomm repository is unrelated and must not supply firmware or installation steps.

## Safe sequence and backup limitation

1. Before the first stock-firmware write, export the router's configuration using the stock UI, stage a Xiaomi-hosted RD03 stock recovery image on the host, and prepare the documented stock-bootloader TFTP recovery network. This preserves a return path if the downgrade fails. The official OpenWrt page also documents later UART/TFTP recovery using an initramfs image; preserve that procedure and a matching image for the chosen OpenWrt layout.
2. 1.0.106 cannot use the documented API exploit directly. The official page says downgrade is required. Downgrading is itself a firmware write. Raw NAND/bootloader/calibration backups cannot be assumed available before root access; the original stock firmware export is not a substitute for those backups.
3. After the documented downgrade, obtain root access only through the API method listed for the observed downgraded version (for 1.0.47, the official table lists `misystem/arn_switch`; 1.0.64 through 1.0.98 use `xqsystem/start_binding`). Before writing OpenWrt, inspect `/proc/mtd` and board/NAND identification, then use the official page's NAND backup procedure (BL2, Nvram, Bdata, Factory, FIP, ubi, KF as present) to copy backups off-router and hash them. If the actual partition map differs or critical calibration/factory data cannot be recovered, stop before the OpenWrt install.
4. Only after backup and recovery gates pass, use the official OpenWrt stable 25.12 AX3000T instructions and exact matching artifact/layout. Do not replace the bootloader or use a ubootmod artifact unless the procedure explicitly requires it and the recovery plan covers it.
5. After install, confirm board identity, management access, wired ports, WAN/DHCP/DNS, both Wi-Fi bands, and persistence after one reboot.

## Host-side preparation (download only; does not flash)

Run from the user's normal Linux terminal. It downloads the Xiaomi stock image to a dedicated recovery folder, prints its SHA-256, and checks that the payload contains the RD03 model/version markers. Do not rename it into an active TFTP directory or trigger router recovery yet.

```sh
mkdir -p "$HOME/ax3000t-rd03-recovery"
cd "$HOME/ax3000t-rd03-recovery"
curl --fail --location --proto '=https' --tlsv1.2 \
  'https://cdn.cnbj1.fds.api.mi-img.com/xiaoqiang/rom/rd03/miwifi_rd03_firmware_ef0ee_1.0.47.bin' \
  -o miwifi_rd03_firmware_ef0ee_1.0.47.bin
sha256sum miwifi_rd03_firmware_ef0ee_1.0.47.bin
python3 - <<'PY'
from pathlib import Path
p = Path('miwifi_rd03_firmware_ef0ee_1.0.47.bin')
b = p.read_bytes()
for marker in (b"HARDWARE 'RD03'", b"ROM '1.0.47'"):
    if marker not in b:
        raise SystemExit(f"STOP: expected marker missing: {marker!r}")
print(f"Payload markers OK; size={len(b)} bytes")
PY
```

This validates source transport and embedded labels, not the Xiaomi signature or a published checksum. The official wiki/CDN path is the provenance basis; preserve the printed digest in the local recovery record. Continue only after the host's TFTP service/firewall settings are prepared and the stock UI configuration export is saved. TFTP downgrade and the final OpenWrt install are separate write stages.

## Execution status

Completed 2026-11-07: the router was downgraded to stock 1.0.47 over bootloader TFTP, all 12 observed NAND partitions were backed up and verified off-router, and OpenWrt 25.12.6 was installed with the stock bootloader layout. The router booted a persistent squashfs/UBI system and passed one reboot. See `FLASH_EXECUTION_REPORT.md` and `recovery/nand-backup/manifest.json` for evidence. WAN service and Wi-Fi client connectivity remain untested because WAN is unplugged and the default Wi-Fi interfaces are disabled; the OpenWrt root password is unset and should be configured promptly.
