#!/usr/bin/python3
'''
Change in assumptions: we're using a triad system, to handle the constraints

We need to know what's "None" and what's actually defined as something.

May 13th: Change to CR to allow for memory bounds
'''

import math
import random

from typing import List, Tuple, Union

from core_types import PA, VA, PTE, SATP

from utils import num_hex_digits

from ConstraintResolver import ConstraintResolver

arch = "RV32"
PageTable = {}

PAGESIZE = 2**12
PAGE_SHIFT = 12


class TranslationWalk:
    pagesize = '4K'
    # va = VA()
    ptes = []
    # pa = PA()
    startLevel = 3
    endLevel = 0

    # TODO: check pagesize valid
    def __init__(self,
                 mode=None,
                 pagesize=None,
                 satp: SATP = None,
                 va: VA = None,
                 pa: PA = None,
                 ptes: List[PTE] = None):
        self.mode = mode
        self.pagesize = pagesize
        self.satp = satp
        self.va = va
        self.pa = pa
        self.ptes = ptes
        self.startLevel = self.calculateStartLevel(mode, pagesize)
        self.endLevel = self.calculateEndLevel(mode, pagesize)

    def calculateStartLevel(self, mode, pagesize):
        if mode == 32:
            self.startLevel = 1
        if mode == 39:
            self.startLevel = 2
        if mode == 48:
            self.startLevel = 3
        return self.startLevel

    def calculateEndLevel(self, mode, pagesize):
        if mode == 32:
            self.endLevel = 0 if (pagesize == '4K') else 1
        if mode == 39:
            self.endLevel = 0 if (pagesize == '4K') else 1 if (pagesize == '2M') else 2
        if mode == 48:
            self.endLevel = 0 if (pagesize == '4K') else 1 if (pagesize == '2M') else 2 if (pagesize == '1G') else 3
        return self.endLevel

    def resolve(self, CR: ConstraintResolver, pte_hashmap: Union[dict, None] = None):
        '''
        Resolve the Translation Walk, satisfying all set parameters, and filling in randomly where appropriate.

        We're going to use the triad method:
        [SATP PPN, VPN(top) --> Addr(top)]
        [PTE(i), PPN(i) -> Addr(i-1)]
        Pass a PTE hashmap for it to find already defined variables
        '''

        pte_hashmap = pte_hashmap or {}

        # CR = ConstraintResolver(mode=self.mode)
        # First: Deal with SATP one
        self.ptes[0].address = CR.resolve(self.satp, self.va, self.ptes[0].address, self.startLevel)
        if self.ptes[0].address in pte_hashmap.keys():
            self.ptes[0] = pte_hashmap[self.ptes[0].address]

        # Intermediate PTEs
        for index, level in enumerate(range(self.startLevel - 1, self.endLevel - 1, -1)):
            self.ptes[index + 1].address = CR.resolve(self.ptes[index], self.va, self.ptes[index + 1].address, level)
            if self.ptes[index + 1].address in pte_hashmap.keys():
                self.ptes[index + 1] = pte_hashmap[self.ptes[index + 1].address]
            else:
                self.ptes[index].set_pointer()

        # handle the leaf
        CR.resolve_leaf(self.ptes[-1], self.va, self.pa, self.endLevel)
        if self.ptes[-1].address in pte_hashmap.keys():
            self.ptes[-1] = pte_hashmap[self.ptes[-1].address]

        
        # assert self.va.data() != None, self.display()
        # self.ptes[-1].broadcast_ppn(ppn)
        # self.pa.set(phys_ppn, mode=self.mode)
        # self.va.set_big_page(self.endLevel, offset)

    def display(self, format_code='x'):
        ''' Print the whole thingy out very nicely '''
        print('------------------------------------------------------------------------')
        print(f'Translation Walk: Mode=Sv{self.mode}, PageSize={self.pagesize}')

        for stage in [self.satp, self.va, *self.ptes, self.pa]:
            print(format(stage, format_code))

        print('------------------------------------------------------------------------')
        print()
