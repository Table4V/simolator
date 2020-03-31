import math
import random

from xml.dom import minidom
# TODO
# 2. Memory tables range

# Our assumptions:
# 2. We translate a given set of pages, return them, and "die"
# 3. satp is initialized
# 4. page size is given from GUI
# 5. only a single mode is supported (32/39/48)

# Nice to have:
# 2. VA = PA + offset
# 3. support ranges (more then 1 contiguous page)

arch = "RV32"
PageTable = {}


class TranslatorError(Exception):
    pass


class SATP:
    mode = 0
    asid = 0 # Not used currently
    ppn = 0
    ppn_isEmpty = False

    def __init__(self, mode=32, asid=0, ppn_isEmpty=False, ppn=0, isLoad=False):
        if isLoad:
            return
        self.set(mode, asid, ppn_isEmpty, ppn)

    def set(self, mode, asid, ppn_isEmpty, ppn):
        self.mode = mode
        self.asid = asid
        self.ppn = ppn
        self.ppn_isEmpty = ppn_isEmpty

'''
    def set(self, satp, arc):
        if arc == "RV32":
            self.ppn = satp & 0x3FFFFF
            self.mode = (satp >> 31) & 0x1
        else:
            self.ppn = satp & 0xFFFFFFFFFFF
            self.mode = (satp >> 60) & 0xF
'''


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

        def __init__(self):
            pass

        def set(self, attributes):
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
    address = 0
    ppn = []
    attributes = ATTRIBUTES()
    isAddrEmpty = True
    isDataEmpty = True
    mode = 0
    errorMessage = ""
    level = 0

    def __init__(self, level=0, mode=32, isLoad=False):
        if isLoad:
            return
        self.set(level, 0, 0, mode, False)

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

    def data(self):
        pte = self.attributes.V | (self.attributes.R << 1) | (self.attributes.W << 2) | (self.attributes.X << 3) | \
                (self.attributes.U << 4) | (self.attributes.G << 5) | (self.attributes.A << 6) | (self.attributes.D << 7) | (self.attributes.RSW << 8)
        if self.mode == 32:
            pte |= (self.ppn[0] << 10) | (self.ppn[1] << 20)
        if self.mode == 39:
            pte |= (self.ppn[0] << 10) | (self.ppn[1] << 19) | (self.ppn[2] << 28)
        if self.mode == 48:
            pte |= (self.ppn[0] << 10) | (self.ppn[1] << 19) | (self.ppn[2] << 28) | (self.ppn[3] << 37)
        return pte

    def getPpn(self):
        if self.mode == 32:
            return (self.ppn[1] << 10) | self.ppn[0]
        elif self.mode == 39:
            return (self.ppn[2] << 18) | (self.ppn[1] << 9) | self.ppn[0]
        elif self.mode == 48:
            return (self.ppn[3] << 27) | (self.ppn[2] << 18) | (self.ppn[1] << 9) | self.ppn[0]


class VA:
    vpn = []
    offset = 0
    mode = 0
    isEmpty = True
    errorMessage = ""

    def __init__(self, data=0xFFFFFFFFFFFF, mode=32, isLoad=False):
        if isLoad:
            return
        self.vpn = []
        self.set(data, mode)
        self.isEmpty = False

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

    def data(self):
        va = 0
        if not self.isEmpty:
            va = self.offset
            if self.mode == 32:
                va |= (self.vpn[0] << 12) | (self.vpn[1] << 22)
            if self.mode == 39:
                va |= (self.vpn[0] << 12) | (self.vpn[1] << 21) | (self.vpn[2] << 30)
            if self.mode == 48:
                va |= (self.vpn[0] << 12) | (self.vpn[1] << 21) | (self.vpn[2] << 30) | (self.vpn[3] << 39)
        return va


class PA:
    ppn = []
    offset = 0
    mode = 0
    isEmpty = True

    def __init__(self, data=0x12345FFF, mode=32, isLoad=False):
        if isLoad:
            return
        self.set(data, mode)
        self.isEmpty = False
        self.mode = mode

    def set(self, data=0x12345678, mode=32):
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

class TranslationWalk:
    pageSize = '4K'
    va = VA()
    ptes = []
    pa = PA()
    startLevel = 3
    endLevel = 0

# TODO: check pageSize valid
    def __init__(self, mode = None, pageSize=None, va=None, pa=None, ptes=None, isLoad=False):
        if isLoad:
            return

        self.pageSize = pageSize
        self.va = va
        self.ptes = ptes
        self.pa = pa
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
    # TODO: raise exception

