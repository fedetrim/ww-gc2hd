#!/bin/zsh
# q.sh LISTFILE [WORKERS]: runs each line of LISTFILE as "python3 verify/chests/vc.py <line>", WORKERS at a
# time (default 3), each run with its own shader cache. Empty lines and lines starting with # are skipped.
#
#   verify/chests/q.sh verify/chests/cases.txt            all 27 cases of the published report (about 30 minutes)
#   grep '^f30_' verify/chests/cases.txt > /tmp/f30.txt && verify/chests/q.sh /tmp/f30.txt
#
# Inputs: the list file; everything vc.py needs (the port built with both test-aid patches, the extracted
# game, research/hd-game/stages.json). Locations and variables: verify/verifyenv.py (WW_PORT_EXE, WW_HD_GAME,
# WW_HD_STAGES, WW_VERIFY_OUT, WW_RESEARCH).
# Outputs, in research/out/verify/chests/: CASE/ (see vc.py) and logs/CASE.out (what vc.py printed).
# If shadercache.bin exists in that folder (copy one from an earlier run), each run starts from a copy of
# it; without it every run compiles its shaders again, which is slower but works.
here=${0:A:h}; root=${here:h:h}; list=${1:A}
out=${WW_VERIFY_OUT:-${WW_RESEARCH:-$root/research}/out/verify}/chests
cd $root
mkdir -p $out/logs
one() { name=${1%% *}; cp -n $out/shadercache.bin $out/shadercache$name.bin 2>/dev/null; eval "python3 ${(q)here}/vc.py $1 --cache $name" > $out/logs/$name.out 2>&1; rm -f $out/shadercache$name.bin; echo "finished $name"; }
n=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  [[ $line == \#* ]] && continue
  one "$line" &
  n=$((n+1))
  if [ $((n % ${2:-3})) -eq 0 ]; then wait; fi
done < $list
wait
