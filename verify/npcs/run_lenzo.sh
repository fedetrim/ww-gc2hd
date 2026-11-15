#!/bin/zsh
# run_lenzo.sh rewards|steps [GCI] [NAME] : Lenzo scenario (docs/verification/npcs.md, rule 2).
# Converts file 1 of GCI (default: sample 01-GZLE-gczelda.gci) with all=MODE, start in Lenzo's shop (stage
# Ocmera), noon, Picto Box on button X, the converter's own album files as Quest Log 1.
#   rewards: X at 8 s shows the Picto Box, A picks the picture and answers every message (60 s).
#   steps:   A talks to Lenzo and answers every message (45 s).
# NAME (default lenzo-MODE) is the output folder.
#
#   verify/npcs/run_lenzo.sh steps
#   verify/npcs/run_lenzo.sh rewards research/out/verify/npcs/lenzo-rewards-legit/input.gci lenzo-rewards-legit
#       (input.gci from make_gci_pictures.py: the current converter writes an album only for pictures the
#       GameCube file owns, and file 1 of the sample owns none; with the plain sample the rewards run has no
#       picture to show)
#
# Inputs: a GameCube save; the native port, the extracted game. Locations and variables: verify/verifyenv.py
# (WW_PORT_EXE, WW_HD_GAME, WW_VERIFY_OUT, WW_RESEARCH).
# Outputs, in research/out/verify/npcs/NAME/: cking.sav, cking_pic*.sav, prep.txt, ingame_test.txt,
# result.txt (analyze.py), shots/, contact.png (needs Pillow), run/ (log, si.bin). About 3 minutes.
here=${0:A:h}; ROOT=${here:h:h}
RES=${WW_RESEARCH:-$ROOT/research}
EXE=${WW_PORT_EXE:-$RES/port-src/build/cmake/wwhd}; GAME=${WW_HD_GAME:-$RES/hd-game/game}
V=${WW_VERIFY_OUT:-$RES/out/verify}/npcs
cd $ROOT
G=${2:-samples/gc/archive-org-memcard-251-us/extracted-gci/01-GZLE-gczelda.gci}
name=${3:-lenzo-$1}
mkdir -p $V/$name
python3 $here/prep.py $G 1 $V/$name/cking.sav Ocmera 0 0 all=$1 --camera-button --album --time 12 > $V/$name/prep.txt 2>&1
if [ $1 = rewards ]; then end=60
  PRESS=$(python3 -c "print('8-8.2:2000,'+','.join('%.1f-%.1f:8000'%(t,t+0.2) for t in [12+2.0*i for i in range(24)]))")
  SHOTS=$(python3 -c "print(','.join(str(3400+15*t) for t in range(14,120,3)))")
else end=45
  PRESS=$(python3 -c "print(','.join('%.1f-%.1f:8000'%(t,t+0.2) for t in [8+2.0*i for i in range(18)]))")
  SHOTS=$(python3 -c "print(','.join(str(3400+15*t) for t in range(14,90,3)))")
fi
rm -rf $V/$name/shots
python3 scripts/ingame_test.py $EXE $GAME $V/$name/cking.sav $V/$name/run $end \
  "WWHD_LINK_WARP=150:-380:0:-259:-16384" "WWHD_TEST_PRESS=$PRESS" "WWHD_TEST_SCREENSHOT=$SHOTS" "WWHD_SCREENSHOT_DIR=$V/$name/shots" > $V/$name/ingame_test.txt 2>&1
python3 $here/analyze.py $V/$name | tee $V/$name/result.txt
python3 $here/contact.py $V/$name/shots $V/$name/contact.png 6
