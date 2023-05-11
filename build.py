import json
import cw_demangler
import subprocess

def main():
    cw_demangler.rem_itanium = True

    print('Generating JSON symbol map...')

    with open('symbols_CHN.txt') as f:
        symbols = {}
        for line in f:
            addr, name = line.split(' ')
            symbols[int(addr, 16)] = name.strip()

        # Mangled symbols
        with open('symbols_CHN.json', 'w') as f:
            json.dump(symbols, f, indent=4)

        # Demangled symbols
        for addr in symbols:
            symbols[addr] = cw_demangler.demangle(symbols[addr])
        with open('symbols_CHN_rem.json', 'w') as f:
            json.dump(symbols, f, indent=4)

    print('Generating symbol map...')

    subprocess.check_output(
        ['python3', "./wii-code-tools/port_symbol_map.py", 
         'symbols_CHN.json', 'C', 'address-map.txt', 'maps',
         '--output-pattern', 'symbols_$VER$_dolphin.map']
    )
         
    subprocess.check_output(
        ['python3', "./wii-code-tools/port_symbol_map.py", 
         'symbols_CHN_rem.json', 'C', 'address-map.txt', 'maps',
         '--output-pattern', 'symbols_$VER$_rem_ghidra.map',
         '--output_format', 'ghidra']
    )

    print('Done!')

if __name__ == '__main__':
    main()
