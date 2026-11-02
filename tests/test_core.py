import ipaddress

import pytest

from subnetcalc.core import (
    broadcast_address,
    host_range,
    int_to_ip,
    ip_to_int,
    network_address,
    networks_overlap,
    prefix_to_mask,
)

NETWORKS = [
    "192.168.10.77/26",
    "10.0.0.5/8",
    "172.16.5.9/20",
    "192.168.1.1/24",
    "10.0.0.5/31",
    "10.0.0.5/32",
    "0.0.0.0/0",
    "128.5.6.7/1",
    "172.31.255.254/16",
    "10.200.3.4/13",
    "192.168.77.200/22",
    "192.168.1.130/25",
    "203.0.113.6/29",
    "203.0.113.6/30",
    "8.8.8.8/32",
    "255.255.255.255/32",
    "1.2.3.4/12",
    "100.64.0.1/10",
    "169.254.10.20/16",
    "192.0.2.255/24",
]


@pytest.mark.parametrize("cidr", NETWORKS)
def test_matches_ipaddress(cidr):
    ip_str, prefix_str = cidr.split("/")
    prefix = int(prefix_str)
    ip = ip_to_int(ip_str)

    ref = ipaddress.ip_network(cidr, strict=False)

    assert prefix_to_mask(prefix) == int(ref.netmask)
    assert int_to_ip(network_address(ip, prefix)) == str(ref.network_address)
    assert int_to_ip(broadcast_address(ip, prefix)) == str(ref.broadcast_address)

    first, last = host_range(ip, prefix)
    if prefix >= 31:
        # /31 and /32 are tiny, so it is safe to list everything.
        expected = list(ref.hosts())
        assert int_to_ip(first) == str(expected[0])
        assert int_to_ip(last) == str(expected[-1])
    else:
        # Don't list hosts() here: for /0 it is over 4 billion addresses.
        assert int_to_ip(first) == str(next(ref.hosts()))
        assert int_to_ip(last) == str(ref.broadcast_address - 1)


@pytest.mark.parametrize("bad_ip", [
    "192.168.10",         # too few octets
    "192.168.10.1.5",     # too many octets
    "192.168.10.256",     # octet out of range
    "192.168.10.abc",     # not a number
    "192.168.10.",        # empty octet
    "192.168.10.-1",      # negative
])
def test_ip_to_int_rejects_bad_input(bad_ip):
    with pytest.raises(ValueError):
        ip_to_int(bad_ip)


@pytest.mark.parametrize("bad_prefix", [-1, 33, 100])
def test_prefix_to_mask_rejects_bad_prefix(bad_prefix):
    with pytest.raises(ValueError):
        prefix_to_mask(bad_prefix)


def test_round_trip():
    for ip in ("0.0.0.0", "192.168.10.0", "255.255.255.255"):
        assert int_to_ip(ip_to_int(ip)) == ip


OVERLAP_CASES = [
    ("192.168.10.0/24", "192.168.10.64/26"),   # contains
    ("192.168.10.64/26", "192.168.10.0/24"),   # inside
    ("192.168.10.0/26", "192.168.10.64/26"),   # adjacent, no overlap
    ("10.0.0.0/8", "10.255.255.255/32"),       # last address of the block
    ("10.0.0.5/32", "10.0.0.5/32"),            # identical /32
    ("10.0.0.0/31", "10.0.0.2/31"),            # adjacent /31s
    ("0.0.0.0/0", "8.8.8.8/32"),               # everything contains everything
    ("172.16.0.0/12", "172.32.0.0/12"),        # just past the end
]


@pytest.mark.parametrize("a, b", OVERLAP_CASES)
def test_overlap_matches_ipaddress(a, b):
    a_ip, a_prefix = a.split("/")
    b_ip, b_prefix = b.split("/")

    mine = networks_overlap(
        ip_to_int(a_ip), int(a_prefix), ip_to_int(b_ip), int(b_prefix)
    )
    ref = ipaddress.ip_network(a, strict=False).overlaps(
        ipaddress.ip_network(b, strict=False)
    )
    assert mine == ref