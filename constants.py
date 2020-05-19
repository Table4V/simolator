#!/usr/bin/python3
''' For various minor constants and other stuff '''
PT_LEVEL_MAP = {
    # Number of levels in the page table, we'll use in Context init
    32: 2,
    39: 3,
    48: 4
}

MAX_PA_MAP = {
    # Largest PA possible + 1, used as default in Context init
    32: 2**34,
    39: 2**56,
    48: 2**56
}

OFFSET = 12
PAGE_SHIFT = 12

PA_BITS = {32: 34, 39: 56, 48: 56}

MODE_PAGESIZE_LEVEL_MAP = {
    # Map the mode and the pagesize to the end level
    32: {
        '4K': 0,
        '4M': 1
    },
    39: {
        '4K': 0,
        '2M': 1,
        '1G': 2
    },
    48: {
        '4K': 0,
        '2M': 1,
        '1G': 2,
        '512G': 3
    },
}
PAGESIZE_INT_MAP = {'4K': 2**12, '2M': 2**22, '4M': 2**24, '1G': 2**30, '512G': 2**39}
