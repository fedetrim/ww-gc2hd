#!/usr/bin/env python3
"""List all entities of one HD stage (optionally one archive: Stage, Room0, ...) from hd_all.json, duplicates
collapsed, with the stage's save record number. Used to read which chests, switches and doors are on the
way to a chest the converter closes again.

Inputs:  hd_all.json in research/out/undo/ (hd_all.py)
Output:  text on stdout: count, archive, chunk, actor name, parameters, aux words, extra bytes.
Run:     python3 -I audit/undo/show.py STAGE [ARC]         e.g. TF_04, or Cave09 Room20
"""
import json, sys, collections, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
d = json.load(open(auditenv.out_file("undo", "hd_all.json")))
st = sys.argv[1]; arc = sys.argv[2] if len(sys.argv) > 2 else None
v = d[st]; print('save_table', v['save_table'])
seen = collections.Counter()
for a in v['ents']:
    if arc is None or a['arc'] == arc:
        seen[(a['arc'], a['layer'], a['name'], a['params'], '/'.join(a['aux']), a['extra'])] += 1
for k, n in seen.items(): print(n, *k)
