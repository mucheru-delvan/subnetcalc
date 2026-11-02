# subnetcalc

A subnet calculator CLI in Python. Given a CIDR block, it prints the network address, netmask, broadcast address, host range and usable host count, can split the block into smaller subnets, and can check whether two networks overlap.

The address maths is implemented by hand with integers and bit operations. The standard library's `ipaddress` module is used only in the tests, as an answer key.

## Usage

Run from the repo root:

```bash
python3 -m subnetcalc.cli 192.168.10.77/26
```

```
Network:      192.168.10.64/26
Netmask:      255.255.255.192
Broadcast:    192.168.10.127
Host range:   192.168.10.65 - 192.168.10.126
Usable hosts: 62
```

### Split a network

```bash
python3 -m subnetcalc.cli 192.168.10.0/24 --split 26
```

```
Network:      192.168.10.0/24
Netmask:      255.255.255.0
Broadcast:    192.168.10.255
Host range:   192.168.10.1 - 192.168.10.254
Usable hosts: 254

Split into 4 blocks of /26:
  192.168.10.0/26  192.168.10.1 - 192.168.10.62
  192.168.10.64/26  192.168.10.65 - 192.168.10.126
  192.168.10.128/26  192.168.10.129 - 192.168.10.190
  192.168.10.192/26  192.168.10.193 - 192.168.10.254
```

### Check for overlap

```bash
python3 -m subnetcalc.cli 192.168.10.0/24 --overlaps 192.168.10.64/26
```

```
Overlap check: 192.168.10.0/24 contains 192.168.10.64/26
```

Invalid input prints a one-line error to stderr and exits with status 1.

## How it works

A `/26` means the first 26 bits of the 32-bit address are the network part. The mask is a 32-bit integer with 26 ones followed by 6 zeros:

```
11111111.11111111.11111111.11000000  =  255.255.255.192
```

Everything else follows from AND and OR on that mask.

### Worked example: 192.168.10.77/26

Only the last octet matters, since the first three are fully covered by the mask.

```
77            = 01001101
mask          = 11000000
77 AND mask   = 01000000 = 64    -> network address 192.168.10.64

~mask         = 00111111
64 OR ~mask   = 01111111 = 127   -> broadcast address 192.168.10.127
```

- Network: `192.168.10.64`
- Broadcast: `192.168.10.127`
- Usable hosts: `192.168.10.65` to `192.168.10.126`, which is 2^6 - 2 = 62

### Edge cases

| Prefix | Behaviour |
| ------ | --------- |
| `/31`  | Point-to-point link (RFC 3021): both addresses are usable, so 2 hosts |
| `/32`  | A single host: first and last are the same address, so 1 host |
| `/0`   | Mask is `0.0.0.0`, and the network covers the whole address space |

Overlap detection relies on a property of CIDR: two blocks are either disjoint or one contains the other. Partial overlap cannot happen.

## Project layout

```
subnetcalc/
├── subnetcalc/
│   ├── core.py    # pure integer bit maths, no printing
│   └── cli.py     # argparse and output formatting
└── tests/
    └── test_core.py
```

`core.py` never prints or parses arguments, which keeps the maths easy to test.

## Tests

```bash
python3 -m pytest -v
```

The suite compares the hand-written functions with `ipaddress` on 20 networks (including `/0`, `/1`, `/31`, `/32` and addresses not on a network boundary), checks overlap detection on 8 cases, and checks that bad input raises `ValueError`.

## License

See [LICENSE](LICENSE).