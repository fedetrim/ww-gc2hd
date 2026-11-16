#!/bin/bash
# Item 1, helper: grep the GameCube source and the HD source of one unit for a regular expression.
# usage: audit/leftovers/i1_g.sh UNIT REGEX [MAXLINES]        e.g. i1_g.sh d_a_npc_de1 '3940|UNK_3940'
# Inputs: the zeldaret/tww clone (src/) and the wwhd clone (wwhd_src/); locations as in audit/auditenv.py
# (WW_RESEARCH, WW_TWW, WW_WWHD). Output: matching lines on stdout, paths relative to each source tree.
R=${WW_RESEARCH:-$(cd "$(dirname "$0")/../.." && pwd)/research}
H=${WW_WWHD:-$R/wwhd}/wwhd_src; T=${WW_TWW:-$R/tww}/src
echo "=== $1 [$2]"; echo " GC:"
find "$T" -name "$1.cpp" -o -name "$1.inc" | xargs grep -n -E "$2" /dev/null | sed "s|^$T/||" | cut -c1-220 | head -${3:-12}
echo " HD:"
find "$H" -name "$1*.cpp" | xargs grep -n -E "$2" /dev/null | grep -v ":ext 0" | sed "s|^$H/||" | cut -c1-230 | head -${3:-12}
