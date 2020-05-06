#!/usr/bin/python3
'''
Change in assumptions: we're using a triad system, to handle the constraints

We need to know what's "None" and what's actually defined as something.

'''

import math
import random

from typing import List, Tuple

arch = "RV32"
PageTable = {}


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
        va_component = (resulting_address - pte_component * PAGESIZE) // PTESIZE
    elif va_component != None and resulting_address != None:
        pte_component = (resulting_address - va_component * PTESIZE) // PAGESIZE
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
    def resolve(self, pte_component, va_component, resulting_address):
        return resolve_constraints(pte_component, va_component, resulting_address, self.satp_ppn_width, self.va_bits,
                                   self.address_size, 2**12, self.PTESIZE)

    def resolve_leaf(self, pte_component, va_component, resulting_address, level):
        ppn_width = sum(self.pte_ppn_widths[level:])  # sum excluding the parts outside is the relevant part here
        pagesize = 2**(12 + sum(self.pte_ppn_widths[:level]))
        return resolve_constraints(pte_component, va_component, resulting_address, ppn_width, self.va_bits,
                                   self.address_size, pagesize,
                                   1)  # calling with a PTESIZE of 1 means that we get the offset math to work


class SATP:
    mode = 0
    asid = 0  # Not used currently
    ppn = None
    ppn_isEmpty = False

    def __init__(self, mode=32, asid=0, ppn_isEmpty=False, ppn=None, isLoad=False):
        if isLoad:
            return
        self.set(mode, asid, ppn_isEmpty, ppn)

    def set(self, mode, asid, ppn_isEmpty, ppn):
        self.mode = mode
        self.asid = asid
        self.ppn = ppn
        self.ppn_isEmpty = ppn_isEmpty

    @property
    def ppn_width(self):
        return 22 if self.mode == 32 else 44

    def __repr__(self):
        mode_flags = {32: 1, 39: 8, 48: 9}.get(self.mode, 0)

        width = 32 if self.mode == 32 else 64
        asid_width = 9 if self.mode == 32 else 16
        mode_str = 'M' if self.mode == 32 else 'Mode'
        ppn_str = ' ' * self.ppn_width if self.ppn is None else f'{self.ppn:0{self.ppn_width}b}'

        top_str = f'|{mode_str}|{"ASID":^{asid_width}}|{"PPN":^{self.ppn_width}}|'
        main_str = f'|{mode_flags:b}|{self.asid:0{asid_width}b}|{ppn_str}|'

        return f'SATP:\n{top_str}\n{main_str}'


