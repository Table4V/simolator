#!.usr/bin/python3
import functools
from typing import Union
import math


def rsetattr(obj, attr, val):
    ''' Recursive get and set attr for using config files '''
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    ''' Recursive get and set attr for using config files '''
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split('.'))


def safe_to_hex(value, num_digits: int) -> str:
    if value != None:
        return f'{value:0{num_digits}x}'
    return ' ' * num_digits


def safe_to_bin(value, num_digits: int) -> str:
    if value != None:
        return f'{value:0{num_digits}b}'
    return ' ' * num_digits


def field_to_string(value, num_bits: int, num_format: str = 'b'):
    if value == None:
        return ' ' * num_bits
    digits = math.ceil(num_bits / 4) if num_format == 'x' else num_bits
    prefix = '0x' if num_format == 'x' else ''
    base = f'{prefix}{value:0{digits}{num_format}}'
    return f'{base:^{num_bits}}'
