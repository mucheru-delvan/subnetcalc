import argparse
import sys

from subnetcalc.core import (
    ip_to_int, int_to_ip, prefix_to_mask,
    network_address, broadcast_address, host_range,
    usable_hosts, split_network,
)


def parse_cidr(cidr: str) -> tuple[int, int]:
    ip_str, sep, prefix_str = cidr.partition("/")
    if not sep:
        raise ValueError(f"expected CIDR like 192.168.10.0/24, got {cidr!r}")
    if not (prefix_str.isascii() and prefix_str.isdigit()):
        raise ValueError(f"prefix is not a number: {prefix_str!r}")

    prefix = int(prefix_str)
    if prefix > 32:
        raise ValueError(f"prefix must be 0-32, got {prefix}")

    return ip_to_int(ip_str), prefix


def format_summary(ip: int, prefix: int) -> str:
    first, last = host_range(ip, prefix)
    rows = [
        ("Network", f"{int_to_ip(network_address(ip, prefix))}/{prefix}"),
        ("Netmask", int_to_ip(prefix_to_mask(prefix))),
        ("Broadcast", int_to_ip(broadcast_address(ip, prefix))),
        ("Host range", f"{int_to_ip(first)} - {int_to_ip(last)}"),
        ("Usable hosts", str(usable_hosts(prefix))),
    ]
    return "\n".join(f"{label + ':':<14}{value}" for label, value in rows)


def format_split(ip: int, prefix: int, new_prefix: int) -> str:
    # Guard against huge outputs, e.g. a /8 split into /32s.
    if new_prefix - prefix > 16:
        raise ValueError("refusing to split into more than 65536 blocks")

    blocks = split_network(ip, prefix, new_prefix)
    lines = [f"Split into {len(blocks)} blocks of /{new_prefix}:"]
    for net, p in blocks:
        first, last = host_range(net, p)
        lines.append(f"  {int_to_ip(net)}/{p}  {int_to_ip(first)} - {int_to_ip(last)}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="subnetcalc",
        description="Subnet calculator: network, broadcast, host range and splits.",
    )
    parser.add_argument("cidr", help="e.g. 192.168.10.77/26")
    parser.add_argument("--split", type=int, metavar="N",
                        help="split into blocks of prefix length N")
    args = parser.parse_args()

    try:
        ip, prefix = parse_cidr(args.cidr)
        print(format_summary(ip, prefix))
        if args.split is not None:
            print()
            print(format_split(ip, prefix, args.split))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()