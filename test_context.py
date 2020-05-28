#!/usr/bin/python3
from ContextManager import ContextManager, ContextManagerFromJSON
import sys

fn = sys.argv[1]
mgr = ContextManagerFromJSON(fn)
mgr.print_dump(len(sys.argv) > 2)
# mgr.dump('output.json')
