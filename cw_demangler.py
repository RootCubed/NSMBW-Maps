# Demangler / Itanium remangler for the CodeWarrior ABI

# Adapted from the NVIDIA demangler script by Ninji
# See https://gist.github.com/RootCubed/9ebecf21eec344f10164cdfabbf0bb41 (Python)
# and https://gist.github.com/RootCubed/d7e2629f4576059853505b7931ffd105 (C++)
# for those scripts

from typing import Tuple
import re

dem_regular = False
rem_itanium = False

def parse_numbered(s: str, i: int) -> Tuple[str, int]:
    assert(s[i].isdigit())
    size = 0
    while s[i].isdigit():
        size = size * 10 + int(s[i])
        i += 1
    name = s[i:(i + size)]
    return name, (i + size)


def parse_typename(s: str, i: int, shouldAddNest: bool) -> Tuple[str, int]:
    if s[i] == 'Q':
        count = int(s[i + 1])
        i += 2
        bits = []
        for _ in range(count):
            bit, i = parse_numbered(s, i)
            bit = resolve_templates(bit)
            bits.append(bit)
        if dem_regular:
            return '::'.join(bits), i
        else:
            if shouldAddNest:
                return f'N{"".join(bits)}E', i
            else:
                return ''.join(bits), i
    elif s[i] == 'F':
        return '', i
    else:
        s, i = parse_numbered(s, i)
        return (resolve_templates(s), i)

names_demangle = {
    'v': 'void',
    'b': 'bool',
    'c': 'char',
    's': 'short',
    'i': 'int',
    'l': 'long',
    'x': 'long long',
    'Sc': 'signed char',
    'Uc': 'unsigned char',
    'Us': 'unsigned short',
    'Ui': 'unsigned int',
    'Ul': 'unsigned long',
    'Ux': 'unsigned long long',
    'f': 'float',
    'w': 'wchar_t',
    'e': '...'
}

names_remangle_itanium = {
    'v': 'v',
    'b': 'b',
    'c': 'c',
    's': 's',
    'i': 'i',
    'l': 'l',
    'f': 'f',
    'w': 'w',
    'x': 'x',
    'Sc': 'a',
    'Uc': 'h',
    'Us': 't',
    'Ui': 'j',
    'Ul': 'm',
    'Ux': 'y',
    'e': 'z'
}

def parse_type(s: str, i: int, func_depth: int) -> Tuple[str, int, int]:
    is_ref = False

    type_name = ''
    type_modifier = ''

    while i < len(s) and s[i].isupper():
        c = s[i]
        if c == 'C':
            if dem_regular:
                type_name += 'const '
            else:
                type_name += 'K'
        elif c == 'P':
            add_typename, i, func_depth = parse_type(s, i + 1, 0)
            if dem_regular:
                # hacky solution but it works
                add_ref = '&' if is_ref else ''
                if '$POINTERS$' in add_typename:
                    return type_name + add_typename.replace('$POINTERS$', '*$POINTERS$') + add_ref, i, 0
                else:
                    return type_name + add_typename + '*' + add_ref, i, 0
            else:
                type_name += 'P'
                return type_name + add_typename, i, 0
        elif c == 'R':
            is_ref = True
            if rem_itanium:
                type_name += 'R'
        elif c == 'U':
            type_modifier = 'U'
        elif c == 'S':
            type_modifier = 'S'
        elif c == 'F':
            arg_str = ''
            i += 1
            is_done = False
            while True:
                if s[i] == '_':
                    is_done = True
                    i += 1
                recurse_typename, i, _ = parse_type(s, i, 0)
                if is_done: break
                arg_str += recurse_typename
                if dem_regular:
                    arg_str += ', '
            if dem_regular:
                arg_str = arg_str[:-2] # remove last comma
                type_name += f'{recurse_typename} ($POINTERS$)( {arg_str} )'
            elif rem_itanium:
                type_name += f'F{recurse_typename}{arg_str}E'
            return type_name, i, func_depth
        elif c == 'A':
            count = int(s[i + 1])
            array_type, i, _ = parse_type(s, i + 3, func_depth)
            if dem_regular:
                if array_type.find('[') > -1:
                    split = array_type.split('[', 1)
                    array_type = split[0]
                    other_array_sizes = '[' + split[1]
                    return f'{array_type}[{count}]{other_array_sizes}', i, 0
                return f'{array_type}[{count}]', i, 0
            if rem_itanium:
                return f'A{count}_{array_type}', i, 0
        elif c == 'M':
            if dem_regular or rem_itanium:
                class_name, i, _ = parse_type(s, i + 1, func_depth)
                assert s[i] == 'F'
                arg_str = ''
                i += 1
                is_done = False
                while True:
                    if s[i] == '_':
                        is_done = True
                        i += 1
                    recurse_typename, i, _ = parse_type(s, i, 0)
                    if is_done: break
                    arg_str += recurse_typename
                    if dem_regular:
                        arg_str += ', '
                if dem_regular:
                    arg_str = arg_str[:-2] # remove last comma
                    type_name += f'{recurse_typename} ({class_name}::*$POINTERS$)( {arg_str} )'
                elif rem_itanium:
                    type_name += f'M{class_name}F{recurse_typename}{arg_str}E'
                return type_name, i, func_depth

        elif c == 'Q': # handled by next section
            break
        else:
            raise Exception('Invalid type modifier "' + c + '"')
        i += 1

    if i >= len(s):
        raise Exception(s)

    if not s[i].isalpha() and not s[i].isdigit():
        raise Exception(s)

    c = s[i]
    if c == 'Q' or c.isdigit():
        n, i = parse_typename(s, i, True)
        type_name += n
    else:
        c = type_modifier + c
        if dem_regular: names_to_use = names_demangle
        if rem_itanium: names_to_use = names_remangle_itanium
        if c not in names_to_use:
            raise Exception('Invalid type "' + c + '"')
        type_name += names_to_use[c]
        i += 1

    if dem_regular and is_ref:
        type_name += '&'

    return type_name, i, 0

