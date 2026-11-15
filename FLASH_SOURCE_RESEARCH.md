# RD03 stock 1.0.106 installation source check

Checked 2026-11-07 against the OpenWrt device page and OpenWrt release metadata.

## Device and install method

The device page describes RD03/RD23 as the MediaTek MT7981B AX3000T and distinguishes RD03v2 as a different Qualcomm model. It recommends the latest OpenWrt 25.12 series for compatibility across AX3000T hardware. Source: [OpenWrt Xiaomi AX3000T device page](https://openwrt.org/toh/xiaomi/ax3000t).

The page's API RCE table says RD03 stock 1.0.106 (CN) has no listed API exploit and requires downgrade. It lists RD03 stock 1.0.98 (CN) with `xqsystem/start_binding`. The page's installation section describes the API RCE sequence for enabling SSH. Therefore no API-unlock command should be run against the currently reported 1.0.106 firmware. The official documented sequence is downgrade stock first, then use the applicable API method on a listed exploitable version.

The same device page says stock downgrade can use either TFTP or the Xiaomi MiWiFi Repair Tool. Its stock-bootloader TFTP section describes DHCP plus TFTP, the firmware filename derived from the router's DHCP-assigned address (example `C0A81F02.img` for `192.168.31.2`), and the Linux setup. It notes some hardware requests a different IP, so the requested address and filename must be observed rather than assumed. The page links an RD03 1.0.47 stock image as an example; it does not publish a checksum for the 1.0.98 image in the page text returned during this check. Do not treat the local 1.0.106 file as the required 1.0.98 downgrade image.

## Backup and recovery implications

The device page's OpenWrt install procedure first obtains SSH, then backs up stock partitions with `nanddump` for BL2, Nvram, Bdata, Factory, FIP, UBI, and KF, and transfers them off-router. This process depends on SSH and cannot be performed through the documented API route on 1.0.106 before downgrading.

The page documents stock-bootloader recovery through UART: load the matching AX3000T `initramfs-kernel.bin` at `0x48000000` and boot it, then install from the running initramfs. For the OpenWrt U-Boot layout, it also documents automatic TFTP boot of `openwrt-mediatek-filogic-xiaomi_mi-router-ax3000t-ubootmod-initramfs-recovery.itb` from `192.168.1.254`. This gives a documented recovery image/path for OpenWrt, but does not supply a documented non-writing way to dump all required stock partitions before the stock downgrade.

## Current firmware recommendation

OpenWrt's page recommends the latest 25.12 release. The official 25.12.6 target directory contains AX3000T stock-layout and U-Boot-layout artifacts with published checksums: [OpenWrt 25.12.6 MediaTek Filogic release directory](https://downloads.openwrt.org/releases/25.12.6/targets/mediatek/filogic/). Those images should only be selected after the router's actual NAND/partition and recovery path are verified. The stock-layout and U-Boot-layout artifacts are distinct; do not replace the stock bootloader as an incidental part of the first install.

## Safe next action

There is no source-supported unlock-only script for the router's current 1.0.106. Before any downgrade write, resolve the backup/recovery gate. The documented partition backup requires SSH, while documented stock recovery involves TFTP and the OpenWrt recovery path involves UART or the U-Boot recovery layout. A UART-backed, read-only stock-partition capture before downgrade would need to be established and verified; the official page does not provide that exact pre-downgrade capture procedure. Until then, stop before downgrading or flashing. Keep stock login tokens out of command arguments, shell history, files, and logs.
