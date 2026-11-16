# Test aids for the native port

The checks "in the running game" (`docs/DIFFERENCES.md`, Verification) drive
[ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp), a native port that runs the original
Wind Waker HD code from your own copy of the game. Its scenario runner already has test aids, controlled by
environment variables (`runtime/src/test_aids.cpp`): scripted button presses, a one-time warp of Link,
screenshots, a dump of the in-memory save block. Two things the verification needed were missing, so two
small patches add them. Both only touch `runtime/src/test_aids.cpp`, do nothing unless their variable is
set, and are not needed to use the converter or to play.

| Patch | Variable | What it does | Why it is needed |
|---|---|---|---|
| `port-ship-warp.patch` | `WWHD_SHIP_WARP=step:x:z[,step:x:z...]` | moves the boat (and Link in it) to a position on the sea, once per entry, `step` logic steps after gameplay starts | to put the boat on top of a sunken treasure and lower the crane (`scripts/ingame_salvage.py`): sailing there with scripted input is not practical |
| `port-kill-enemies.patch` | `WWHD_KILL_ENEMIES=step[,step...]` | asks the game to delete every loaded enemy actor at the given steps | some chests appear only when their room is empty (Pawprint Isle cave, the lookout platforms, the Ghost Ship ladder). The fights cannot be scripted, so the enemies are removed and the chest's own appear logic runs |

What the aids replace is travel and combat. What is being tested is not touched: the chest, the salvage
point or the character reads the converted save and reacts by the game's own code.

Apply them to a checkout of the port and build it as its README says:

```
cd research/port-src
git apply ../../scripts/port-ship-warp.patch      # first: the second patch builds on it
git apply ../../scripts/port-kill-enemies.patch
cmake --build build/cmake --target wwhd
```

The patches were made against commit `1af1d61` (2026-11-13); on a later commit they may need to be placed by
hand (each is one block inside `before_execute_link`, plus one line in `dumping()`).

License: the port is under the Mozilla Public License 2.0, and these patches modify one of its files, so
they are under the MPL 2.0 as well (https://mozilla.org/MPL/2.0/). The rest of this repository is under the
license in `LICENSE`.
