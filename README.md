# Xiaomi AX3000T RD03: agent runbook for OpenWrt

This runbook documents the recorded procedure for the **Xiaomi AX3000T RD03 (MediaTek MT7981B)**: downgrade stock firmware to 1.0.47, enable SSH, preserve stock NAND data, and install OpenWrt. It is written for an automation agent operating from a Linux host.

## Constraints and stop conditions

- No UART or serial cable is used. The downgrade does require a human to hold Reset until the orange LED blinks. The agent prepares TFTP first, asks the human to perform this action, then observes the request and serves the image.
- Proceed only when the device reports `hardware=RD03`. RD03v2 is a different Qualcomm device. Do not use its firmware or instructions.
- The source research says the initially observed stock 1.0.106 has no listed API unlock and requires downgrade. Do not run the 1.0.47 unlock against another version.
- Keep Xiaomi `stok`, SSH credentials, and any tokens out of argv, shell history, logs, source files, and Git. Enter the `stok` only at the script's hidden prompt.
- Stop on any mismatch in firmware identity, TFTP request name/address, partition map, image layout, backup verification, or command result.

## Source of truth

- [OpenWrt Xiaomi AX3000T device page](https://openwrt.org/toh/xiaomi/ax3000t)
- [Xiaomi RD03 stock 1.0.47 image](https://cdn.cnbj1.fds.api.mi-img.com/xiaoqiang/rom/rd03/miwifi_rd03_firmware_ef0ee_1.0.47.bin)
- [OpenWrt 25.12.6 Filogic artifacts](https://downloads.openwrt.org/releases/25.12.6/targets/mediatek/filogic/)

The source review was recorded on 2026-11-07 in [FLASH_SOURCE_RESEARCH.md](FLASH_SOURCE_RESEARCH.md). Recheck the official device page and current stable release before a future run; do not assume 25.12.6 remains current.

## Agent procedure

### `recovery/` file guide and mandatory preflight

Before any firmware downgrade or OpenWrt write, inspect the recovery assets and complete the applicable backup/recovery preparation. A verified stock NAND backup is mandatory before installing OpenWrt. The `backup-rd03.py` helper only works after SSH is available on stock 1.0.47, so it cannot back up NAND before the downgrade from 1.0.106; this is a known limitation, not a reason to claim pre-downgrade backup is complete. Stage and verify the stock recovery image and TFTP host setup first. If the user's requirement is that NAND backup must precede *any* firmware downgrade, stop: current documented procedure cannot satisfy it without first establishing another supported backup path.

- `backup-rd03.py`: reads the expected `/proc/mtd` map, dumps 12 partitions over SSH, copies them locally, and checks sizes and transfer hashes. Requires stock 1.0.47 SSH; writes device-specific files and a manifest under `recovery/nand-backup/`.
- `unlock-rd03-1047.py`: validates RD03/stock 1.0.47 and enables SSH through the documented API; requests the web UI `stok` via a hidden prompt. It is not a backup or recovery script.
- `serve-rd03-stock.sh`: verifies the stock image SHA-256, configures isolated host networking and runs DHCP/TFTP for downgrade/recovery. It requires root and currently hard-codes an interface, MAC, IP, and TFTP filename that must be checked against the actual setup. Human Reset-button action is needed to enter orange-blinking TFTP mode.
- `miwifi_rd03_firmware_ef0ee_1.0.47.bin`: Xiaomi RD03 stock 1.0.47 firmware used for downgrade and stock TFTP recovery.
- `openwrt-25.12.6-mediatek-filogic-xiaomi_mi-router-ax3000t-initramfs-factory.ubi`: OpenWrt factory-layout image; do not assume it is the correct install artifact without matching the official device instructions and partition layout.
- `openwrt-25.12.6-mediatek-filogic-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin`: sysupgrade image for an already installed compatible OpenWrt system; it is not the stock-firmware first-install image.
- `nand-backup/` (created by the backup helper): sensitive device-specific partition dumps and manifest. Keep private, verify completeness, and store a protected second copy; never publish it.

Required order: inspect assets and verify the stock recovery image/TFTP preparation; perform the human Reset action to downgrade to 1.0.47; verify model/version; unlock SSH; run and verify the NAND backup; only then install OpenWrt. If “backup first” means before the downgrade itself, the current scripts cannot do that: do not downgrade until a supported pre-downgrade backup/recovery method is established.

### 1. Identify and stage

1. Query stock init info read-only and require RD03. Record current firmware version and router address. For current 1.0.106, the recorded address was `192.168.31.1`; discover it rather than assuming it.
2. Download the Xiaomi-hosted 1.0.47 image to a private working directory. Check its SHA-256 and embedded RD03/1.0.47 markers. The `expected=77bf35b27b6ec29fbfe2c3f4280618cd70bade5e9998d407b634ce8a12825cc6` value in `recovery/serve-rd03-stock.sh` is the image's expected SHA-256 checksum. It is a public integrity-check value, not a password, token, API key, or private key. A match detects file changes; it does not by itself prove who published the image, so trust depends on checksum provenance.
3. Stage host-side TFTP and isolated Ethernet configuration. The script `recovery/serve-rd03-stock.sh` currently assumes interface `enx00e04c680e8b`, MAC `00:0c:e7:11:22:33`, host `192.168.31.100`, and TFTP name `C0A81F02.img`. Inspect and adapt only from observed hardware/network facts. Once the agent is ready and listening, have the human hold Reset until the orange LED blinks; then observe the router's actual DHCP/TFTP request and serve the matching image. Stop if the request differs from the prepared setup.
4. Prepare the documented TFTP recovery image and host setup before writing. A stock config export is not a NAND backup. Do not proceed if the required recovery path is unavailable.

### 2. Downgrade and unlock

Only after step 1's recovery gate is satisfied, transfer the verified stock image by the officially documented stock-bootloader TFTP method. Observe the actual DHCP/TFTP request and require it to match the staged address and filename. Do not infer success from a transfer alone: wait for reboot, reconnect, and verify `hardware=RD03` and `romversion=1.0.47` through the read-only API.

Run `python3 recovery/unlock-rd03-1047.py` only after those checks and on an isolated local link. It validates model/version and requests the `stok` interactively without echoing it. Verify SSH independently before continuing. Stop on any nonzero API result or unexpected response.

### 3. Back up stock NAND

Run `python3 recovery/backup-rd03.py` from the project directory after verifying SSH host identity. The script expects the exact 12-partition map encoded in it and checks each dump's size and transfer hash. Keep `recovery/nand-backup/` private and out of Git; it contains device-specific calibration and factory data. Confirm all expected partitions exist, manifest hashes match the files, and copy a second protected backup before writing OpenWrt. Stop if the map differs, a dump reports ECC/bad-block issues, SSH host identity is uncertain, or any verification fails.

### 4. Install OpenWrt

Select the current official AX3000T **stock-bootloader layout** image matching the verified board and partition layout. Verify the official checksum. Do not use a U-Boot-mod image or replace the bootloader as part of this procedure. Follow the current OpenWrt device-page installation commands exactly; this repository does not contain a verified, self-contained install script. Before the write, recheck the recovery gate and verified off-device NAND backup. After reboot, confirm board identity, management access, persistent squashfs/UBI boot, wired LAN, WAN/DHCP/DNS, both Wi-Fi bands, and one reboot.

## Recorded outcome and known gaps

The project plan records that on 2026-11-07 the device was downgraded to 1.0.47 over bootloader TFTP, 12 NAND partitions were backed up, and OpenWrt 25.12.6 was installed with the stock bootloader layout; one reboot passed. However, `FLASH_EXECUTION_REPORT.md` and `recovery/nand-backup/manifest.json` were not present in the supplied project directory at documentation time, so this README cannot independently verify those claims. The source plan also records WAN unplugged, Wi-Fi interfaces disabled, and root password unset. Treat WAN and Wi-Fi as untested, and set a strong root password immediately on any reachable installation.

## Related files

- [FLASH_PLAN.md](FLASH_PLAN.md): source-backed plan and prior execution notes.
- [FLASH_SOURCE_RESEARCH.md](FLASH_SOURCE_RESEARCH.md): official-source review and recovery limitations.
- `recovery/unlock-rd03-1047.py`, `recovery/backup-rd03.py`, `recovery/serve-rd03-stock.sh`: host-side helper scripts; inspect assumptions before use.
