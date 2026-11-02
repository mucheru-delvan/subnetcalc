def ip_to_int(ip: str) -> int:
    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError(f"expected 4 octets, got {len(parts)}: {ip!r}")

    result = 0
    for part in parts:
        if not (part.isascii() and part.isdigit()):
            raise ValueError(f"octet is not a number: {part!r}")
        octet = int(part)
        if octet > 255:
            raise ValueError(f"octet out of range 0-255: {octet}")
        result = (result << 8) | octet
    return result


def int_to_ip(n: int) -> str:
    if not 0 <= n <= 0xFFFFFFFF:
        raise ValueError(f"not a 32-bit value: {n}")
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def prefix_to_mask(prefix: int) -> int:
    if not 0 <= prefix <= 32:
        raise ValueError(f"prefix must be 0-32, got {prefix}")
    host_bits = 32 - prefix
    all_ones = (1 << 32) - 1
    return all_ones ^ ((1 << host_bits) - 1)

def network_address(ip: int, prefix: int) -> int:
    return ip & prefix_to_mask(prefix)


def broadcast_address(ip: int, prefix: int) -> int:
    mask = prefix_to_mask(prefix)
    return network_address(ip, prefix) | (~mask & 0xFFFFFFFF)


def host_range(ip: int, prefix: int) -> tuple[int, int]:
    network = network_address(ip, prefix)
    broadcast = broadcast_address(ip, prefix)

    # /32 is a single host: the address is both first and last.
    if prefix == 32:
        return network, network

    # /31 is a point-to-point link (RFC 3021): both addresses are usable,
    # so there is no separate network/broadcast address to skip.
    if prefix == 31:
        return network, broadcast

    # Normal subnet: skip the network address and the broadcast address.
    return network + 1, broadcast - 1

def usable_hosts(prefix: int) -> int:
    if not 0 <= prefix <= 32:
        raise ValueError(f"prefix must be 0-32, got {prefix}")

    # /32 is a single host.
    if prefix == 32:
        return 1

    # /31 is a point-to-point link (RFC 3021): both addresses are usable.
    if prefix == 31:
        return 2

    # Normal subnet: subtract the network and broadcast addresses.
    return 2 ** (32 - prefix) - 2


def split_network(ip: int, prefix: int, new_prefix: int) -> list[tuple[int, int]]:
    if not 0 <= prefix <= 32:
        raise ValueError(f"prefix must be 0-32, got {prefix}")
    if not 0 <= new_prefix <= 32:
        raise ValueError(f"new prefix must be 0-32, got {new_prefix}")
    if new_prefix <= prefix:
        raise ValueError(
            f"new prefix /{new_prefix} must be longer than /{prefix}"
        )

    start = network_address(ip, prefix)
    block_size = 1 << (32 - new_prefix)
    count = 1 << (new_prefix - prefix)

    return [(start + i * block_size, new_prefix) for i in range(count)]