class Translator:

    numTranslationWalk = 1
    translationWalks = []
    config = 0
    satp = SATP()
    mode = 32
    minPageSize = pow(2, 12)
    pteSize = 4
    config = 0

    def __init__(self, config=0, isLoad=True):
        if isLoad:
            self.config = config
            return

    def build(self):
        self.calculatePteSize()
        for i in range(0, len(self.translationWalks)):
            self.build_translation_walk(i)

    def clear(self):
        self.numTranslationWalk = 1
        self.translationWalks = []
        self.config = 0
        self.satp = SATP()
        self.mode = 32
        self.minPageSize = pow(2, 12)
        self.pteSize = 4
        self.config = 0



    def load_file(self, file):
        print('Loading translations from %s, wait a minute please' % file)
        ff = Interface()
        ff.load_file(self, file)

    # def writeXML(self):

    def calculatePteSize(self):
        if self.mode == 32:
            self.pteSize = 4
        elif self.mode == 39:
            self.pteSize = 8
        elif self.mode == 48:
            self.pteSize = 8

    def build_translation_walk(self, row):
        # Initialize SATP
        self.set_satp_ppn()
        # If the VA is given as an input, use it. Otherwise, randomize it
        self.set_va(row)
        # If the PA is given as an input, it will be used in the translation creation
        for level in range(self.translationWalks[row].startLevel, self.translationWalks[row].endLevel-1, -1):
            self.set_table(row, level)
        self.set_pa(row)
        self.printTranslationWalk(row)

    def printTranslationWalk(self, row):
        print("SATP: mode = " + str(self.satp.mode) + " PPN = " + str(self.satp.ppn))

        walk = self.translationWalks[row]
        print("(%d) %s : VA = 0x%X" % (row, walk.pageSize,walk.va.data()))
        for pte in reversed(walk.ptes):
            if pte:
                print('   -->     PTE(%s) = 0x%X [0x%X]' % (pte.level, pte.address,pte.data()))
        print("        PA = 0x%X" % walk.pa.data())
        print('***********************************************************************************')

    def set_satp_ppn(self):
        if self.satp.ppn_isEmpty:
            print('SATP[PPN] is empty')
            self.satp.ppn_isEmpty = False
            raise TranslatorError("satp is empty")

    '#a (the name is from the spec book) is next PTE base address'
    def calculate_a(self, pte):
        a = pte.getPpn() * self.minPageSize
        return a

    def calculatePtePpnWidth(self, i):
        if self.mode == 32:
            width = 12 if (i == 1) else 10
        elif self.mode == 39:
            width = 26 if (i == 2) else 9
        elif self.mode == 48:
            width = 17 if (i == 3) else 9
        return width

    def set_pte_addr(self, row, level):
        if self.translationWalks[row].ptes[level].isAddrEmpty:
            if level == self.translationWalks[row].startLevel:
                # First pte
                a = self.satp.ppn * self.minPageSize
            else:
                # not first pte
                a = self.calculate_a(self.translationWalks[row].ptes[level+1])

            self.translationWalks[row].ptes[level].address = a + self.translationWalks[row].va.vpn[level] * self.pteSize
            self.translationWalks[row].ptes[level].isAddrEmpty = False
        else:
            raise TranslatorError("translationWalks[%d].ptes[%d].isAddrEmpty is true" % (row, level))
            # TODO: if pte addr is not empty
            # TODO: legal value of pte address with previous level ppn and vpn[offset]

    def set_pte_data(self, row, level):
        if self.translationWalks[row].ptes[level].isDataEmpty:
            if self.translationWalks[row].ptes[level].address in PageTable:
                self.translationWalks[row].ptes[level] = PageTable[self.translationWalks[row].ptes[level].address]
                self.translationWalks[row].ptes[level].isDataEmpty = False
                return True
            elif level == self.translationWalks[row].endLevel:
                # Leaf pte
                for i in range(self.translationWalks[row].startLevel, level-1, -1):
                    width = self.calculatePtePpnWidth(i)
                    if self.translationWalks[row].pa.isEmpty:
                        self.translationWalks[row].ptes[level].ppn[i] = random.getrandbits(width)
                    else:
                        self.translationWalks[row].ptes[level].ppn[i] = self.translationWalks[row].pa.ppn[i]

                # Prevent arch exception by filling 0's when we're generating a super-page
                for i in range(level-1, -1, -1):
                    self.translationWalks[row].ptes[level].ppn[i] = 0

                self.translationWalks[row].ptes[level].attributes.D = random.getrandbits(1)
                self.translationWalks[row].ptes[level].attributes.A = 1 if self.translationWalks[row].ptes[level].attributes.D == 1 else \
                    random.getrandbits(1)
                self.translationWalks[row].ptes[level].attributes.U = random.getrandbits(1)
                self.translationWalks[row].ptes[level].attributes.X = random.getrandbits(1)
                self.translationWalks[row].ptes[level].attributes.W = random.getrandbits(1)
                self.translationWalks[row].ptes[level].attributes.R = 1 if ((self.translationWalks[row].ptes[level].attributes.X == 0) and
                                                               (self.translationWalks[row].ptes[level].attributes.X == 0)) else \
                    random.getrandbits(1)
                self.translationWalks[row].ptes[level].attributes.RSW = 0
                self.translationWalks[row].ptes[level].attributes.V = 1
                self.translationWalks[row].ptes[level].attributes.G = random.getrandbits(1)

            else:

                # Not a leaf PTE, pointer to next pte
                if self.translationWalks[row].ptes[level-1].isAddrEmpty:
                    for i in range(self.translationWalks[row].startLevel, -1, -1):
                        width = self.calculatePtePpnWidth(i)
                        self.translationWalks[row].ptes[level].ppn[i] = random.getrandbits(width)

                else:
                    raise TranslatorError("table walk not empty")
                    # TODO: do what the user requested
                self.translationWalks[row].ptes[level].attributes.X = 0
                self.translationWalks[row].ptes[level].attributes.W = 0
                self.translationWalks[row].ptes[level].attributes.R = 0
                self.translationWalks[row].ptes[level].attributes.RSW = 0
                self.translationWalks[row].ptes[level].attributes.V = 1
                self.translationWalks[row].ptes[level].attributes.G = random.getrandbits(1)

            self.translationWalks[row].ptes[level].isDataEmpty = False
        else:
            # TODO: if pte data is not empty
            raise TranslatorError("TODO: pte data not empty")

    def set_table(self, row, level):
        if self.translationWalks[row].va.isEmpty:
            raise TranslatorError("VA is empty")

        self.set_pte_addr(row, level)
        self.set_pte_data(row, level)
        self.translationWalks[row].ptes[level].isEmpty = False

    def set_pa(self, row):
        leaf = self.translationWalks[row].endLevel
        self.translationWalks[row].pa.mode = self.mode
        if self.translationWalks[row].pa.isEmpty:
            self.translationWalks[row].pa.isEmpty = False
            if self.translationWalks[row].ptes[leaf].isEmpty:
                #TODO: leaf pte is empty
                raise TranslatorError("TODO: leaf pte is empty")
            else:
                # leaf pte isn't empty
                for i in range(self.translationWalks[row].startLevel, leaf-1, -1):
                    self.translationWalks[row].pa.ppn[i] = self.translationWalks[row].ptes[leaf].ppn[i]

            if self.translationWalks[row].va.isEmpty:
                # We assume that VA is set or randomized before PA
                raise TranslatorError("TODO: VA is empty when we calculate PA")
            else:
                for i in range(leaf-1, -1, -1):
                    self.translationWalks[row].pa.ppn[i] = self.translationWalks[row].va.vpn[i]
                self.translationWalks[row].pa.offset = self.translationWalks[row].va.offset
        else:
            # TODO: move that to set_va, rename to set_va_pa, and finish everything before the translation creation
            # Make sure that the PA offset is the same as the VA offset
            for i in range(leaf - 1, -1, -1):
                if self.translationWalks[row].pa.ppn[i] != self.translationWalks[row].va.vpn[i]:
                    raise TranslatorError("VA offset %d is not the same as PA offset %d"  % (i))
            if self.translationWalks[row].pa.offset != self.translationWalks[row].va.offset:
                raise TranslatorError("VA offset is not the same as PA offset")
            self.translationWalks[row].pa.isEmpty = False

    def set_va(self, row):
        if self.translationWalks[row].va.isEmpty:
            self.translationWalks[row].va.isEmpty = False
            # Randomize the entire VA
            self.translationWalks[row].va.set(random.getrandbits(self.mode), self.mode)
            # If the PA is not empty, use its offset
            if not self.translationWalks[row].pa.isEmpty:
                leaf = self.translationWalks[row].calculateEndLevel(self.mode, self.translationWalks[row].pageSize)
                for i in range(leaf - 1, -1, -1):
                    self.translationWalks[row].va.vpn[i] = self.translationWalks[row].pa.ppn[i]
                self.translationWalks[row].va.offset = self.translationWalks[row].pa.offset
        # Else, nothing to do here, move along


