#!/usr/bin/python3

from NewTranslator import *

satp = SATP(mode=39)



va = VA(mode=39)
# print(va)
va.set(0x7d_dead_beef, mode=39)
# print(va)
pa = PA(mode=39)
# print(pa)
pa.set(0x7d_dead_beef, mode=39)
# print(pa.ppn)
# print(pa)

ptes = [PTE(mode=39), PTE(mode=39), PTE(mode=39)]
ptes[1].ppn[1] = 0b100011001

walk = TranslationWalk(39, '4K', satp, va, pa, ptes)
walk.display()
walk.resolve()
walk.display()
# walk.resolve()
# walk.display()
