#!/usr/bin/python3
'''
Manages the testing context -- e.g. how much memory we have, keeping track of PTEs that have already been created, etc.
'''

import random
from typing import List, Tuple, Union
from collections import defaultdict
import json5
import json
from sty import fg, bg, ef, RgbBg, rs

from simulator_errors import Errors
from utils import safe_to_bin, safe_to_hex, rsetattr, rgetattr, addr_to_memsize, num_hex_digits
from typeutils import resolve_flag, resolve_int
from core_types import PA, PTE, SATP, VA
from constants import PT_LEVEL_MAP, MAX_PA_MAP, MODE_PAGESIZE_LEVEL_MAP, PA_BITS, PAGESIZE_INT_MAP
from NewTranslator import TranslationWalk, InvalidTranslationWalk

from ConstraintResolver import ConstraintResolver

NullableInt = Union[int, None]

bg.set_style('orange', RgbBg(255, 150, 50))


class Context:
    '''
    Hold our data, and make special & probabilistic test cases
    '''
    def random_address(self):
        return random.randint(self.lower_bound, self.memory_size - 1)

    def valid_address(self, value):
        return value < self.memory_size

    def num_ptes(self, pagesize):
        return self.levels - MODE_PAGESIZE_LEVEL_MAP[self.mode][pagesize]

    def _format_va(self, va_addr: int, colorterm=True):
        if va_addr is None:
            return '***'
        va_digits = num_hex_digits(self.mode)
        va_str = f'{va_addr:#0{va_digits}x}'
        if colorterm and self.va_reference_counter[va_addr] > 1:
            return fg.red + va_str + fg.rs
        return va_str

    def _format_pa(self, pa_addr: int, colorterm=True):
        if pa_addr is None:
            return '***'
        pa_digits = num_hex_digits(PA_BITS[self.mode])
        pa_str = f'{pa_addr:#0{pa_digits}x}'
        if colorterm and self.reference_counter[pa_addr] > 1:
            return fg.red + pa_str + fg.rs
        return pa_str

    def _tw_ministring_err(self, walk: InvalidTranslationWalk, color=True) -> str:
        ppn_width = num_hex_digits(walk.satp.ppn_width)
        # pa_str = self._format_pa(walk.pa.data(), color)
        va_str = self._format_va(walk.va.data(), color) + fg.black
        # if color and walk.pa.data() == walk.va.data(): # Color PA = VA blue bg
        #     pa_str = bg.cyan + pa_str + bg.rs
        #     va_str = bg.cyan + va_str + bg.rs
        pte_entries = ' '.join([self._format_pa(x.address, color) for x in walk.ptes])
        if walk.ptes[-1].get_ppn() is None:
            final_ppn = '???'
        else:
            final_ppn = f'{walk.ptes[-1].get_ppn():#0{ppn_width}x}'
        pte_str = f'=>{pte_entries} {final_ppn}'
        err = fg.red + f' INVALID: {walk.error_type}  ' + fg.black
        base = f'SATP: {walk.satp.ppn:#0{ppn_width}x} VA: {va_str} -> [{pte_str}] {err}'
        # return f'{bg.orange} + {fg.black} + {base} + {fg.rs} + {bg.rs}'
        return bg.orange + fg.black + base + fg.rs + bg.rs


    def _tw_ministring(self, walk: Union[TranslationWalk, InvalidTranslationWalk], color=True) -> str:
        ''' Return a compact one-line representation of the walk '''
        # satp_ppn_digits = num_to44 if walk.mode != 32 else 22
        if type(walk) == InvalidTranslationWalk:
            return self._tw_ministring_err(walk, color)
        ppn_width = num_hex_digits(walk.satp.ppn_width)
        pa_str = self._format_pa(walk.pa.data(), color)
        va_str = self._format_va(walk.va.data(), color)
        if color and walk.pa.data() == walk.va.data(): # Color PA = VA blue bg
            pa_str = bg.cyan + pa_str + bg.rs
            va_str = bg.cyan + va_str + bg.rs
        pte_entries = ' '.join([self._format_pa(x.address, color) for x in walk.ptes])
        final_ppn = f'{walk.ptes[-1].get_ppn():#0{ppn_width}x}'
        pte_str = f'=>{pte_entries} {final_ppn}'
        base = f'SATP: {walk.satp.ppn:#0{ppn_width}x} VA: {va_str} -> [{pte_str}] -> {pa_str}'
        return base

    def __init__(self, memory_size: Union[int, None], mode: int, lower_bound: int = 0, pte_min: int = 0, pte_max: int = None):
        ''' Initialize a ContextManager.
        params:
        size of memory (= the max physical address allowed in the simulation + 1)
        mode = 32 / 39 / 48
        '''
        # TODO: add stuff to classes for bounded randomness issues.
        self.memory_size = memory_size or MAX_PA_MAP[mode]  # 0 is not supported here (duh)
        self.lower_bound = lower_bound
        self.mode = mode
        self.address_table = {
        }  # we'll use this to keep track of PTEs & PAs that have already been allocated and their physical addresses
        self.vas = {}
        self.pas = {}
        self.ptes = {}
        # self.leaves = {}
        self.walks: List[TranslationWalk] = []
        self.levels = PT_LEVEL_MAP[mode]
        self.satps: List[SATP] = []
        self.reference_counter = defaultdict(int)
        self.va_reference_counter = defaultdict(int)
        self.pte_min = pte_min
        self.pte_max = pte_max or self.memory_size
        self.CR = ConstraintResolver(mode=mode, memory_size=self.memory_size, lower_bound=self.lower_bound, pte_min=pte_min, pte_max=pte_max)

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
        # The last one is a leaf, mark that
        # self.leaves[pte.address] = pte
        self.walks.append(walk)
        self.reference_counter[pa.data()] += 1
        self.va_reference_counter[va.data()] += 1
    
    def add_invalid_walk(self, pagesize: str, va: VA, pa: PA, ptes: List[PTE], satp: SATP):
        '''
        Add a translation walk to the context.
        Meant for when it's been specced out already.
        Registers the relevant components in all the relevant lookup tables.
        '''
        walk = InvalidTranslationWalk(self.mode, pagesize, satp, va, pa, ptes)
        walk.resolve(CR=self.CR, pte_hashmap=self.ptes)
        if va.data():
            self.vas[va.data()] = va
            self.va_reference_counter[va.data()] += 1
        # self.address_table[pa.data()] = pa
        # self.pas[pa.data()] = pa
        self.satps.append(satp)
        for pte in ptes:
            if pte.address:
                # may need more checks in terms of marking things
                self.address_table[pte.address] = pte 
                self.ptes[pte.address] = pte
                self.reference_counter[pte.address] += 1
        # The last one is a leaf, mark that
        # self.leaves[pte.address] = pte
        self.walks.append(walk)
        # self.reference_counter[pa.data()] += 1

    def add_test_case(self, same_va_pa: float = 0, reuse_pte: float = 0, aliasing: float = 0, pagesize='4K', va=None, pa=None, **kwargs):
        '''
        Add a test case, with probabilistic usage of 'Testing Knowledge' cases.
        Made in a way that in the future passing JSON into it will be easy. (Through the kwargs)
        Probabilities from 0 to 1 (float).
        '''
        # Step one: create and load everything from the test case

        if (type(pagesize) == list):
            pagesize = random.choice(pagesize)
        
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
            if kwargs.get('satp.ppn'):
                satp = SATP(mode=self.mode, asid=kwargs.get('satp.asid', 0), ppn=kwargs.get('satp.ppn'))
            else:
                satp = SATP(mode=self.mode, **kwargs.get('satp', {})) #asid=kwargs.get('satp.asid', 0), ppn=kwargs.get('satp.ppn'))
        

        ptes = [None] * self.num_ptes(pagesize)
        reuse_pte = resolve_flag(reuse_pte)
        if reuse_pte:  # for now: not allowed with specifying PTE data
            reuse_index = random.randint(0, self.num_ptes(pagesize) - 1)
            # reuse_index = 2
            take_from = random.choice(self.walks)
            random_pte_addr = take_from.ptes[reuse_index].address
            ptes[reuse_index] = self.ptes[random_pte_addr]

            # if reuse_index == 0:
            #     random_pte_addr = random.sample(self.leaves.keys(), 1)[0]
            # else:
            #     for i in range(10):
            #         random_pte_addr = random.sample(self.ptes.keys(), 1)[0]
            #         print(random_pte_addr)
            #         if random_pte_addr not in self.leaves.keys():
            #             break
            #     else:
            #         raise RuntimeError("Could not find a non-leaf")
            #     print(f'picked {random_pte_addr:#x}, {reuse_index}')
        
        elif kwargs.get('ptes'):
            for i, pte_attrs in enumerate(kwargs.get('ptes')):
                address = resolve_int(pte_attrs.get('address'))
                if address in self.ptes.keys(): # check to make sure that we reuse, and don't double define
                    ptes[i] = self.ptes[address]
                else:
                    ptes[i] = PTE(mode=self.mode)
                    ptes[i].address = address
                    if ppns := pte_attrs.get('ppns'):
                        ptes[i].ppn = ppns

                flags = pte_attrs.get('attributes', {})

                for flag, value in flags.items():
                    setattr(ptes[i].attributes, flag, resolve_flag(value))

        # inialize all remaining undefined PTEs
        for i in range(len(ptes)):
            if ptes[i] == None:
                ptes[i] = PTE(mode=self.mode)

        if errs := kwargs.get('errors'):
            use_errs = {}
            prob = errs.get('p')
            err = False
            if prob:
                if resolve_flag(prob): # Do a distribution choice
                    errtype = random.choices(errs.get('types'), errs.get('weights'), k=1)[0]
                    for error in ('mark_invalid', 'write_no_read', 'global_nonglobal', 'leaf_as_pointer', 'uncleared_superpage'):
                        use_errs[error] = 0
                    use_errs[errtype] = 1
            else:
                use_errs = errs
            # V = 0
            if resolve_flag(use_errs.get('mark_invalid')):
                err = True
                ptes[-1].attributes.V = 0
            # W=1, R=0, on the leaf
            if resolve_flag(use_errs.get('write_no_read')):
                err = True
                ptes[-1].attributes.R = 0 
                ptes[-1].attributes.W = 1
            # Global mapping followed by G=0
            if resolve_flag(use_errs.get('global_nonglobal')):
                err = True
                ptes[-2].attributes.G = 1 
                ptes[-1].attributes.G = 0
            # Leaf marked as pointer
            if resolve_flag(use_errs.get('leaf_as_pointer')):
                err = True
                ptes[-1].attributes.R = 0 
                ptes[-1].attributes.X = 0
            # Superpage has data set
            if resolve_flag(use_errs.get('uncleared_superpage')):
                err = True
                ptes[-1].ppn[0] = random.randint(10, 200)
            
            if err:
                self.add_invalid_walk(pagesize, va, pa, ptes, satp)
            else:
                self.add_walk(pagesize, va, pa, ptes, satp)
        else:
            self.add_walk(pagesize, va, pa, ptes, satp)
        
    def dump(self, filename: str):
        ''' Export the full things to a JSON '''
        with open(filename, 'w') as f:
            json.dump(self, f, default=lambda x: x.__dict__)

    def jsonify(self) -> dict:
        ''' Return a minimal JSON friendly thingy'''
        return {
            'mode': self.mode,
            'lower_bound': self.lower_bound,
            'memory_size': self.memory_size,
            'walks': [walk.jsonify() for walk in self.walks]
        }

    def __repr__(self):
        return f'<ContextManager: Sv{self.mode}, Memory Bounds: {self.lower_bound:0x}-{self.memory_size:0x}>'

    def print_dump(self, full_dump=False):
        satp_digits = num_hex_digits(44 if self.mode != 32 else 22) + 2

        print('ContextManager Trace')
        print(
            f'Mode: {self.mode}, MemSize: {self.memory_size:#x} (={addr_to_memsize(self.memory_size)}). Max VA = {2**self.mode - 1:#0x}'
        )
        print()
        if full_dump:
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


