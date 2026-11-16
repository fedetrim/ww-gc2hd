#!/usr/bin/env python3
"""Dump every entity chunk (actors, scalable objects, chests, doors, spawn points) of every HD stage, all
layers, with the reader of audit/rewards/stage_all.py.

Inputs:  extracted Wind Waker HD: content/Common/Stage/*.szs and content/Common/Pack/*.pack
Output:  hd_all.json (about 4 MB) in research/out/undo/, or the path given as argument.
Run:     python3 -I audit/undo/hd_all.py [OUT.json]        (about 2 minutes)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.REWARDS)
import stage_all  # noqa: E402
hs, ht, hk = stage_all.hd(auditenv.HD_GAME)
json.dump(hs, open(sys.argv[1] if len(sys.argv) > 1 else auditenv.out_file("undo", "hd_all.json"), "w"))
print("stages", len(hs), "tags", dict(sorted(ht.items())), "skipped", hk)
