#!/bin/bash
# run.sh [machine-code] [rewards] [undo] [leftovers]: runs the main scripts of the named audits (all four
# when none is named) in the order audit/README.md gives, and writes every output to research/out/<audit>/
# (or $WW_AUDIT_OUT/<audit>/). The interactive helpers (where.py, flag.py, gcdis.py, npc_*.py, show.py, ...)
# are not run here.
#
#   audit/run.sh                      everything, about 10 minutes
#   audit/run.sh machine-code         about 1 minute
#
# `leftovers` needs the outputs of `machine-code` and `rewards`; `undo` needs nothing from the others.
# Inputs and their locations: audit/auditenv.py and docs/SETUP-RESEARCH.md.
set -e
A=$(cd "$(dirname "$0")" && pwd)
R=${WW_RESEARCH:-$(dirname "$A")/research}
OUT=${WW_AUDIT_OUT:-$R/out}
py() { python3 -I "$@"; }

machine_code() {
  local a=$A/machine-code o=$OUT/machine-code; mkdir -p "$o"
  py "$a/gc_extract.py"                                   # -> gc_calls.json
  py "$a/hd_extract.py"                                   # -> hd_calls.json
  py "$a/stubs.py" --json "$o/stubs.json" > "$o/stubs.txt"
  py "$a/validate.py"    > "$o/validate.txt"
  py "$a/compare.py"     > "$o/diff_all.txt"
  py "$a/compare.py" --global > "$o/global_diff.txt"
  py "$a/funcdiff.py"    > "$o/funcdiff.txt"
  py "$a/rewards.py" --all > "$o/rewards_all.txt"
  py "$a/gtitm.py"       > "$o/gtitm.txt"
  py "$a/tables_all.py"  > "$o/tables_all.txt"
  py "$a/stub_table.py"  > "$o/stub_table.md"
}

rewards() {
  local a=$A/rewards o=$OUT/rewards; mkdir -p "$o"
  py "$a/stage_all.py"   > "$o/stage_all.txt"             # -> stage_all.json
  py "$a/stage_cmp.py"   > "$o/stage_cmp.txt"
  py "$a/stage_types.py" > "$o/stage_types.txt"
  py "$a/totals.py"      > "$o/totals.txt"
  py "$a/rando_tables.py" > "$o/rando_tables.txt"         # -> rando_tables.json
  py "$a/rando_match.py" > "$o/rando_match.txt"           # -> rando_pairs.json
  py "$a/rando_final.py" > "$o/rando_final.txt"
  py "$a/reach.py"       > "$o/reach.txt"
  py "$a/reach_hd.py"    > "$o/reach_hd.txt"
  py "$a/gc_only_stages.py" > "$o/gc_only_stages.txt"
  py "$a/misc_tables.py" > "$o/misc_tables.txt"
  py "$a/item_table.py"  > "$o/item_table.txt"
  py "$a/item_tables.py" > "$o/item_tables.txt"
  for s in dump callers mdata tables2 tables3; do py "$a/shops_$s.py" > "$o/shops_$s.txt"; done
}

undo() {
  mkdir -p "$OUT/undo"
  py $A/undo/hd_all.py > "$OUT/undo/hd_all.txt"         # -> hd_all.json
}

leftovers() {
  local a=$A/leftovers o=$OUT/leftovers; mkdir -p "$o"
  py "$a/i1_sites.py"    > "$o/i1_sites.txt"
  py "$a/i1_auto.py"     > "$o/i1_auto.txt"
  py "$a/i1_ctx.py" "" 3 > "$o/i1_ctx.txt"
  py "$a/i67_actordat.py" > "$o/i67_actordat.txt"
  py "$a/i67_tags.py"    > "$o/i67_tags.txt"
  py "$a/i67_cmp.py"     > "$o/i67_cmp.txt"
  py "$a/i67_evlist.py"  > "$o/i67_evlist.txt"
  py "$a/i8_direct.py"   > "$o/i8_direct.txt"             # -> i8_direct.json
  py "$a/i8_cmp.py" all  > "$o/i8_all.txt"
  py "$a/i8_cmp.py"      > "$o/i8_stubs.txt"
  py "$a/i8_src.py"      > "$o/i8_src.txt"
}

[ $# -eq 0 ] && set -- machine-code rewards undo leftovers
for x in "$@"; do
  case $x in
    machine-code) machine_code ;; rewards) rewards ;; undo) undo ;; leftovers) leftovers ;;
    *) echo "unknown audit: $x (machine-code, rewards, undo, leftovers)" >&2; exit 2 ;;
  esac
  echo "$x: done, outputs in $OUT/$x"
done
