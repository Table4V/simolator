#!venv/bin/python3

from Context import Context, ContextFromJSON
import sys
import json
import argparse

parser = argparse.ArgumentParser(description='Run a JSON5 input')
parser.add_argument('input', help='JSON5 input file.')
parser.add_argument('output', help='JSON output filename. If omitted, prints to console.', nargs='?')
args = parser.parse_args()

fn = args.input
mgr = ContextFromJSON(fn)

if args.output:
    with open(args.output, 'w') as f:
        json.dump(mgr.jsonify(), f)
else:
    mgr.print_dump()
