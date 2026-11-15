#!/usr/bin/env python3
"""List the sources of the GameCube decompilation that still have undecompiled functions: a function counts as
a stub when its body is only a `/* Nonmatching */` comment.

Inputs:  zeldaret/tww clone: src/{d,f_op,f_pc,f_ap,m_Do,c}/**/*.{cpp,inc,c}
Output:  text on stdout; with --json OUT also {source file: [stub functions, functions]}.
         The other scripts read research/out/machine-code/stubs.json.
Run:     python3 -I audit/machine-code/stubs.py --json research/out/machine-code/stubs.json

The result depends on the commit of zeldaret/tww (the audit used d217e2b: 81 files).
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
ROOT = os.path.join(auditenv.TWW, "src")
pat = re.compile(r"\)\s*(const\s*)?\{\s*/\*\s*Nonmatching[^*]*\*/\s*\}")
out = {}
for sub in ("d", "f_op", "f_pc", "f_ap", "m_Do", "c"):
    for root, _, files in os.walk(os.path.join(ROOT, sub)):
        for fn in files:
            if not fn.endswith((".cpp", ".inc", ".c")): continue
            s = open(os.path.join(root, fn), errors="replace").read()
            n = len(pat.findall(s))
            total = len(re.findall(r"^/\* [0-9A-Fa-f]{8}-[0-9A-Fa-f]{8}", s, re.M))
            if n: out[os.path.relpath(os.path.join(root, fn), ROOT)] = (n, total)
if "--json" in sys.argv:
    json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=0)
for k, (n, t) in sorted(out.items()):
    print("%-40s %3d stub functions of %3d" % (k, n, t))
print(len(out), "files")
