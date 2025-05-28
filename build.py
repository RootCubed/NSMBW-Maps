import cw_demangler
import subprocess

def main():
    cw_demangler.rem_itanium = True

    print('Generating JSON symbol map...')

    with open('symbols_CHN.map') as f:
        dem_map = []
        for line in f:
            parts = line.strip().split(' ')
            try:
                parts[4] = cw_demangler.demangle(parts[4])
            except:
                print('Failed to demangle: ' + parts[4])

            dem_map.append(' '.join(parts))

        with open('symbols_CHN_rem.map', 'w') as f:
            f.write('\n'.join(dem_map))

    print('Generating symbol map...')

    subprocess.check_output(
        ['python3', "./wii-code-tools/port_symbol_map.py",
         '--unmapped-address-behavior=drop',
         'symbols_CHN.map', 'C', 'address-map.txt', 'maps',
         '--output-pattern', 'symbols_$VER$_dolphin.map']
    )

    subprocess.check_output(
        ['python3', "./wii-code-tools/port_symbol_map.py",
         '--unmapped-address-behavior=drop',
         'symbols_CHN_rem.map', 'C', 'address-map.txt', 'maps',
         '--output-pattern', 'symbols_$VER$_rem_ghidra.map',
         '--output-format', 'ghidra']
    )

    subprocess.check_output(
        ['python3', './make_objdiff_map.py']
    )

    print('Done!')

if __name__ == '__main__':
    main()
