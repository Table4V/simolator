#!/usr/bin/python3
from ContextManager import ContextManager, ContextManagerFromJSON
import sys
import json

fn = sys.argv[1]
mgr = ContextManagerFromJSON(fn)
mgr.print_dump(len(sys.argv) > 2)
# mgr.dump('output.json')

# mgr.dump('output.json')
with open('minout.json', 'w') as f:
    json.dump(mgr.jsonify(), f)
