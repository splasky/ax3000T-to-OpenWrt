#!/bin/sh
# Run as root only with the router powered off and this Ethernet link isolated.
set -eu

iface=enx00e04c680e8b
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
image="$root/miwifi_rd03_firmware_ef0ee_1.0.47.bin"
expected=77bf35b27b6ec29fbfe2c3f4280618cd70bade5e9998d407b634ce8a12825cc6

[ "$(id -u)" -eq 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
[ -f "$image" ] || { echo 'Missing RD03 1.0.47 image.' >&2; exit 1; }
printf '%s  %s\n' "$expected" "$image" | sha256sum -c -
command -v dnsmasq >/dev/null
command -v nmcli >/dev/null

tftp=$(mktemp -d)
chmod 755 "$tftp"
cleanup() {
    rm -f "$tftp/C0A81F02.img"
    rmdir "$tftp" 2>/dev/null || true
    ip address del 192.168.31.100/24 dev "$iface" 2>/dev/null || true
    nmcli device set "$iface" managed yes >/dev/null 2>&1 || true
    nmcli device connect "$iface" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
ln -s "$image" "$tftp/C0A81F02.img"
nmcli device disconnect "$iface"
nmcli device set "$iface" managed no
ip -4 address flush dev "$iface"
ip address add 192.168.31.100/24 dev "$iface"
ip link set "$iface" up
ip -4 address show dev "$iface" | grep -q '192.168.31.100/24' || {
    echo 'Static TFTP address did not persist.' >&2
    exit 1
}
echo 'Ready: power on the router while holding reset; release at flashing orange LED.'
echo 'Watch the request filename below. If it differs, stop and adjust before retrying.'
dnsmasq --no-daemon --port=0 --interface="$iface" --bind-interfaces \
    --dhcp-range=192.168.31.2,192.168.31.2,255.255.255.0,10m \
    --dhcp-host=00:0c:e7:11:22:33,192.168.31.2 \
    --dhcp-ignore=tag:!known \
    --enable-tftp --tftp-root="$tftp" --log-dhcp --log-queries --log-facility=-