class Interface:

    def save_satp(self, obj, doc):
        elm = doc.createElement("SATP")
        elm.setAttribute("asid", "0x%X" % obj.asid)
        elm.setAttribute("mode", "%d" % obj.mode)
        elm.setAttribute("ppn", "0x%X" % obj.ppn)
        elm.setAttribute("ppnIsEmpty", "%s" % obj.ppn_isEmpty)
        return elm

    def load_satp(self, obj, elm):
        obj.asid = int(elm.getAttribute("asid"), 0)
        obj.mode = int(elm.getAttribute("mode"), 0)
        obj.ppn = int(elm.getAttribute("ppn"), 0)
        obj.ppn_isEmpty = elm.getAttribute("ppn_isEmpty").lower() == "true"

    def save_pte_attr(self, obj, elm):
        elm.setAttribute("v", "%d" % obj.V)
        elm.setAttribute("r", "%d" % obj.R)
        elm.setAttribute("w", "%d" % obj.W)
        elm.setAttribute("x", "%d" % obj.X)
        elm.setAttribute("u", "%d" % obj.U)
        elm.setAttribute("g", "%d" % obj.G)
        elm.setAttribute("a", "%d" % obj.A)
        elm.setAttribute("d", "%d" % obj.D)
        elm.setAttribute("rsw", "%d" % obj.RSW)

    def load_pte_attr(self, obj, elm):
        obj.V = int(elm.getAttribute("v"), 0)
        obj.R = int(elm.getAttribute("r"), 0)
        obj.W = int(elm.getAttribute("w"), 0)
        obj.X = int(elm.getAttribute("x"), 0)
        obj.U = int(elm.getAttribute("u"), 0)
        obj.G = int(elm.getAttribute("g"), 0)
        obj.A = int(elm.getAttribute("a"), 0)
        obj.D = int(elm.getAttribute("d"), 0)
        obj.RSW = int(elm.getAttribute("rsw"), 0)

    def save_pte(self, obj, doc):
        elm = doc.createElement("PTE")
        elm.setAttribute("level", "%d" % obj.level)
        elm.setAttribute("mode", "%d" % obj.mode)
        elm.setAttribute("address", "0x%X" % obj.address)
        elm.setAttribute("errorMessage", obj.errorMessage)
        elm.setAttribute("isAddrEmpty", "%s" % obj.isAddrEmpty)
        elm.setAttribute("isDataEmpty", "%s" % obj.isDataEmpty)
        self.save_pte_attr(obj.attributes, elm)
        for v in obj.ppn:
            v_elm = doc.createElement("PPN")
            v_elm.setAttribute("value", "0x%X" % v)
            elm.appendChild(v_elm)
        return elm

    def load_pte(self, obj, elm):
        obj.level = int(elm.getAttribute("level"), 0)
        obj.mode = int(elm.getAttribute("mode"), 0)
        obj.address = int(elm.getAttribute("address"), 0)
        obj.errorMessage = elm.getAttribute("errorMessage")
        obj.isAddrEmpty = elm.getAttribute("isAddrEmpty").lower() == "true"
        obj.isDataEmpty = elm.getAttribute("isDataEmpty").lower() == "true"
        obj.attributes = PTE.ATTRIBUTES()
        self.load_pte_attr(obj.attributes, elm)
        obj.ppn = []
        for v in elm.getElementsByTagName("PPN"):
            obj.ppn.append(int(v.getAttribute("value"), 0))

    def save_va(self, obj, doc):
        elm = doc.createElement("VA")
        elm.setAttribute("offset", "0x%X" % obj.offset)
        elm.setAttribute("mode", "%d" % obj.mode)
        elm.setAttribute("isEmpty", "%s" % obj.isEmpty)
        for v in obj.vpn:
            v_elm = doc.createElement("VPN")
            v_elm.setAttribute("value", "0x%X" % v)
            elm.appendChild(v_elm)
        return elm

    def load_va(self, obj, elm):
        obj.offset = int(elm.getAttribute("offset"), 0)
        obj.mode = int(elm.getAttribute("mode"), 0)
        obj.isEmpty = elm.getAttribute("isEmpty").lower() == "true"
        obj.vpn = []
        for v in elm.getElementsByTagName("VPN"):
            obj.vpn.append(int(v.getAttribute("value"), 0))

    def save_pa(self, obj, doc):
        elm = doc.createElement("PA")
        elm.setAttribute("mode", "%d" % obj.mode)
        elm.setAttribute("offset", "0x%X" % obj.offset)
        elm.setAttribute("isEmpty", "%s" % obj.isEmpty)
        for v in obj.ppn:
            v_elm = doc.createElement("PPN")
            v_elm.setAttribute("value", "0x%X" % v)
            elm.appendChild(v_elm)
        return elm

    def load_pa(self, obj, elm):
        obj.offset = int(elm.getAttribute("offset"), 0)
        obj.mode = int(elm.getAttribute("mode"), 0)
        obj.isEmpty = elm.getAttribute("isEmpty").lower()  == "true"
        obj.ppn = []
        for v in elm.getElementsByTagName("PPN"):
            obj.ppn.append(int(v.getAttribute("value"), 0))

    def save_translation_walk(self, obj, doc):
        elm = doc.createElement("TranslationWalk")
        elm.setAttribute("pageSize", obj.pageSize)
        elm.setAttribute("startLevel", "%d" % obj.startLevel)
        elm.setAttribute("endLevel", "%d" % obj.endLevel)
        elm.appendChild(self.save_va(obj.va, doc))
        elm.appendChild(self.save_pa(obj.pa, doc))
        for v in obj.ptes:
            if v:
                elm.appendChild(self.save_pte(v, doc))
        return elm

    def load_translation_walk(self, obj, elm):
        obj.pageSize = elm.getAttribute("pageSize")
        obj.startLevel = int(elm.getAttribute("startLevel"), 0)
        obj.endLevel = int(elm.getAttribute("endLevel"), 0)
        obj.va = VA(isLoad=True)
        self.load_va(obj.va, elm.getElementsByTagName("VA")[0])
        obj.pa = PA(isLoad=True)
        self.load_pa(obj.pa, elm.getElementsByTagName("PA")[0])
        obj.ptes = [None, None, None, None]
        for v in elm.getElementsByTagName("PTE"):
            pte = PTE(isLoad=True)
            self.load_pte(pte, v)
            obj.ptes[pte.level] = pte


    def save_translator(self, obj, doc):
        elm = doc.createElement("Translator")
        elm.setAttribute("config", "%d" % obj.config)
        elm.setAttribute("numTranslationWalk", "%d" % len(obj.translationWalks))
        elm.setAttribute("mode", "%d" % obj.mode)
        elm.setAttribute("minPageSize", "%d" % obj.minPageSize)
        elm.setAttribute("pteSize", "%d" % obj.pteSize)
        elm.appendChild(self.save_satp(obj.satp, doc))
        for v in obj.translationWalks:
            elm.appendChild(self.save_translation_walk(v, doc))
        return elm

    def load_translator(self, obj, elm):
        obj.config = int(elm.getAttribute("config"), 0)
        obj.mode = int(elm.getAttribute("mode"), 0)
        obj.minPageSize = int(elm.getAttribute("minPageSize"), 0)
        obj.pteSize = int(elm.getAttribute("pteSize"), 0)
        obj.satp = SATP(isLoad=True)
        self.load_satp(obj.satp, elm.getElementsByTagName("SATP")[0])
        obj.translationWalks = []
        for v in elm.getElementsByTagName("TranslationWalk"):
            tk = TranslationWalk(isLoad=True)
            self.load_translation_walk(tk, v)
            obj.translationWalks.append(tk)

    def load_file(self, translator, fileName):
        doc = minidom.parse(fileName)
        self.load_translator(translator, doc.documentElement)

    def save_file(self, translator, fileName):
        doc = minidom.Document()
        doc.appendChild(self.save_translator(translator, doc))
        txt = doc.toprettyxml()
        doc.unlink()

        text_file = open(fileName, "w")
        text_file.write(txt)
        text_file.close()


# 'MAIN():'

# #seed = random.randint(0, 99999999)
# #random.seed(seed)
# # print('SEED = ' + str(seed))

# ff = Interface()

# try:
#     #translator = Translator()
#     #translator.build()
#     #ff.save_file(translator, "a.xml")
#     new_translator = Translator()
#     new_translator.load_file("a.xml")
#     new_translator.build()
#     ff.save_file(new_translator, "cc.xml")
# except TranslatorError as te:
#     print("ERROR: %s" % te)