def ContextFromJSON(json_data: Union[str, dict]) -> Context:
    ''' Load a JSON5 test config '''
    if type(json_data) == str:
        filename = json_data
        with open(filename) as f:
            params = json5.load(f)
    else:
        params = json_data

    mgr = Context(params.get('memory_size'), params.get('mode'), params.get('lower_bound', 0), params.get('pte_min', 0), params.get('pte_max'))

    test_cases = params.get('test_cases', [])

    for test_case in test_cases:
        if rg := test_case.get('page_range'): # Walrus
            # We do a  mapping of the first page address
            start = rg.get('start', mgr.lower_bound)
            end   = rg.get('end', mgr.memory_size)
            step  = rg.get('step', None)
            num_pages = rg.get('num_pages', None)
            
            current_addr = start
            n_iters = 0
            while current_addr < end and (num_pages is None or n_iters < num_pages):
                for i in range(5): # how many failures we will try before we give up
                    try:
                        mgr.add_test_case(**test_case, pa=current_addr)
                        break
                    except (Errors.SuperPageNotCleared, Errors.InvalidConstraints):
                        pass
                else:
                    raise Errors.InvalidConstraints(f"Couldn't satisfy constraints after {i+1} tries")
                current_addr += step or PAGESIZE_INT_MAP[mgr.walks[-1].pagesize]
                n_iters += 1

        else:
            for i in range(test_case.get('repeats', 1)):
                mgr.add_test_case(**test_case)

    return mgr