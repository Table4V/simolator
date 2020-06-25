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
from simulator_errors import Errors

arch = "RV32"
PageTable = {}

PAGESIZE = 2**12
PAGE_SHIFT = 12


class TranslationWalk:
    pagesize = '4K'
    # va = VA()
    # ptes: List[PTE] = []
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

        global_flag = False # if this is set, then we need to assert that subsequent levels are marked as global, I think
        # First: Deal with SATP one
        self.ptes[0].address = CR.resolve(self.satp, self.va, self.ptes[0].address, self.startLevel)
        if self.ptes[0].address in pte_hashmap.keys():
            self.ptes[0] = pte_hashmap[self.ptes[0].address]

            global_flag = self.ptes[0].assert_global(global_flag)

        # Intermediate PTEs
        for index, level in enumerate(range(self.startLevel - 1, self.endLevel - 1, -1)):
            self.ptes[index + 1].address = CR.resolve(self.ptes[index], self.va, self.ptes[index + 1].address, level)
            if self.ptes[index + 1].address in pte_hashmap.keys():
                self.ptes[index + 1] = pte_hashmap[self.ptes[index + 1].address]
            else:
                self.ptes[index].set_pointer()

            global_flag = self.ptes[index].assert_global(global_flag)
            self.ptes[index].assert_pointer()

        # handle the leaf
        CR.resolve_leaf(self.ptes[-1], self.va, self.pa, self.endLevel)
        if self.ptes[-1].address in pte_hashmap.keys():
            self.ptes[-1] = pte_hashmap[self.ptes[-1].address]

        self.ptes[-1].validate_leaf()
        global_flag = self.ptes[-1].assert_global(global_flag)
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

    def jsonify(self):
        d = {}
        d['mode'] = self.mode
        d['startLevel'] = self.startLevel
        d['endLevel'] = self.endLevel
        d["ptes"] = [pte.jsonify() for pte in self.ptes]
        d['va'] = self.va.jsonify()
        d['pa'] = self.pa.jsonify()
        d['satp'] = self.satp.jsonify()
        return d

    def jsonify_color(self, va_ref_counter: dict, pa_ref_counter: dict):
        d = {}
        d['mode'] = self.mode
        d['startLevel'] = self.startLevel
        d['endLevel'] = self.endLevel
        d["ptes"] = [pte.jsonify() for pte in self.ptes]
        d['va'] = self.va.jsonify()
        d['pa'] = self.pa.jsonify()
        d['satp'] = self.satp.jsonify()

        if self.va.data() == self.pa.data(): # colorize VA = PA
            d['va']['same_va_pa'] = True
            d['pa']['same_va_pa'] = True

        if va_ref_counter[self.va.data()] > 1:
            d['va']['reuse'] = True
        
        if pa_ref_counter[self.pa.data()] > 1:
            d['pa']['reuse'] = True
        
        for pte in d['ptes']:
            if pa_ref_counter[pte['address']] > 1:
                pte['reuse'] = True
        return d


class InvalidTranslationWalk(TranslationWalk):
    def __init__(self, mode=None, pagesize=None, satp=None, va=None, pa=None, ptes=None, error_type=None):
        super().__init__(mode=mode, pagesize=pagesize, satp=satp, va=va, pa=pa, ptes=ptes)
        self.error_type = error_type

    def resolve(self, CR, pte_hashmap=None):
        try:
            super().resolve(CR, pte_hashmap=pte_hashmap)
        except Errors.SuperPageNotCleared:
            self.error_type = 'Superpage not cleared'
        except Errors.PTEMarkedInvalid:
            self.error_type = 'PTE is marked invalid'
        except Errors.WriteNoReadError:
            self.error_type = 'R = 0 & W = 1'
        except Errors.LeafMarkedAsPointer:
            self.error_type = 'Leaf marked as Ptr'
        except Errors.NonGlobalAfterGlobal:
            self.error_type = 'G followed by non-G'
        except:
            print('Unexpected error occurred in execution')
            raise

    def jsonify(self):
        d = super().jsonify()
        d['error_type'] = self.error_type
        return d


    def jsonify_color(self, va_ref_counter: dict, pa_ref_counter: dict):
        d = super().jsonify_color(va_ref_counter, pa_ref_counter)
        d['error_type'] = self.error_type
        return d
