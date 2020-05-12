#!/usr/bin/python3

from typing import Union, Tuple, List
import random


def resolve_int(value: Union[int, List[int]]) -> int:
    if type(value) == list:
        return random.choice(value)
    return value


def resolve_flag(flag: Union[int, float, None, List[int]]) -> int:
    if type(flag) == float:
        return int(random.random() < flag)
    elif type(flag) == list:
        return random.choice(flag)
    return flag