def resolve_templates(s: str) -> str:
    begin_pos = s.find('<')
    if begin_pos == -1:
        if rem_itanium:
            return str(len(s)) + s
        return s
    template_bit = ''
    i = begin_pos + 1
    while i < len(s):
        if s[i] == ',':
            if dem_regular:
                template_bit += ', '
            i += 1
            continue
        if s[i] == '>':
            break
        elif re.match('[-\d]+[>,]', s[i:]) != None:
            # integer literal in template? uhhhh ok
            literal = re.match('[-\d]+', s[i:])[0]
            if dem_regular:
                template_bit += literal
            else:
                template_bit += 'XLi' + literal.replace('-', 'n') + 'EE'
            i += len(literal)
        else:
            type, i, _ = parse_type(s, i, 0)
            type = type.replace('$POINTERS$', '')
            template_bit += type
    if rem_itanium:
        template_bit = f'I{template_bit}E'
    else:
        template_bit = f'<{template_bit}>'
    if rem_itanium:
        return str(len(s[0:begin_pos])) + s[0:begin_pos] + template_bit
    return s[0:begin_pos] + template_bit

def demangle(s: str) -> str:
    if s.endswith('__'): return s

    split_symbol = re.search('^(..+?)__([CFQ1234567890].+)', s)
    if split_symbol == None: return s

    method = split_symbol.group(1)
    class_name, i = parse_typename(s, len(method) + 2, False)

    local_sym = False
    guard_sym = False
    if (method.startswith('@LOCAL@') or method.startswith('@GUARD@')):
        if method.startswith('@LOCAL'):
            local_sym = True
        else:
            guard_sym = True

        method = re.sub('@(LOCAL|GUARD)@', '', method)

    method = resolve_templates(method)

    is_vtable = False
    if rem_itanium:
        if method == '4__dt':
            method = 'D0'
        elif method == '4__ct':
            method = 'C1'
        elif method == '4__vt':
            method = ''
            is_vtable = True



    demangled = ''
    remangle_is_nested = False

    if dem_regular:
        demangled = class_name
    if class_name != '':
        remangle_is_nested = True
        if dem_regular:
            demangled += '::'


    if dem_regular:
        demangled += method

    is_const = False
    if not i >= len(s) and s[i] == 'C':
        is_const = True
        i += 1

    if dem_regular and i == len(s):
        return demangled
        
    i += 1 # skip over initial F

    param_string = ''
    func_depth = 0
    func_ret_type = ''
    special_sym_end_str = ''
    local_sym_name = ''
    while i < len(s):
        arg = ''
        if s[i] == '@' and (local_sym or guard_sym):
            subs = s[i + 1:].split('@')
            local_sym_name = subs[0]
            if len(subs) == 1:
                special_sym_end_str = str(len(subs[0])) + subs[0] + '_0'
            elif len(subs) == 2:
                special_sym_end_str = str(len(subs[0])) + subs[0] + '_' + subs[1]
            break
        is_ret_val = False
        if s[i] == '_':
            is_ret_val = True
            i += 1
        arg, i, func_depth = parse_type(s, i, func_depth)
        if dem_regular:
            arg = arg.replace('$POINTERS$', '')
        if is_ret_val:
            func_ret_type = arg
            continue
        param_string += arg
        if dem_regular:
            param_string += ', '
    if dem_regular:
        param_string = param_string[:-2] # remove last comma

    if dem_regular:
        demangled += '( ' + param_string + ' )'

        if is_const:
            demangled += ' const'

    if dem_regular:
        if func_ret_type != '':
            demangled = f'{func_ret_type} {demangled}'
        if local_sym:
            return demangled + '::' + local_sym_name
        if guard_sym:
            return f'guard variable for {demangled}'
        return demangled
    else:
        lsbeg = 'Z' if local_sym else ''
        lsend = 'E' if local_sym else ''
        gs = 'GV' if guard_sym else ''
        nesbeg = 'N' if remangle_is_nested else ''
        nesend = 'E' if remangle_is_nested else ''
        cs = 'K' if is_const else ''
        vt = 'TV' if is_vtable else ''
        return f'_Z{lsbeg}{gs}{vt}{nesbeg}{cs}{class_name}{method}{nesend}{func_ret_type}{param_string}{lsend}{special_sym_end_str}'

def demangle_try(s: str) -> str:
    try:
        return demangle(s)
    except Exception as e:
        sys.stderr.write('Demangler error: ' + str(e) + '\n')

import os
import sys

def main():
    global dem_regular, rem_itanium
    if len(sys.argv) < 2:
        dem_regular = True
        while True:
            sym = input()
            print(demangle_try(sym))
    else:
        demang_type = sys.argv[1]
        if demang_type == 'demangle':
            dem_regular = True
        elif demang_type == 'remangle_itanium':
            rem_itanium = True
        else:
            print('Please specify demangling type (demangle or remangle_itanium)')
            return
        
        if len(sys.argv) == 2:
            while True:
                sym = input()
                print(demangle_try(sym))
        else:
            arg = sys.argv[2]
            if not os.path.isfile(arg):
                print(demangle_try(arg))
                return

            with open(arg, 'r') as inputFile:
                lines = tuple(line.strip() for line in inputFile)

            for line in lines:
                line_parts = line.split(' ')
                line_parts[0] = demangle_try(line_parts[0])
                print(' '.join(line_parts))

if __name__ == '__main__':
    main()