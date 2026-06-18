#!/usr/bin/env python3
"""Patch mmcv ext_loader to gracefully handle missing CUDA ops."""
import sys

filepath = '/home/pepe/ai_env/lib/python3.12/site-packages/mmcv/utils/ext_loader.py'

with open(filepath, 'r') as f:
    lines = f.readlines()

new_lines = []
skip_until_return = False
patched = False
for i, line in enumerate(lines):
    # When we see the non-parrots load_ext that does import_module directly
    if "ext = importlib.import_module('mmcv.' + name)" in line and not patched:
        # Replace with try/except version
        indent = '        '
        new_lines.append(indent + 'try:\n')
        new_lines.append(indent + '    ext = importlib.import_module(\'mmcv.\' + name)\n')
        new_lines.append(indent + '    for fun in funcs:\n')
        new_lines.append(indent + '        assert hasattr(ext, fun), f\'{fun} miss in module {name}\'\n')
        new_lines.append(indent + '    return ext\n')
        new_lines.append(indent + 'except Exception as e:\n')
        new_lines.append(indent + '    warnings.warn(f\'mmcv C ext {name} not available, using stubs: {e}\')\n')
        new_lines.append(indent + '    ExtModule = namedtuple(\'ExtModule\', funcs)\n')
        new_lines.append(indent + '    return ExtModule(*[None]*len(funcs))\n')
        patched = True
        # Skip the next lines (for loop, assert, return)
        skip_until_return = True
        continue
    if skip_until_return:
        if 'return ext' in line:
            skip_until_return = False
            continue
        continue
    new_lines.append(line)

with open(filepath, 'w') as f:
    f.writelines(new_lines)

print(f'Patched: {patched}')
print(f'Lines: {len(lines)} -> {len(new_lines)}')

# Verify
with open(filepath, 'r') as f:
    content = f.read()
    print('Has try:', 'try:' in content)
    print('Has except:', 'except Exception' in content)