#!/usr/bin/python3
'''
Change in assumptions: we're using a triad system, to handle the constraints

We need to know what's "None" and what's actually defined as something.

'''

import math
import random

from typing import List, Tuple, Union

from core_types import PA, VA, PTE, SATP

arch = "RV32"
PageTable = {}

PAGESIZE = 2**12
PAGE_SHIFT = 12


def mask(n: int) -> int:
    # Create a bit mask for n bits
    return 2**n - 1


# In case we want to switch to Numpy or something else later
def randbits(n: int) -> int:
    return random.getrandbits(n)


class TranslatorError(Exception):
    pass


class InvalidConstraints(Exception):
    pass  # this may be worth moving to a warning if we foresee this being valid?


class InvalidBigPage(Exception):
    pass  # this may be worth moving to a warning if we foresee this being valid?


class UnalignedAddress(Exception):
    pass  # this may be worth moving to a warning if we foresee this being valid?


def equate(x: int, y: int, nbits: int) -> Tuple[int, int]:
    ''' Check x and y and fill constrained, randomizing if not set. '''
    if x is None and y is None:
        x = randbits(nbits)
        y = x
        return x, y
    elif x is not None:
        y = x
        return x, y
    elif y is not None:
        x = y
        return x, y
    elif x == y:
        return x, y
    else:
        raise InvalidConstraints()


def resolve_satp_addr(satp: SATP, addr: int) -> int:
    ''' Modify the SATP to fit the constraints '''
    addr = addr >> PAGE_SHIFT if addr != None else None
    satp.ppn, addr = equate(satp.ppn, addr, satp.ppn_width)
    return addr << PAGE_SHIFT


def resolve_pte_addr(pte: PTE, addr: int, start_level: int = 0) -> int:
    '''
    Goes over the segments of the PTE against the address, filling the constraints as necessary.
    Returns the address (the high segment, shifted accordingly)
    '''
    offset = 0
    result_address = 0
    addr = addr >> PAGE_SHIFT if addr != None else None

    for i, bits in enumerate(pte.widths):
        addr_val = addr & mask(bits) if addr != None else None
        pte.ppn[i], addr_val = equate(pte.ppn[i], addr_val, bits)
        result_address |= (addr_val << offset)
        offset += bits
    return result_address << PAGE_SHIFT


def resolve_pte_pa(pte: PTE, pa: PA, final_level):
    for i in range(final_level):  # clear all the low parts
        if pte.ppn[i]:
            raise InvalidBigPage()
        pte.ppn[i] = 0  # must be zero!
    ''' Modify the PTE and PA for the last stage '''
    for i in range(final_level, len(pte.widths)):
        pte.ppn[i], pa.ppn[i] = equate(pte.ppn[i], pa.ppn[i], pte.widths[i])


def resolve_va_addr(va: VA, addr: int, vpn_no: int, PTESIZE: int, offset_bits: int = PAGE_SHIFT) -> int:
    '''
    Get the VA address on place, the integer segment will be returned.
    Requires the # of the VPN Segment as an argument.
    Returns the low segment of the resulting address.
    '''
    addr_val = addr & mask(offset_bits) if addr != None else None
    if addr_val and addr_val % PTESIZE:
        return UnalignedAddress()
    addr_val = addr_val // PTESIZE if addr_val != None else None
    va.vpn[vpn_no], addr_val = equate(va.vpn[vpn_no], addr_val, va.widths[vpn_no])
    return addr_val * PTESIZE


def resolve_va_pa_final(va: VA, pa: PA, max_page_vpn: int = -1):
    ''' For the final pa := va part, accounting for bigpages. Use -1 for smallest page size (range inclusive) '''
    va.offset, pa.offset = equate(va.offset, pa.offset, 12)  # offset always 12 bits
    for i in range(max_page_vpn + 1):
        va.vpn[i], pa.ppn[i] = equate(va.vpn[i], pa.ppn[i], va.widths[i])


def resolve_stage(pte: Union[PTE, SATP], va: VA, resulting_address: int, vpn_no: int, PTESIZE: int) -> int:
    '''
    New approach: high and low parts in parallel. We compare the resulting address
    through it being tied to the specific fields in parallel.
    '''
    if type(pte) == PTE:
        hi_result = resolve_pte_addr(pte, resulting_address)
    else:
        hi_result = resolve_satp_addr(pte, resulting_address)
    lo_result = resolve_va_addr(va, resulting_address, vpn_no, PTESIZE)
    print(hi_result, lo_result, type(pte))
    return hi_result | lo_result


def resolve_stage_leaf(pte: PTE, va: VA, pa: PA, final_level: int):
    '''
    New approach: high and low parts in parallel. We compare the resulting address
    through it being tied to the specific fields in parallel.
    '''
    resolve_pte_pa(pte, pa, final_level)
    resolve_va_pa_final(va, pa, final_level - 1)


