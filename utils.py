#!.usr/bin/python3


def safe_to_hex(value, num_digits: int) -> str:
    if value != None:
        return f'{value:0{num_digits}x}'
    return ' ' * num_digits


def safe_to_bin(value, num_digits: int) -> str:
    if value != None:
        return f'{value:0{num_digits}b}'
    return ' ' * num_digits
