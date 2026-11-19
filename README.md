# ww-gc2hd

Bring your GameCube *Wind Waker* save to *Wind Waker HD* on the Wii U (or Cemu), and keep playing where
you left off.

```
./ww-gc2hd convert "My Save.gci" -o out
```

It shows you what is in the save, asks before converting, writes `out/cking.sav` and prints a report of
everything it changed and why. Your original save is never modified.

You need Python 3.8 or newer and a copy of this repository (`git clone`, or "Download ZIP" on GitHub).
Nothing else to install. On Windows, run it as `python ww-gc2hd convert ...`.

## Why a plain copy is not enough

The two games store a save in almost the same way, so copying it across looks like it works: the file
loads, Link has his items, the map is there.

But HD is not the same game. Nintendo moved some rewards to other places. A save that was fine on the
GameCube can describe a situation that cannot happen in HD, and the game does not notice or repair it.

The worst example is the Triforce. On the GameCube every shard has a **Triforce Chart**: you find the
chart, then salvage the shard from the sea. In HD, for five of the eight (2, 4, 6, 7 and 8), the chest
that held the chart gives you the **Triforce Shard** directly, and the old chart numbers now belong to
ordinary Treasure Charts. So if your GameCube save has
one of those charts and you have not salvaged its shard yet, a plain copy leaves you with:

- the chest already open, so it will never give the shard;
- a Treasure Chart that leads to an ordinary treasure where your Triforce Chart used to lead to the shard;
- no other place in the game that has that shard.

You need all eight shards to reach the end of the game. **That save can no longer be finished**, and
nothing tells you: you find out hours later, when the shard is nowhere.

### The existing converter does exactly this

There is one other converter, `gc2hd.py`, part of the
[ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp) project (read at commit `1af1d61`).
It copies the save field by field and adjusts three things: the save counter, the Tingle Tuner (HD's
Tingle Bottle) and the Deluxe Picto Box at one step of Lenzo's quest. It does not handle any of the chests,
charts or Mrs. Marie's reward, where the two games give different things, and it prints no warning when
your save is in one of them.

You can check it yourself with a real save from this repository,
`samples/gc/pack1/Wind Waker/5th save.gci`. That player opened the Savage Labyrinth chest on floor 30,
got Triforce Chart 6 and had not salvaged the shard yet: a normal mid-game save. We ran `gc2hd.py` on it.
Its line for that file is (player name replaced here):

```
  file 1: 'NAME' -> 'NAME'  [save counter 0 -> 1; Tingle Tuner -> Tingle Bottle (same item number 0x21)]
```

In the file it wrote, the chest is open, Triforce Shard 6 is not held, and the chart is now Treasure
Chart 44. Triforce Shard 6 cannot be obtained in that save.

That is not the only problem. With that converter:

- The **Hero's Charm** can be lost for good, and a **Piece of Heart** can be collected twice, depending
  on what you did in the Savage Labyrinth and with Mrs. Marie.
