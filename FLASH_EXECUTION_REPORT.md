# AX3000T RD03 OpenWrt flash execution report

Date: 2026-11-07

This public summary is based on the operator's execution report. Device-specific NAND dumps and private host paths are intentionally excluded.

## Result

The Xiaomi AX3000T RD03 boots OpenWrt 25.12.6 (`r33311-981c978eff`) using the stock bootloader layout. Live board identity was `xiaomi,mi-router-ax3000t` on `mediatek/filogic`. The writable overlay persisted a temporary-file check across one reboot; the temporary file was then removed. Wired LAN management was verified.

WAN DHCP/DNS were not tested because WAN had no physical link. Both radio bands were detected, but Wi-Fi client connectivity was not tested because the default interfaces were disabled. At the time of the report, the root password was unset and needed to be configured before ordinary use.

## Verified sequence

1. The stock API identified hardware RD03 running firmware 1.0.106. The [OpenWrt AX3000T device guide](https://openwrt.org/toh/xiaomi/ax3000t) indicated that downgrade was required for the documented path.
2. The Xiaomi-hosted RD03 1.0.47 image was checked for RD03/version markers and matched the recorded MD5 and SHA-256 values in the original execution record. These are image integrity checks; they do not independently establish publisher identity.
3. Stock bootloader TFTP mode was entered by holding Reset until the orange LED blinked. The host observed the DHCP/TFTP exchange and served the requested stock image. The stock API then reported RD03 firmware 1.0.47.
4. The documented `misystem/arn_switch` method enabled SSH. The router reported MediaTek MT7981, 128 MiB SPI NAND, and NMBM. Its `/proc/mtd` map included the expected boot, factory, UBI, and key partitions.
5. All 12 mapped NAND partitions were dumped with `nanddump`, copied off-router, and checked against remote MD5 and expected partition sizes. Each dump reported zero ECC failures and zero bad blocks. A manifest recorded partition names, sizes, and SHA-256 hashes. The actual dumps and manifest remain private and are not included in this public repository.
6. The OpenWrt 25.12.6 stock-layout initramfs image checksum was verified, then the image was written to the inactive UBI partition following the device guide. Boot flags were set and read back; the router booted the initramfs successfully.
7. The matching stock-layout sysupgrade image checksum was verified and `sysupgrade -T` accepted it. After `sysupgrade -n`, live checks confirmed persistent OpenWrt 25.12.6, squashfs root, writable overlay, and persistence across reboot.

No OpenWrt U-Boot modification was performed. The exact image digests are available in the original local execution record; they are omitted here to keep this concise. Refer to the official OpenWrt release directory for release artifacts and published checksums.

## Remaining setup and validation

- Set a strong root password before regular use.
- Configure Wi-Fi and test clients on both 2.4 GHz and 5 GHz.
- Connect WAN and validate DHCP and DNS.
- Test each physical Ethernet port with a real link.
- Do not import the Xiaomi settings archive as an OpenWrt configuration.
