from simulator_errors import Errors
import random
from typing import Union, List, Tuple
from constants import OFFSET, PAGE_SHIFT
from core_types import PA, PTE, SATP, VA

NullableInt = Union[int, None]


def mask(n: int) -> int:
    # Create a bit mask for n bits
    return 2**n - 1


def _randbits(n: int) -> int:
    return random.randint(0, 2**n - 1)


def equate(x: int, y: int, backing_value: int) -> Tuple[int, int]:
    ''' Check x and y and fill constrained, setting to backing value (chosen by memory context aware generator) if both are undefined. '''
    if x is None and y is None:
        x = backing_value
        y = x
        return x, y
    elif y is None:
        y = x
        return x, y
    elif x is None:
        x = y
        return x, y
    elif x == y:
        return x, y
    else:
        raise Errors.InvalidConstraints(f"Couldn't satisfy constraints: {x} != {y}")


class ConstraintResolver:
    '''
    Convenience class to dispatch the various types of constraints we might need to resolve.

    The main case of special treatment is dispatching the leaf page (where only some are used).
    Also, PAGESIZE is always 2**12 for a non-leaf, and then the leaf is already done differently?

    Change: support memory bounds
    Change: support additional bounds for the PTE range
    '''
    def __init__(self, mode: int, memory_size: int, lower_bound: int = 0, pte_min: int = None, pte_max: int = None):
        self.mode = mode
        self.memory_size = memory_size
        self.lower_bound = lower_bound
        self.pte_min = pte_min
        self.pte_max = pte_max - 1 if type(pte_max) == int else pte_max

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

    @property
    def ALIGNMENT_BITS(self) -> int:
        return 2 if self.mode == 32 else 3

    def _random_pa_address(self) -> int:
        ''' Get a random PA in the memory range '''
        # TODO: maybe incorporate check that it is free?
        return random.randint(self.lower_bound, self.memory_size - 1)

    def _random_pte_address(self) -> int:
        ''' Get a random PTE address in the memory range as well as the PTE range '''
        # TODO: maybe incorporate check that it is free?
        low = max(self.lower_bound, self.pte_min or 0)
        high = min(self.memory_size - 1, self.pte_max or self.memory_size)
        return random.randint(low, high)

    def _chunk_address(self, address: NullableInt, trim_offset: bool = True) -> Union[List[int], List[None]]:
        ''' Break up the number to a list according to the PTE PPN widths '''
        if address is None:
            return [None] * len(self.pte_ppn_widths)

        if trim_offset:
            address >>= OFFSET

        chunked = []
        for width in self.pte_ppn_widths:
            this_value = address & mask(width)
            chunked.append(this_value)
            address >>= width  # shift off the bits that have been assigned

        return chunked

    def _chunk_random_pa_address(self, pte_aligned: bool = True) -> List[int]:
        ''' Use the known PTE field widths to break out a random PA address to an array accordingly '''
        value = self._random_pa_address()  # random bounded PA

        # if we need it PTE aligned, then clear the bits needed for that with a shift-unshift
        if pte_aligned:
            value >>= self.ALIGNMENT_BITS
            value <<= self.ALIGNMENT_BITS

        return self._chunk_address(value, trim_offset=True)

    def _chunk_random_pte_address(self, pte_aligned: bool = True) -> List[int]:
        ''' Use the known PTE field widths to break out a random PA address to an array accordingly '''
        value = self._random_pte_address()  # random bounded PTE PA

        # if we need it PTE aligned, then clear the bits needed for that with a shift-unshift
        if pte_aligned:
            value >>= self.ALIGNMENT_BITS
            value <<= self.ALIGNMENT_BITS

        return self._chunk_address(value, trim_offset=True)

    def _resolve_satp_addr(self, satp: SATP, addr: int) -> int:
        ''' Modify the SATP to fit the constraints '''
        addr = (addr >> PAGE_SHIFT) if addr != None else None
        satp.ppn, addr = equate(satp.ppn, addr, self._random_pte_address() >> PAGE_SHIFT)
        return addr << PAGE_SHIFT

    def _resolve_pte_addr(self, pte: PTE, addr: int, start_level: int = 0) -> int:
        '''
        Goes over the segments of the PTE against the address, filling the constraints as necessary.
        Use a randomly generated valid backing value.
        Returns the address (the high segment, shifted accordingly)
        '''
        offset = 0
        result_address = 0
        # addr = addr >> PAGE_SHIFT if addr != None else None
        for i, (bits, addr_val, randomized_value) in enumerate(
                zip(pte.widths, self._chunk_address(addr), self._chunk_random_pte_address())):
            pte.ppn[i], addr_val = equate(pte.ppn[i], addr_val, randomized_value)
            result_address |= (addr_val << offset)
            offset += bits
        return result_address << PAGE_SHIFT

    def _resolve_pte_pa(self, pte: PTE, pa: PA, final_level):
        for i in range(final_level):  # clear all the low parts
            if pte.ppn[i]:
                raise Errors.SuperPageNotCleared()
            pte.ppn[i] = 0  # must be zero!
        ''' Modify the PTE and PA for the last stage '''
        backing_values = self._chunk_random_pa_address()
        for i in range(final_level, len(pte.widths)):
            pte.ppn[i], pa.ppn[i] = equate(pte.ppn[i], pa.ppn[i], backing_values[i])

    def _resolve_va_addr(self, va: VA, addr: int, vpn_no: int) -> int:
        '''
        Get the VA address on place, the integer segment will be returned.
        Requires the # of the VPN Segment as an argument.
        Returns the low segment of the resulting address.
        '''
        addr_val = addr & mask(OFFSET) if addr != None else None
        if addr_val and addr_val % self.PTESIZE:
            return Errors.UnalignedAddress('VA Address not aligned')
        addr_val = addr_val >> self.ALIGNMENT_BITS if addr_val != None else None
        va.vpn[vpn_no], addr_val = equate(va.vpn[vpn_no], addr_val, random.getrandbits(va.widths[vpn_no]))
        return addr_val << self.ALIGNMENT_BITS

    def _resolve_va_pa_final(self, va: VA, pa: PA, max_page_vpn: int = -1):
        ''' For the final pa := va part, accounting for bigpages. Use -1 for smallest page size (range inclusive) '''
        va.offset, pa.offset = equate(va.offset, pa.offset, random.getrandbits(12))  # offset always 12 bits
        # BOUNDS CHECK: I think this could be bigger than the physical memory (e.g. a 512GB page in Sv48) so we will use a PA bounded source here
        backing_values = self._chunk_random_pa_address()
        for i in range(max_page_vpn + 1):
            va.vpn[i], pa.ppn[i] = equate(va.vpn[i], pa.ppn[i], backing_values[i])

    def _resolve_stage(self, pte: Union[PTE, SATP], va: VA, resulting_address: int, vpn_no: int, PTESIZE: int) -> int:
        '''
        New approach: high and low parts in parallel. We compare the resulting address
        through it being tied to the specific fields in parallel.
        '''
        if type(pte) == PTE:
            hi_result = self._resolve_pte_addr(pte, resulting_address)
        else:
            hi_result = self._resolve_satp_addr(pte, resulting_address)
        lo_result = self._resolve_va_addr(va, resulting_address, vpn_no)
        return hi_result | lo_result

    def _resolve_stage_leaf(self, pte: PTE, va: VA, pa: PA, final_level: int):
        '''
        New approach: high and low parts in parallel. We compare the resulting address
        through it being tied to the specific fields in parallel.
        '''
        self._resolve_pte_pa(pte, pa, final_level)
        self._resolve_va_pa_final(va, pa, final_level - 1)

    # Non leaf pages
    def resolve(self, pte: Union[PTE, SATP], va: VA, resulting_address: int, vpn_no: int) -> int:
        ''' Returns the address, changes the rest inplace. '''
        return self._resolve_stage(pte, va, resulting_address, vpn_no, self.PTESIZE)

    def resolve_leaf(self, pte: PTE, va: VA, pa: PA, level: int):
        self._resolve_stage_leaf(pte, va, pa, level)