- **Treasure Charts 42 to 46**, or the sunken treasure they lead to, can be lost: the place that gives
  charts 43 to 46 in HD (three chests and Mrs. Marie's reward) may already be done on the GameCube, and a
  Triforce Chart you had already used turns into one of these charts marked as salvaged.
- Your **Picto Box pictures** are dropped.
- The Sail and the Wind Waker stay on item buttons, where HD never has them.

Its own README reports a test in the game: 26 converted saves show up in the file select, load into
gameplay and have the right hearts, rupees and items. That is true, and it is exactly why the problem
goes unnoticed. It lists Cemu, a Wii U and
saving and reloading in the game as not tested.

To be fair: if your save has not touched any of these places, for example a save from early in the game,
none of the reward problems above arise with that converter. For every field our rules do not touch,
both tools write the same value: we compared them on the 470 used files of the sample cards. (The last two points still apply, along with a few
smaller conventions listed in `docs/DIFFERENCES.md`.) The trouble is that it cannot tell you which kind of
save you have.

### What this tool does instead

- It knows every difference we found between the two games, after comparing them in full
  ([docs/DIFFERENCES.md](docs/DIFFERENCES.md) lists each one with its evidence).
- When your save is in one of those situations, it stops, explains it and lets you choose how to
  resolve it. Either way you end up with a save HD itself could have written.
- Nothing unique is lost and nothing can be collected twice: Triforce Shards, charts, the Hero's Charm,
  Pieces of Heart, the Deluxe Picto Box. A test checks every combination of situations and answers.
- Your Picto Box pictures come along.
- Every situation the tool asks about (listed below) was played in the running game with both answers,
  not only read in code, and the converted samples were loaded in the game. "The game" here is the native
  PC port of Wind Waker HD, which runs the game's own code; loading and saving were repeated in Cemu. On a
  real Wii U one converted save was loaded and looked at; nothing was played there.

## The questions it may ask

Of the 42 healthy USA sample files here, 32 are in none of these situations; a late-game save can be in
several. For each one your save is in, the tool explains it and offers two answers:

- **`steps`**: what you did stays done. You give up what the GameCube gave you there and receive what HD
  gives there. With the floor-50 chest: it stays open, and your Piece of Heart becomes the Hero's Charm.
- **`rewards`**: what you hold stays yours. The place is undone, and the place where HD keeps your reward
  is marked done. With the floor-50 chest, if you do not hold the Hero's Charm: you keep the Piece of
  Heart, and the chest is closed again with the charm inside. A Triforce Chart is the exception, because HD has no chart for that shard: it is dropped
  and its chest is closed again, so you open it in HD and get the shard.

Both are correct saves. There is no default, because it is your save and your call. Some situations
affect each other (the floor-50 chest, Mrs. Marie and the Pawprint chest share rewards), so when the tool
asks, it spells out what each answer means for your save in particular.

To answer in advance, for example in a script, use `--all steps` or `--all rewards`, or one option per
situation:

| Option (`steps` or `rewards`) | Your save is in it when |
|---|---|
| `--triforce-chart-2`, `-4`, `-6`, `-7`, `-8` | you own that Triforce Chart and have not salvaged its shard |
| `--horseshoe-chest`, `--star-belt-chest` | you opened that lookout chest (HD keeps Treasure Chart 43 / 44 there) |
| `--floor50` | you opened the Savage Labyrinth chest on floor 50 (GameCube: Piece of Heart, HD: Hero's Charm) |
| `--pawprint-chest` | you opened the chest in the Pawprint Isle Wizzrobe cave (HD keeps Treasure Chart 46 there). With `--floor50 rewards` the chest stays open and the answer is only about its Silver Rupee |
| `--marie` | Mrs. Marie gave you her reward for 40 Joy Pendants (GameCube: Hero's Charm, HD: Treasure Chart 45) |
| `--lenzo` | Lenzo accepted your third picture and you do not have the Deluxe Picto Box yet |

An answer can differ per file: `--floor50 1=steps,3=rewards`.

## Putting the save on your console

The tool writes `cking.sav` and, if you had pictures, `cking_pic*.sav` files next to it. Copy all of them.

- **Wii U**: restore them with a save manager such as SaveMii.
- **Cemu**: put them in `mlc01/usr/save/00050000/10143500/user/80000001/` (`10143600` for the European
  game).

The save replaces all three Quest Logs of the game. Back up the save you have there first, and remove its
old `cking_pic*` files.

**Which game do you have?** A USA GameCube save is written for the USA version of Wind Waker HD. If your
Wind Waker HD is the European one, add `--hd-region europe`.

## Other options

| Option | What it does |
|---|---|
| `--swift-sail` | turns your Sail into HD's Swift Sail |
| `--hero-mode` | turns on HD's Hero Mode |
| `--name NAME` | changes the player name (up to 8 characters). With several files: `--name 2=Zelda` |
| `--hd-region usa\|europe` | the Wind Waker HD game the save is for. Default: the same region as the GameCube save |
| `--no-pictures` | leaves the Picto Box pictures out |
| `--force` | replaces a save already in the output folder, after moving it to a backup folder there |
| `-y`, `--yes` | skips the "convert this file?" question |
| `--quiet` | does not print the summary of each file |

Two more commands:

```
./ww-gc2hd info   "My Save.gci"     # what a GameCube or HD save holds
./ww-gc2hd verify out/cking.sav     # checks that an HD save is well formed
```

## What it accepts

- **Files**: `.gci`, `.gcs`, `.sav`, or a whole memory card image (Dolphin's `MemoryCardA.USA.raw`, a
  card dump). All three files on the card become Quest Logs 1 to 3.
- **Region**: USA GameCube saves (`GZLE01`). European and Japanese saves are refused unless you add
  `--allow-region`; they convert, but none of the checks were made for them. A Japanese save also needs
  `--hd-region`, because the Japanese Wind Waker HD is not covered.
- **Only saves made by normal play.** A save that was edited, made with glitches, or damaged is left out:
  its Quest Log is written empty and the report says what is wrong with it. The tool does not try to
  repair it. (`convert` then ends with exit status 3 instead of 0. If no file on the card can be
  converted, nothing is written and it ends with status 1.)

In a terminal the output uses colours; set `NO_COLOR` to turn them off. Output sent to a file is plain
text. Without a terminal nothing is asked: if your save is in situations that have no answer yet, the
tool lists them with their options and stops.

## How do I know it is right?

Fair question for a tool that rewrites your save. In short:

- The rules come from reading the code of both games and comparing the data on both discs, place by
  place. They were checked against 257 real GameCube saves and 45 real HD saves.
- Every situation the tool asks about was played in the running game, with both answers. The running
  game is the [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp) native port, built
  from a copy of Wind Waker HD; loading, saving and reloading were repeated in Cemu. These runs start
  next to the place being tested, with test aids, and last seconds to minutes; they are not playthroughs
  (the end of "Verification" in `docs/DIFFERENCES.md`).
- Every healthy USA sample (42 files) was converted and loaded in the game, and 36 of them were saved
  again from the pause menu and compared with what the game wrote.
- On a real Wii U one converted save was loaded and looked at (European game). Nothing was played there.

What is **not** covered is written down too: nothing was played on a console, the European
Wind Waker HD rests on less evidence than the USA one, there is one place where a kept rupee can be
found a second time, and the coloured output was never tried in a Windows console (the tests do run
on Windows). The details, with the evidence for every
claim, are in [docs/DIFFERENCES.md](docs/DIFFERENCES.md); the reports of the runs in the game are in
`docs/verification/`.

## For contributors

`CLAUDE.md` describes how the project is organised and the rules any change must keep.
`docs/SETUP-RESEARCH.md` explains how to set up the game dumps and the tools needed to repeat the research
and the checks in the game. `python3 -m unittest tests.test_wwsave` runs the tests.

The repository holds no game data and no third-party code, except two small patches for the native port
(`scripts/PORT-PATCHES.md`). The saves under `samples/` were shared
publicly by their authors and are kept here with their sources (`samples/SOURCES.md`). If one of them is
yours and you want it removed, open an issue.

## License

MIT (`LICENSE`), for the code and documents of this project. Not covered by it: the saves in `samples/`,
which belong to the people who shared them, and the two patches for the native port in `scripts/`, which
are under the Mozilla Public License 2.0 like the file they modify (`scripts/PORT-PATCHES.md`).

This project is not affiliated with Nintendo. The Legend of Zelda and The Wind Waker are trademarks of
Nintendo.

## Made with AI assistance

The research, the code, the tests, the in-game verification and the documents of this project were made
with the help of an AI coding assistant (Claude, by Anthropic), directed and reviewed by the author. Treat
the claims here like any other: each one in `docs/DIFFERENCES.md` carries its evidence so that it can be
checked, and what was not verified is listed there.
