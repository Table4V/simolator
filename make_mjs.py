#!/usr/bin/python3

import json
import glob

examples = []

for fn in glob.glob('examples/*.json5'):
    with open(fn) as f:
        text = f.read()
        name = fn.split('.')[0].split('/')[1]
        name = name.replace('_', ' ')
        name = name.title()
        examples.append({'name': name, 'data': text })

stmt = 'export const examples = ' + json.dumps(examples)

with open('gui/modules/examples.mjs', 'w') as f:
    f.write(stmt)