class PTE:
    class ATTRIBUTES:
        V = 0
        R = 0
        W = 0
        X = 0
        U = 0
        G = 0
        A = 0
        D = 0
        RSW = 0

        defined = False

        def __init__(self):
            pass

        def set(self, attributes):
            self.defined = True
            self.V = attributes & 0x1
            self.R = (attributes >> 1) & 0x1
            self.W = (attributes >> 2) & 0x1
            self.X = (attributes >> 3) & 0x1
            self.U = (attributes >> 4) & 0x1
            self.G = (attributes >> 5) & 0x1
            self.A = (attributes >> 6) & 0x1
            self.D = (attributes >> 7) & 0x1
            self.RSW = (attributes >> 8) & 0x3

    mode = 0
    address = None
    ppn = [None, None, None, None]
    attributes = ATTRIBUTES()
    isAddrEmpty = True
    isDataEmpty = True
    mode = 0
    errorMessage = ""
    level = 0

    @property
    def widths(self):
        if self.mode == 32:
            return [10, 12]
        elif self.mode == 39:
            return [9, 9, 17]
        elif self.mode == 48:
            return [9, 9, 9, 17]
        return []

    def __init__(self, level=0, mode=32, isLoad=False):
        if isLoad:
            return
        self.mode = mode
        self.level = level
        self.ppn = [None for i in self.widths if i]

    def broadcast_ppn(self, ppn: int, start_level=0):
        for i in range(start_level):
            self.ppn[i] = 0  # leaves are zeroed below the used portion of the ppn
        for i, width in enumerate(self.widths[start_level:], start=start_level):
            if not width:
                return
            self.ppn[i] = ppn & mask(width)
            ppn >>= width  # shift off the bits that've been assigned

        # self.set(level, 0, 0, mode, False)

    def set(self, level, address, data, mode=32, save=True):
        self.level = level
        self.mode = mode
        if address not in PageTable:
            self.address = address
            self.attributes.set(data & 0x3FF)

            if mode == 32:
                self.ppn.append((data >> 10) & 0x3FF)
                self.ppn.append((data >> 20) & 0xFFF)
            if mode == 39:
                self.ppn.append((data >> 10) & 0x1FF)
                self.ppn.append((data >> 19) & 0x1FF)
                self.ppn.append((data >> 28) & 0x3FFFFFF)
            if mode == 48:
                self.ppn.append((data >> 10) & 0x1FF)
                self.ppn.append((data >> 19) & 0x1FF)
                self.ppn.append((data >> 28) & 0x1FF)
                self.ppn.append((data >> 37) & 0x1FFFF)
            if save:
                PageTable[self.address] = self
        elif PageTable[address].data() == data:
            self.address = PageTable[address].address
            self.attributes = PageTable[address].attributes
            self.ppn = PageTable[address].ppn

    @property
    def finalize_random(self):
        for i, bits in enumerate(self.widths):
            if self.ppn[i] is None and bits:
                self.ppn[i] = randbits(bits)

    # New: make it simpler to find whether it is a leaf
    @property
    def leaf(self):
        return self.defined and (self.attributes.X | self.attributes.W | self.attributes.R)

    def data(self):
        return None  # TODO: handle attrs so this can go trhough
        pte = (self.attributes.V | (self.attributes.R << 1) | (self.attributes.W << 2) | (self.attributes.X << 3) |
               (self.attributes.U << 4) | (self.attributes.G << 5) | (self.attributes.A << 6) | (self.attributes.D << 7)
               | (self.attributes.RSW << 8))
        if self.mode == 32:
            pte |= (self.ppn[0] << 10) | (self.ppn[1] << 20)
        if self.mode == 39:
            pte |= (self.ppn[0] << 10) | (self.ppn[1] << 19) | (self.ppn[2] << 28)
        if self.mode == 48:
            pte |= (self.ppn[0] << 10) | (self.ppn[1] << 19) | (self.ppn[2] << 28) | (self.ppn[3] << 37)
        return pte

    def get_ppn(self):
        if None in self.ppn:
            return None
        if self.mode == 32:
            return (self.ppn[1] << 10) | self.ppn[0]
        elif self.mode == 39:
            return (self.ppn[2] << 18) | (self.ppn[1] << 9) | self.ppn[0]
        elif self.mode == 48:
            return (self.ppn[3] << 27) | (self.ppn[2] << 18) | (self.ppn[1] << 9) | self.ppn[0]

    def __repr__(self):
        data_str = f'{self.data():x}' if self.data() != None else '???'
        ppn_str = f'0x{self.get_ppn():x}' if self.get_ppn() != None else '???'
        addr_str = f'{self.address:x}' if self.address != None else '???'
        header = f'PTE: {data_str} ({ppn_str}) @{addr_str}'
        display_line = f'|RSDAGUXWRV|'
        val_line = f'|{" "*10}|'  # TODO: FLAGS
        for i, (width, value) in enumerate(zip(self.widths, self.ppn)):
            name = f'PPN{i}'
            display_line = f'|{name:^{width}}{display_line}'
            vs = ' ' * width if value is None else f'{value:0{width}b}'
            val_line = f'|{vs}{val_line}'

        return f'{header}\n{display_line}\n{val_line}'
        # if self.mode == 32:
        #     return f'<PTE: PPN1:{self.ppn[1]:03x} PPN0:{self.ppn[0]:03x} Leaf={self.leaf}>'
        # elif self.mode == 39:
        #     return f'<PTE: PPN2:{self.ppn[2]:07x} PPN1:{self.ppn[1]:03x} PPN0:{self.ppn[0]:03x} Leaf={self.leaf}>'
        # elif self.mode == 48:
        #     return f'<PTE: PPN3: {self.ppn[3]:03x} PPN2:{self.ppn[2]:03x} PPN1:{self.ppn[1]:03x} PPN0:{self.ppn[0]:03x} Leaf={self.leaf}>'
        # else: # shouldn't have no valid mode
        #     return '<PTE?>'


class VA:
    vpn = []
    offset = None
    mode = 0
    isEmpty = True
    errorMessage = ""

    def __init__(self, data=None, mode=32, isLoad=False):
        if isLoad:
            return
        self.mode = mode
        if data == None:
            self.isEmpty = True
            self.vpn = [None for i in self.widths if i]
        else:
            self.isEmpty = False
            self.set(data, mode)

    def set(self, data=0xFFFFFFFFFFFF, mode=32):
        self.offset = data & 0xFFF
        self.mode = mode
        self.vpn = []

        if mode == 32:
            self.vpn.append((data >> 12) & 0x3FF)
            self.vpn.append((data >> 22) & 0x3FF)
        if mode == 39:
            self.vpn.append((data >> 12) & 0x1FF)
            self.vpn.append((data >> 21) & 0x1FF)
            self.vpn.append((data >> 30) & 0x1FF)
        if mode == 48:
            self.vpn.append((data >> 12) & 0x1FF)
            self.vpn.append((data >> 21) & 0x1FF)
            self.vpn.append((data >> 30) & 0x1FF)
            self.vpn.append((data >> 39) & 0x1FF)
        self.isEmpty = False

    def get_big_page(self, level=3):
        big_offset = self.offset
        width = 0
        for i in range(level):
            width += self.widths[i]
            segment = self.vpn[i]
            big_offset |= segment << width
        return big_offset

    def set_big_page(self, level, data):
        self.offset = data & mask(12)
        data >>= 12
        for i in range(level):
            self.vpn[i] = data & mask(self.widths[i])
            data >>= self.widths[i]  # shift off the bits that've been assigned

    def data(self):
        va = None
        if None not in self.vpn and self.offset != None:
            va = self.offset
            if self.mode == 32:
                va |= (self.vpn[0] << 12) | (self.vpn[1] << 22)
            if self.mode == 39:
                va |= (self.vpn[0] << 12) | (self.vpn[1] << 21) | (self.vpn[2] << 30)
            if self.mode == 48:
                va |= (self.vpn[0] << 12) | (self.vpn[1] << 21) | (self.vpn[2] << 30) | (self.vpn[3] << 39)
        return va

    @property
    def widths(self):
        if self.mode == 32:
            return [10, 10, None, None]
        elif self.mode == 39:
            return [9, 9, 9, None]
        elif self.mode == 48:
            return [9, 9, 9, 9]
        return [None, None, None, None]

    def __repr__(self):
        data_str = f'{self.data():x}' if self.data() != None else '???'
        header = f'VA: {data_str}'
        display_line = f'|{"Offset":^12}|'
        val_line = f'|{self.offset:012b}|' if self.offset != None else f'|{" "*12}|'
        for i, (width, value) in enumerate(zip(self.widths, self.vpn)):
            name = f'VPN{i}'
            display_line = f'|{name:^{width}}{display_line}'
            vs = ' ' * width if value is None else f'{value:0{width}b}'
            val_line = f'|{vs}{val_line}'

        return f'{header}\n{display_line}\n{val_line}'


