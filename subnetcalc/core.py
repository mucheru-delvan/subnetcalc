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