import sys

sys.path.append('wii-code-tools')

from lib_wii_code_tools import common
from lib_wii_code_tools import address_maps as lib_address_maps

with open('address-map.txt', 'r', encoding='utf-8') as f:
    mappers = lib_address_maps.load_address_map(f)

mapper_from = mappers['C']
mapper_to = mappers['P1']

start_addrs = [
    ("", 0),
    (".init", 0x80004000, 0x26c0),
    ("extab", 0x800066C0, 0x48),
    ("extabindex", 0x80006720, 0x5c),
    (".text", 0x80006780, 0x2E7550),
    (".ctors", 0x802EDCE0, 0x2E0),
    (".dtors", 0x802EDFC0, 0x10),
    (".rodata", 0x802EDFE0, 0x106B0),
    (".data", 0x802FE6A0, 0x532D0),
    (".bss", 0x80351980, 0xD5FF0),
    (".sdata", 0x80427980, 0x2520),
    (".sbss", 0x80429EA0, 0x14B0),
    (".sdata2", 0x8042B360, 0x4B50),
    (".sbss2", 0x8042FEC0, 0x60),
    ("", 0xFFFFFFFF)
]
curr_sec = 0

eh = lib_address_maps.UnmappedAddressHandling(
        common.ErrorVolume(common.ErrorVolume.default()),
        lib_address_maps.UnmappedAddressHandling.Behavior(lib_address_maps.UnmappedAddressHandling.Behavior.DROP))

res = []
with open('symbols_CHN.map') as f:
    i = 0
    for line in f:
        parts = line.strip().split(' ')
        if len(parts) != 5:
            print('Error: could not parse line: ' + line)
            continue
        addr, size, _, align, name = parts

        if name.startswith('hash_'):
            continue

        addr = int(addr, 16)
        start_mapped_addr = lib_address_maps.map_addr_from_to(
            mapper_from, mapper_to, addr,
            error_handling=eh)
        end_mapped_addr = lib_address_maps.map_addr_from_to(
            mapper_from, mapper_to, addr + int(size, 16) - 1,
            error_handling=eh)
        if start_mapped_addr is None or end_mapped_addr is None:
            continue
        true_size = end_mapped_addr - start_mapped_addr + 1
        if true_size <= 0:
            continue
        if start_mapped_addr >= start_addrs[curr_sec + 1][1]:
            curr_sec += 1
        sec_name = start_addrs[curr_sec][0]
        ty = 'function' if sec_name == '.text' or sec_name == '.init' else 'object'
        if name in ['_rom_copy_info', '_bss_init_info']:
            ty = 'object'
        res.append(f'{name} = {sec_name}:0x{start_mapped_addr:08x}; // type:{ty} size:0x{true_size:x}')
        i += 1

with open('maps/wiimj2d_symbols.txt', 'w') as f:
    f.write('\n'.join(res))