class PA:
    ppn = []
    offset = None
    mode = 0
    isEmpty = True

    def __init__(self, data=None, mode=32, isLoad=False):
        if isLoad:
            return
        self.mode = mode
        if data:
            self.set(data, mode)
            self.isEmpty = False
        else:
            self.ppn = [None for i in self.widths if i != None]

    def set(self, data=0x12345678, mode=32):
        self.ppn = []
        self.offset = data & 0xFFF
        if mode == 32:
            self.ppn.append((data >> 12) & 0x3FF)
            self.ppn.append((data >> 22) & 0x3FF)
        if mode == 39:
            self.ppn.append((data >> 12) & 0x1FF)
            self.ppn.append((data >> 21) & 0x1FF)
            self.ppn.append((data >> 30) & 0x1FF)
        if mode == 48:
            self.ppn.append((data >> 12) & 0x1FF)
            self.ppn.append((data >> 21) & 0x1FF)
            self.ppn.append((data >> 30) & 0x1FF)
            self.ppn.append((data >> 39) & 0x1FFFF)
        self.isEmpty = False

    def data(self):
        pa = 0
        if not self.isEmpty:
            pa = self.offset
            if self.mode == 32:
                pa |= (self.ppn[0] << 12) | (self.ppn[1] << 22)
            if self.mode == 39:
                pa |= (self.ppn[0] << 12) | (self.ppn[1] << 21) | (self.ppn[2] << 30)
            if self.mode == 48:
                pa |= (self.ppn[0] << 12) | (self.ppn[1] << 21) | (self.ppn[2] << 30) | (self.ppn[3] << 39)
        return pa

    @property
    def widths(self) -> List[int]:
        if self.mode == 32:
            return [10, 12, None, None]
        elif self.mode == 39:
            return [9, 9, 17, None]
        elif self.mode == 48:
            return [9, 9, 9, 17]
        return [None, None, None, None]

    def __repr__(self):
        data_str = f'{self.data():x}' if self.data() != None else '???'
        header = f'PA: {data_str}'
        display_line = f'|{"Offset":^12}|'
        val_line = f'|{self.offset:012b}|' if self.offset != None else f'|{" "*12}|'
        for i, (width, value) in enumerate(zip(self.widths, self.ppn)):
            name = f'PPN{i}'
            display_line = f'|{name:^{width}}{display_line}'
            vs = ' ' * width if value is None else f'{value:0{width}b}'
            val_line = f'|{vs}{val_line}'

        return f'{header}\n{display_line}\n{val_line}'


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
        self.satp.ppn, self.va.vpn[self.startLevel], self.ptes[0].address = CR.resolve(
            self.satp.ppn, self.va.vpn[self.startLevel], self.ptes[0].address)

        # Intermediate PTEs
        for index, level in enumerate(range(self.startLevel, self.endLevel, -1)):
            ppn, self.va.vpn[level - 1], self.ptes[index + 1].address = CR.resolve(self.ptes[index].get_ppn(),
                                                                                   self.va.vpn[level - 1],
                                                                                   self.ptes[index + 1].address)
            self.ptes[index].broadcast_ppn(ppn)

        # handle the leaf
        ppn, offset, phys_ppn = CR.resolve_leaf(self.ptes[-1].get_ppn(), self.va.get_big_page(self.endLevel),
                                                self.pa.data(), self.endLevel)
        self.ptes[-1].broadcast_ppn(ppn)
        self.pa.set(phys_ppn, mode=self.mode)
        self.va.set_big_page(self.endLevel, offset)

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
