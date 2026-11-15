#!/bin/zsh
# run_marie.sh NAME GCI FILE MODE [prep flags...] : Mrs. Marie scenario (docs/verification/npcs.md, rule 1).
# Converts file FILE (1-3) of the GameCube save GCI with all=MODE (steps | rewards), puts the Joy Pendant on
# button X, noon, start in the school (stage Nitiyou); Link is moved in front of Mrs. Marie, shows the pendant
# (X at 8 s) and answers every message with A until 60 s. Extra flags go to prep.py (--add-pendant for a file
# with no Joy Pendant).
#
#   verify/npcs/run_marie.sh marie-rewards-A samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 rewards
#
# Inputs: a GameCube save (path relative to the repository root or absolute); the native port, the extracted
# game. Locations and variables: verify/verifyenv.py (WW_PORT_EXE, WW_HD_GAME, WW_VERIFY_OUT, WW_RESEARCH).
# Outputs, in research/out/verify/npcs/NAME/: cking.sav, prep.txt, ingame_test.txt, result.txt (analyze.py),
# shots/, contact.png (needs Pillow), run/ (log, si.bin). About 3 minutes.
here=${0:A:h}; ROOT=${here:h:h}
RES=${WW_RESEARCH:-$ROOT/research}
EXE=${WW_PORT_EXE:-$RES/port-src/build/cmake/wwhd}; GAME=${WW_HD_GAME:-$RES/hd-game/game}
V=${WW_VERIFY_OUT:-$RES/out/verify}/npcs
name=$1 gci=$2 file=$3 mode=$4; shift 4
cd $ROOT
mkdir -p $V/$name
python3 $here/prep.py $gci $file $V/$name/cking.sav Nitiyou 0 0 all=$mode --pendant-button --time 12 "$@" > $V/$name/prep.txt 2>&1 || { cat $V/$name/prep.txt; exit 1; }
SHOTS=$(python3 -c "print(','.join(str(3400+30*t) for t in range(7,62,3)))")
PRESS=$(python3 -c "print('8-8.2:2000,'+','.join('%.1f-%.1f:8000'%(t,t+0.2) for t in [12+1.5*i for i in range(32)]))")
rm -rf $V/$name/shots
python3 scripts/ingame_test.py $EXE $GAME $V/$name/cking.sav $V/$name/run 62 \
  "WWHD_LINK_WARP=150:-4:0:-175:-32768" "WWHD_TEST_PRESS=$PRESS" "WWHD_TEST_SCREENSHOT=$SHOTS" "WWHD_SCREENSHOT_DIR=$V/$name/shots" > $V/$name/ingame_test.txt 2>&1
python3 $here/analyze.py $V/$name > $V/$name/result.txt 2>&1
python3 $here/contact.py $V/$name/shots $V/$name/contact.png 4
echo "== $name"; tail -3 $V/$name/prep.txt; cat $V/$name/result.txt
