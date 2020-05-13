#!/usr/bin/python3
'''
Manages the testing context -- e.g. how much memory we have, keeping track of PTEs that have already been created, etc.
'''

import random
from typing import List, Tuple, Union
from collections import defaultdict
import json5
import json
from sty import fg, bg

from utils import safe_to_bin, rsetattr, rgetattr, addr_to_memsize, num_hex_digits
from typeutils import resolve_flag, resolve_int
from core_types import PA, PTE, SATP, VA
from constants import PT_LEVEL_MAP, MAX_PA_MAP, MODE_PAGESIZE_LEVEL_MAP, PA_BITS
from NewTranslator import TranslationWalk

from ConstraintResolver import ConstraintResolver

class ContextManager:
    '''
    Hold our data, and make special & probabilistic test cases
    '''
    def random_address(self):
        return random.randint(0, self.memory_size - 1)

    def valid_address(self, value):
        return value < self.memory_size

    def num_ptes(self, pagesize):
        return self.levels - MODE_PAGESIZE_LEVEL_MAP[self.mode][pagesize]

    def _format_va(self, va_addr: int, colorterm=True):
        va_digits = num_hex_digits(self.mode)
        va_str = f'{va_addr:#0{va_digits}x}'
        if colorterm and self.va_reference_counter[va_addr] > 1:
            return fg.red + va_str + fg.rs
        return va_str

    def _format_pa(self, pa_addr: int, colorterm=True):
        pa_digits = num_hex_digits(PA_BITS[self.mode])
        pa_str = f'{pa_addr:#0{pa_digits}x}'
        if colorterm and self.reference_counter[pa_addr] > 1:
            return fg.red + pa_str + fg.rs
        return pa_str

    def _tw_ministring(self, walk: TranslationWalk, color=True) -> str:
        ''' Return a compact one-line representation of the walk '''
        # satp_ppn_digits = num_to44 if walk.mode != 32 else 22
        ppn_width = num_hex_digits(walk.satp.ppn_width)
        pa_str = self._format_pa(walk.pa.data(), color)
        va_str = self._format_va(walk.va.data(), color)
        if color and walk.pa.data() == walk.va.data(): # Color PA = VA blue bg
            pa_str = bg.cyan + pa_str + bg.rs
            va_str = bg.cyan + va_str + bg.rs
        pte_entries = ' '.join([self._format_pa(x.address, color) for x in walk.ptes])
        pte_str = f'=>{pte_entries} {walk.ptes[-1].get_ppn():#0{ppn_width}x}'
        base = f'SATP: {walk.satp.ppn:#0{ppn_width}x} VA: {va_str} -> [{pte_str}] -> {pa_str}'
        return base

    def __init__(self, memory_size: Union[int, None], mode: int):
        ''' Initialize a ContextManager.
        params:
        size of memory (= the max physical address allowed in the simulation + 1)
        mode = 32 / 39 / 48
        '''
        # TODO: add stuff to classes for bounded randomness issues.
        self.memory_size = memory_size or MAX_PA_MAP[mode]  # 0 is not supported here (duh)
        self.mode = mode
        self.address_table = {
        }  # we'll use this to keep track of PTEs & PAs that have already been allocated and their physical addresses
        self.vas = {}
        self.pas = {}
        self.ptes = {}
        self.walks: List[TranslationWalk] = []
        self.levels = PT_LEVEL_MAP[mode]
        self.satps: List[SATP] = []
        self.reference_counter = defaultdict(int)
        self.va_reference_counter = defaultdict(int)
        self.CR = ConstraintResolver(mode=mode, memory_size=self.memory_size)

    def add_walk(self, pagesize: str, va: VA, pa: PA, ptes: List[PTE], satp: SATP):
        '''
        Add a translation walk to the context.
        Meant for when it's been specced out already.
        Registers the relevant components in all the relevant lookup tables.
        '''
        walk = TranslationWalk(self.mode, pagesize, satp, va, pa, ptes)
        walk.resolve(CR=self.CR, pte_hashmap=self.ptes)
        self.vas[va.data()] = va
        self.address_table[pa.data()] = pa
        self.pas[pa.data()] = pa
        self.satps.append(satp)
        for pte in ptes:
            self.address_table[pte.address] = pte
            self.ptes[pte.address] = pte
            self.reference_counter[pte.address] += 1
        self.walks.append(walk)
        self.reference_counter[pa.data()] += 1
        self.va_reference_counter[va.data()] += 1

    def add_test_case(self, same_va_pa: float = 0, reuse_pte: float = 0, aliasing: float = 0, pagesize='4K', va=None, pa=None, **kwargs):
        '''
        Add a test case, with probabilistic usage of 'Testing Knowledge' cases.
        Made in a way that in the future passing JSON into it will be easy. (Through the kwargs)
        Probabilities from 0 to 1 (float).
        '''
        # Step one: create and load everything from the test case
        
        if resolve_flag(aliasing):  # reuse an existing PA in the system
            pa_addr = random.sample(self.pas.keys(), 1)[0]
            pa = self.pas[pa_addr]
        elif pa in self.pas.keys():
            pa = self.pas[pa]
        else:
            pa = PA(mode=self.mode, data=pa)

        if resolve_flag(same_va_pa) and pa.data():
            va = pa.data()
        
        if va in self.vas.keys():
            va = self.vas[va]
        else:
            va = VA(mode=self.mode, data=va)

        if resolve_flag(same_va_pa):  # same VA and PA
            if pa.data() and va.data():
                pass
            elif pa.data():
                va.set(pa.data())
            else: # TODO: bounds checking!
                va.set(self.random_address())
                pa.set(va.data())
        
        reuse_satp = resolve_flag(kwargs.get('reuse_satp'))
        if reuse_satp:
            satp = random.choice(self.satps)
        else:
            satp = SATP(mode=self.mode, asid=kwargs.get('satp.asid', 0), ppn=kwargs.get('satp.ppn'))
        

        ptes = [None] * self.num_ptes(pagesize)
        reuse_pte = resolve_flag(reuse_pte)
        if reuse_pte:  # for now: not allowed with specifying PTE data
            reuse_index = random.randint(0, self.num_ptes(pagesize) - 1)
            random_pte_addr = random.sample(self.ptes.keys(), 1)[0]  # sample 1 allows using the generator
            ptes[reuse_index] == self.ptes[random_pte_addr]
            # else:
            #     ptes[i] = PTE(mode=self.mode)
        elif kwargs.get('ptes'):
            for i, pte_attrs in enumerate(kwargs.get('ptes')):
                address = resolve_int(pte_attrs.get('address'))
                if address in self.ptes.keys(): # check to make sure that we reuse, and don't double define
                    ptes[i] = self.ptes[address]
                else:
                    ptes[i] = PTE(mode=self.mode)
                    ptes[i].address = address
                    ptes[i].ppns = pte_attrs.get('ppns')

                flags = pte_attrs.get('attributes', {})

                for flag, value in flags.items():
                    setattr(ptes[i].attributes, flag, resolve_flag(value))

        # inialize all remaining undefined PTEs
        for i in range(len(ptes)):
            if not ptes[i]:
                ptes[i] = PTE(mode=self.mode)

        self.add_walk(pagesize, va, pa, ptes, satp)

    def dump(self, filename: str):
        ''' Export the full things to a JSON '''
        with open(filename, 'w') as f:
            json.dump(self, f, default=lambda x: x.__dict__)

    def print_dump(self):
        satp_digits = num_hex_digits(44 if self.mode != 32 else 22) + 2

        print('ContextManager Trace')
        print(
            f'Mode: {self.mode}, MemSize: {self.memory_size:#x} (={addr_to_memsize(self.memory_size)}). Max VA = {2**self.mode:#0x}'
        )
        print()

        print('Virtual Addresses:')
        va_digits = num_hex_digits(self.mode) + 2  # account for the 0x taking up space
        for i, va_address in enumerate(self.vas.keys()):
            print(f'{i}\t{va_address:#0{va_digits}x}')
        print()

        print('Physical Addresses:')
        pa_digits = num_hex_digits(PA_BITS[self.mode]) + 2
        for i, pa_address in enumerate(self.pas.keys()):
            print(f'{i}\t{pa_address:#0{pa_digits}x}')
        print()

        print('PTEs:')
        for i, pte in enumerate(self.ptes.values()):
            print(f'{i}\t{pte.ministring()}')
        print()

        print('SATPs:')
        for i, satp in enumerate(self.satps):
            print(f'{i}\t{satp.ppn:#0{satp_digits}x}')
        print()

        print('Walks:')
        for i, walk in enumerate(self.walks):
            print(f'{i}\t{self._tw_ministring(walk)}')
        print()


def ContextManagerFromJSON(filename: str) -> ContextManager:
    ''' Load a JSON5 test config '''
    with open(filename) as f:
        params = json5.load(f)

    mgr = ContextManager(params.get('memory_size'), params.get('mode'))

    test_cases = params.get('test_cases', [])

    for test_case in test_cases:
        for i in range(test_case.get('repeats', 1)):
            mgr.add_test_case(**test_case)

    return mgr