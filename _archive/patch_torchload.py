#!/usr/bin/env python3
"""Prepend torch.load monkey-patch to MuseTalk app.py"""
import sys

f = '/mnt/seagate/MuseTalk/app.py'
with open(f, 'r') as fh:
    content = fh.read()

patch = """# Monkey-patch torch.load for PyTorch 2.6+ compat
import torch as _torch
_orig_torch_load = _torch.load
def _safe_torch_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _orig_torch_load(*args, **kwargs)
_torch.load = _safe_torch_load

"""

if 'weights_only' not in content:
    with open(f, 'w') as fh:
        fh.write(patch + content)
    print('PATCHED OK')
else:
    print('ALREADY PATCHED')