# TODO: maybe come up with some system to avoid the gross none checks?
# TODO: maybe move this to be a function of the mode to avoid the resulting PTE size checks?
def resolve_constraints(pte_component,
                        va_component,
                        resulting_address,
                        pte_bits,
                        va_bits,
                        ra_bits,
                        PAGESIZE=2**12,
                        PTESIZE=4) -> Tuple[int, int, int]:
    '''
    Resolve the constraints using Page * Pagesize + VA * PTESIZE = ResultingAddress.
    Fills values in randomly where there are degrees of freedom.
    '''
    if pte_component != None and va_component != None and resulting_address != None:
        if pte_component * PAGESIZE + va_component * PTESIZE != resulting_address:
            raise InvalidConstraints()
    elif pte_component != None and va_component != None:
        resulting_address = pte_component * PAGESIZE + va_component * PTESIZE
    elif pte_component != None and resulting_address != None:
        va_component = (resulting_address - (pte_component * PAGESIZE)) // PTESIZE
    elif va_component != None and resulting_address != None:
        pte_component = (resulting_address - (va_component * PTESIZE)) // PAGESIZE
    elif resulting_address == None:
        resulting_address = randbits(ra_bits)
        return resolve_constraints(pte_component, va_component, resulting_address, pte_bits, va_bits, ra_bits, PAGESIZE,
                                   PTESIZE)
    elif pte_bits == None:
        pte_component = randbits(pte_bits)
        return resolve_constraints(pte_component, va_component, resulting_address, pte_bits, va_bits, ra_bits, PAGESIZE,
                                   PTESIZE)
    return pte_component, va_component, resulting_address


class ConstraintResolver:
    '''
    Convenience class to dispatch the various types of constraints we might need to resolve.

    The main case of special treatment is dispatching the leaf page (where only some are used).
    Also, PAGESIZE is always 2**12 for a non-leaf, and then the leaf is already done differently?
    '''
    def __init__(self, mode: int):
        self.mode = mode

    @property
    def pte_ppn_widths(self) -> List[int]:
        if self.mode == 32:
            return [10, 12]
        elif self.mode == 39:
            return [9, 9, 26]
        elif self.mode == 48:
            return [9, 9, 9, 17]
        return []

    @property
    def address_size(self) -> int:
        return 34 if self.mode == 32 else 56

    @property
    def satp_ppn_width(self) -> int:
        return 22 if self.mode == 32 else 44

    @property
    def va_bits(self) -> int:
        return 10 if self.mode == 32 else 9

    @property
    def PTESIZE(self) -> int:
        return 4 if self.mode == 32 else 8

    # Non leaf pages
    def resolve(self, pte: Union[PTE, SATP], va: VA, resulting_address: int, vpn_no: int) -> int:
        ''' Returns the address, changes the rest inplace. '''
        return resolve_stage(pte, va, resulting_address, vpn_no, self.PTESIZE)

    def resolve_leaf(self, pte: PTE, va: VA, pa: PA, level: int):
        resolve_stage_leaf(pte, va, pa, level)


class TranslationWalk:
    pageSize = '4K'
    # va = VA()
    ptes = []
    # pa = PA()
    startLevel = 3
    endLevel = 0

    # TODO: check pageSize valid
    def __init__(self,
                 mode=None,
                 pageSize=None,
                 satp: SATP = None,
                 va: VA = None,
                 pa: PA = None,
                 ptes: List[PTE] = None,
                 isLoad=False):
        # if isLoad:
        #     return

        self.mode = mode
        self.pageSize = pageSize
        self.satp = satp
        self.va = va
        self.pa = pa
        self.ptes = ptes
        self.startLevel = self.calculateStartLevel(mode, pageSize)
        self.endLevel = self.calculateEndLevel(mode, pageSize)

    def calculateStartLevel(self, mode, pageSize):
        if mode == 32:
            self.startLevel = 1
        if mode == 39:
            self.startLevel = 2
        if mode == 48:
            self.startLevel = 3
        return self.startLevel

    def calculateEndLevel(self, mode, pageSize):
        if mode == 32:
            self.endLevel = 0 if (pageSize == '4K') else 1
        if mode == 39:
            self.endLevel = 0 if (pageSize == '4K') else 1 if (pageSize == '2M') else 2
        if mode == 48:
            self.endLevel = 0 if (pageSize == '4K') else 1 if (pageSize == '2M') else 2 if (pageSize == '1G') else 3
        return self.endLevel

    def resolve(self):
        '''
        Resolve the Translation Walk, satisfying all set parameters, and filling in randomly where appropriate.

        We're going to use the triad method:
        [SATP PPN, VPN(top) --> Addr(top)]
        [PTE(i), PPN(i) -> Addr(i-1)]
        '''

        CR = ConstraintResolver(mode=self.mode)
        # First: Deal with SATP one
        # print(self.startLevel, self.endLevel)
        self.ptes[0].address = CR.resolve(self.satp, self.va, self.ptes[0].address, self.startLevel)

        # Intermediate PTEs
        for index, level in enumerate(range(self.startLevel, self.endLevel, -1)):
            self.ptes[index + 1].address = CR.resolve(self.ptes[index], self.va, self.ptes[index + 1].address, level)

        # handle the leaf
        CR.resolve_leaf(self.ptes[-1], self.va, self.pa, self.endLevel)
        # self.ptes[-1].broadcast_ppn(ppn)
        # self.pa.set(phys_ppn, mode=self.mode)
        # self.va.set_big_page(self.endLevel, offset)

    def display(self):
        ''' Print the whole thingy out very nicely '''
        print('------------------------------------------------------------------------')
        print(f'Translation Walk: Mode=Sv{self.mode}, PageSize={self.pageSize}')
        print(self.satp)
        print(self.va)
        for pte in self.ptes:
            print(pte)
        print(self.pa)
        print('------------------------------------------------------------------------')
        print()
