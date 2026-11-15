# Wind Waker save samples: sources and provenance

Collected 2026-11-14. Everything here was only downloaded and extracted; nothing from the
downloads was executed. `gc/pack1` and `gc/cryze` were already present; their sources were identified
afterwards (table below) and confirmed by downloading them again and comparing checksums
(`scripts/fetch_samples.py`).

Checks applied:
- HD: `cking.sav` must be exactly 8966 bytes. Failures are in a `rejected/` folder.
- GC: `.gci` must start with `GZL` at offset 0. All kept `.gci` files pass (all are 98368 bytes).

Totals: **46 distinct HD `cking.sav`** (48 files, 2 byte-identical duplicates) and
**83 GC `.gci`** (82 distinct; 19 GZLE01, 60 GZLJ01, 4 GZLP01) in the new source folders.

Side finding: an existing GC -> HD converter already exists in
https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp (`tools/savegame/gc2hd.py`, `hd2gc.py`,
`hd_save_info.py`, `wwsave.py` with the documented layouts). Not copied here and not run.

---

## HD (Wii U) saves: `hd/`

### hd/gbatemp-compilation — 7 saves (7 distinct)

- Source: first post of the GBAtemp thread "Wii U - Save Files Compilation",
  https://gbatemp.net/threads/wii-u-save-files-compilation.427761/ (GBAtemp itself is behind a
  Cloudflare check; the post was read through the Wayback Machine capture
  `web.archive.org/web/20260729190007/...`). The files are hosted on Google Drive and downloaded
  directly without login.
- Console vs Cemu: not stated per file. The folder layouts (`u/`+`c/`, `80000001/`+`common/`) look like
  console dumps made with Saviine/SaveMii, but that is my inference.
- Layout: `archives/NN_<name>` (original archive), `extracted/NN_<name>/` (contents).

| # | Original file name | Region (from name) | Uploader's description | Drive link |
|---|---|---|---|---|
| 01 | TLOZ Wind Waker HD [BCZE01].7z | USA | "not a fantastic save ... I haven't done much side-questing. Best thing I can say I have is the Swift Sail" | https://drive.google.com/open?id=0B5p7e1g-NHIva0pFOHVfQ2s3c3M |
| 02 | Zelda Windwaker HD [BCZE01].zip | USA | Everything in the zeldadungeon.net walkthrough up to chapter 8.1 (Nayru's Pearl) | https://drive.google.com/open?id=0B5p7e1g-NHIvYmV3YXBkc2hlalk |
| 03 | Zelda Windwaker HD [BCZE01](1).zip | USA | Starts at the entrance of the Tower of the Gods; walkthrough complete up to 9.1 incl. sidequests; 13 hearts, 5000 rupee wallet, Swift Sail, whole sea charted, 99 bombs, 3 bottles | https://drive.google.com/open?id=0B5p7e1g-NHIvbWJaaWNnSE80ZUk |
| 04 | Zelda Wind Waker [BCZP01].zip | EUR | "one playthrough, start hero mode in save slot 1" | https://drive.google.com/open?id=0B5p7e1g-NHIvaU5ycmxRYVZoYkE |
| 05 | cking.zip | not stated | Quest Log 1 "Link" at Ganon's Tower; Quest Log 2 ready to start in Hero Mode; Quest Log 3 free | https://drive.google.com/open?id=0B5p7e1g-NHIva0NxZkwyRjRrb28 |
| 06 | The Legend Of Zelda - Wind Waker HD [BCZE01].zip | USA | Three saves: Second Quest just started (about Windfall), "my sister's save", Normal Quest 100% (kevstar91) | https://drive.google.com/open?id=0B5p7e1g-NHIvdzliS3JnQVdIeEk |
| 07 | ckingv2.zip | not stated (continuation of 06, so USA) | Continuation of kevstar91's save: normal and second quest both at 100%, name Link (FredericVincent0, Sep 2024) | https://drive.google.com/file/d/1Y_6JQPc_8aMXY5SvIc5jpyH3ivQO6fC0/view |

All seven `cking.sav` are 8966 bytes. Pages 2-66 of the thread were also scanned (Wayback
copies); they contain no further Wind Waker HD download links, only requests and re-posts of
the links above.

### hd/github-chriztr_wiiu-game-saves-for-cemu — 4 saves (3 new)

- Source: https://github.com/chriztr/wiiu-game-saves-for-cemu, folder `GameSaves/ZeldaWWHD`
  (commit in `COMMIT.txt`).
- Uploader says: saves exported with Cemu's Title Manager "at certain points in the game as I
  progress"; no per-save description and no region stated.
- Files: `zelda_wwhd_chp1.zip`, `chp2`, `chp3` (chriztr, Cemu; names suggest consecutive chapters, progress not described) and
  `kevstar91/zeldawwhd_100percent.zip` (its `cking.sav` is byte-identical to gbatemp #06).
- All four `cking.sav` are 8966 bytes; each has `cking_playlog.sav`.

### hd/savegameworld — 2 saves

- Source: https://www.savegameworld.com/pc-the-legend-of-zelda-the-wind-waker-hd-savegame/
  (file https://www.savegameworld.com/download/Wind_Waker_HD_Save.zip), author "ILive", March 2025.
- Uploader says: played on Cemu 2.6; whole game completed, whole map opened, all treasure
  collected, all Tingle statues, 19 hearts, Nintendo Gallery not fully finished. Two folders:
  "Tower of Ganon" (before the final trials and Ganon) and "Completed game" (slot 2 left for
  Second Quest).
- Region: EUR (`meta.xml` in the archive says title ID 0005000010143600, product code WUP-P-BCZP).
- Both `cking.sav` are 8966 bytes.

### hd/github-issue-attachments — 35 saves (34 distinct)

- Source: files attached to bug reports of the Wind Waker HD PC/Switch/Android ports:
  ZeldaWWHDRecomp/ZeldaWWHDRecomp, centollOS/SwitchWakerHD, GreenNaugahyde/ZeldaWWHDRecompAndroid,
  Nycolazs/WindWakerHD-Android-Plus. Collected through the public GitHub API (issue bodies and
  comments) and downloaded from `github.com/user-attachments/files/...` without login.
- Caveat: these were written by the recompiled ports, not by a console or Cemu. They use the same
  8966-byte `cking.sav`. Region and progress are not stated by the reporters; the issue title
  is the only hint of where in the game the save is (table below). Some may originate from
  imported Cemu/console saves or from the ports' own GC -> HD converter; this is not recorded.
- Layout: one folder per attachment, `<repo>_issue<N>_<attachment id>/` with the original
  archive and `extracted/`. `attachments.tsv` is the raw list (folder, file, URL, issue, title).
  Three attachments are raw `cking.sav.txt` (the `.txt` suffix was added by the uploader for
  GitHub; they are binary, 8966 bytes).
- `wwstate-only/`: 19 attachments that contain only `.wwstate` portable save states of the
  ports (no `cking.sav`). Kept because the ZeldaWWHDRecomp docs say a state embeds the save
  data, but they are not `cking.sav` samples.
- `rejected/ZeldaWWHDRecomp_issue529_34719414/`: `cking.sav` is 12054 bytes, not 8966 (issue
  "Stuck at Tower of Gods"). Kept for inspection.
- Two `.zip` attachments were actually RAR5 archives (issue 312 `user.zip`, SwitchWakerHD issue
  141 `State.zip`); extracted with bsdtar.
- Duplicates: SwitchWakerHD issue 52 has the same `cking.sav.txt` attached twice.

| Folder | Issue | Issue title | Attachment | Result |
|---|---|---|---|---|
| `ZeldaWWHDRecompAndroid_issue4_33079052` | [GreenNaugahyde/ZeldaWWHDRecompAndroid/issues/4](https://github.com/GreenNaugahyde/ZeldaWWHDRecompAndroid/issues/4) | lossless.dll 60fps causes jelly-like effect | [dcd0f8c6a236af6e009ec7774d537ecc.zip](https://github.com/user-attachments/files/33079052/dcd0f8c6a236af6e009ec7774d537ecc.zip) | not kept (not a save: video/fonts) |
| `ZeldaWWHDRecompAndroid_issue23_33271660` | [GreenNaugahyde/ZeldaWWHDRecompAndroid/issues/23](https://github.com/GreenNaugahyde/ZeldaWWHDRecompAndroid/issues/23#issuecomment-6091907432) | (comment) | [user.zip](https://github.com/user-attachments/files/33271660/user.zip) | cking.sav 8966 bytes OK md5 95a04d52 |
| `WindWakerHD-Android-Plus_issue24_33793975` | [Nycolazs/WindWakerHD-Android-Plus/issues/24](https://github.com/Nycolazs/WindWakerHD-Android-Plus/issues/24#issuecomment-6329548421) | (comment) | [WindWakerHD.Saves.zip](https://github.com/user-attachments/files/33793975/WindWakerHD.Saves.zip) | cking.sav 8966 bytes OK md5 6d0403d5 |
| `wwstate-only/ZeldaWWHDRecomp_issue571_34834879` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/571](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/571) | Font glitches when navigating in-game port settings menu | [slot2.zip](https://github.com/user-attachments/files/34834879/slot2.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue571_34834882` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/571](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/571) | Font glitches when navigating in-game port settings menu | [save.zip](https://github.com/user-attachments/files/34834882/save.zip) | cking.sav 8966 bytes OK md5 1a5ad753; 1 .wwstate |
| `rejected/ZeldaWWHDRecomp_issue529_34719414` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/529](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/529) | Stuck at Tower of Gods | [Zelda.zip](https://github.com/user-attachments/files/34719414/Zelda.zip) | cking.sav 12054 bytes REJECTED md5 24499f3d; 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue493_34589784` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/493](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/493) | Performance drops when opening gamepad in one-screen mode | [slot2.zip](https://github.com/user-attachments/files/34589784/slot2.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue469_34530589` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/469](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/469) | Boat sail flickering at 60 fps | [save.zip](https://github.com/user-attachments/files/34530589/save.zip) | cking.sav 8966 bytes OK md5 2501615d; 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue446_34489357` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/446](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/446) | Boat sail flickers if you select a framerate above 60 | [slot1.zip](https://github.com/user-attachments/files/34489357/slot1.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue446_34489377` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/446](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/446) | Boat sail flickers if you select a framerate above 60 | [cking.zip](https://github.com/user-attachments/files/34489377/cking.zip) | cking.sav 8966 bytes OK md5 44b54b48 |
| `wwstate-only/ZeldaWWHDRecomp_issue361_34292581` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/361](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/361) | Loading save state when crawling causes respawn loop | [slot1.zip](https://github.com/user-attachments/files/34292581/slot1.zip) | 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue353_34276523` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/353](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/353) | Rupee sparkle effect stays on-screen when rupee display is off | [slot1.zip](https://github.com/user-attachments/files/34276523/slot1.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue334_34190104` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/334](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/334) | Android Performance Regression after v0.5.0 | [saves.zip](https://github.com/user-attachments/files/34190104/saves.zip) | cking.sav 8966 bytes OK md5 afeaac26; 1 .wwstate |
| `ZeldaWWHDRecomp_issue322_34016118` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/322](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/322) | Save dates are the current system date, not actual save date | [cking.zip](https://github.com/user-attachments/files/34016118/cking.zip) | cking.sav 8966 bytes OK md5 44a00e12 |
| `ZeldaWWHDRecomp_issue309_33939896` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/309](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/309) | Selecting My Dedicated Nvidia GPU Crashes My Game On CachyOS | [save.+.state.zip](https://github.com/user-attachments/files/33939896/save.%2B.state.zip) | cking.sav 8966 bytes OK md5 48307a21; 1 .wwstate |
| `ZeldaWWHDRecomp_issue307_33933279` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/307](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/307) | Bloom visual bug at higher resolutions | [state.zip](https://github.com/user-attachments/files/33933279/state.zip) | cking.sav 8966 bytes OK md5 18b53935; 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue299_33901570` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/299](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/299) | Camera is choppy in Boating Course minigame with frame interpolation | [boatingcourse_slot1.zip](https://github.com/user-attachments/files/33901570/boatingcourse_slot1.zip) | 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue297_33894147` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/297](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/297) | Mipmap issue on light underneath Triforce Shard/Chart chests | [slot5.zip](https://github.com/user-attachments/files/33894147/slot5.zip) | 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue283_33830392` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/283](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/283) | Interpolation causes Link to stay invisible after scenes that make him invisible temporarily | [slot1.zip](https://github.com/user-attachments/files/33830392/slot1.zip) | 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue275_33813450` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/275](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/275) | UI Effects (Arrow Element, Rupee Sparkle) are offset on non-16:9 aspect ratios | [slot3.zip](https://github.com/user-attachments/files/33813450/slot3.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue254_33680064` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/254](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/254) | Performance degredation on Android on de56d1d | [evosave.zip](https://github.com/user-attachments/files/33680064/evosave.zip) | cking.sav 8966 bytes OK md5 3a5eed84; 1 .wwstate |
| `ZeldaWWHDRecomp_issue251_33642303` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/251](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/251) | Missing interpolation for cutting trees and when trasitioning to first person view/telescope view | [Wind.Waker.Saves.zip](https://github.com/user-attachments/files/33642303/Wind.Waker.Saves.zip) | cking.sav 8966 bytes OK md5 f6cc1c64; 1 .wwstate |
| `ZeldaWWHDRecomp_issue237_33583087` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/237](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/237) | Mouse camera stuttering when sailing | [slot1.zip](https://github.com/user-attachments/files/33583087/slot1.zip) | cking.sav 8966 bytes OK md5 c277af26; 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue229_33552585` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/229](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/229) | (WIN) Gyro not working with Switch Pro Controller & camera drift | [slot1.zip](https://github.com/user-attachments/files/33552585/slot1.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue223_33515517` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/223](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/223) | Game crashes when talking to Orca | [state.zip](https://github.com/user-attachments/files/33515517/state.zip) | cking.sav 8966 bytes OK md5 3a8a32ed; 1 .wwstate |
| `ZeldaWWHDRecomp_issue179_33410800` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/179](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/179) | Sploosh Kaboom Mini Game Visual Bug | [WWHDSaves.zip](https://github.com/user-attachments/files/33410800/WWHDSaves.zip) | cking.sav 8966 bytes OK md5 c7bfc740; 1 .wwstate |
| `ZeldaWWHDRecomp_issue178_33361454` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/178](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/178) | Performance issues on Steam Deck | [saves.zip](https://github.com/user-attachments/files/33361454/saves.zip) | cking.sav 8966 bytes OK md5 4a471d33; 1 .wwstate |
| `ZeldaWWHDRecomp_issue167_33346280` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/167](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/167) | Inverting the camera also inverts the Wind Waker Baton direction | [save.zip](https://github.com/user-attachments/files/33346280/save.zip) | cking.sav 8966 bytes OK md5 97ed5b1e; 1 .wwstate |
| `ZeldaWWHDRecomp_issue160_33323831` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/160](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/160) | NPC talking bug | [states.zip](https://github.com/user-attachments/files/33323831/states.zip) | cking.sav 8966 bytes OK md5 5d6f1674; 1 .wwstate |
| `ZeldaWWHDRecomp_issue145_33303346` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/145](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/145) | Crash In Forbidden Woods with Quick Door | [state.zip](https://github.com/user-attachments/files/33303346/state.zip) | cking.sav 8966 bytes OK md5 f45b76d4; 1 .wwstate |
| `ZeldaWWHDRecomp_issue119_33274308` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/119](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/119) | Mail textures appear black in the Mail Sorting minigame (US version) | [bug-mailsorting.zip](https://github.com/user-attachments/files/33274308/bug-mailsorting.zip) | cking.sav 8966 bytes OK md5 ac60a31d; 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue85_33222357` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/85](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/85) | Medli not appearing inside room in Dragon Roost Island after speaking to Chieftain? | [slot2.state.zip](https://github.com/user-attachments/files/33222357/slot2.state.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue85_33222358` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/85](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/85) | Medli not appearing inside room in Dragon Roost Island after speaking to Chieftain? | [cking.sav.zip](https://github.com/user-attachments/files/33222358/cking.sav.zip) | cking.sav 8966 bytes OK md5 d33f68cc |
| `ZeldaWWHDRecomp_issue79_33215368` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/79](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/79) | [0.2.8] After saving the game gets stuck. | [cking.zip](https://github.com/user-attachments/files/33215368/cking.zip) | cking.sav 8966 bytes OK md5 2627250c |
| `ZeldaWWHDRecomp_issue76_33205565` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/76](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/76) | Ultrawide resolutions: Misaligned menu selection boxes | [states.zip](https://github.com/user-attachments/files/33205565/states.zip) | cking.sav 8966 bytes OK md5 8a77c884; 1 .wwstate |
| `ZeldaWWHDRecomp_pull39_33132841` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/pull/39](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/pull/39#issuecomment-6028434549) | (comment) | [cking.sav.zip](https://github.com/user-attachments/files/33132841/cking.sav.zip) | cking.sav 8966 bytes OK md5 0c0ecc71 |
| `ZeldaWWHDRecomp_issue68_33258077` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/68](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/68#issuecomment-6084211634) | (comment) | [save.zip](https://github.com/user-attachments/files/33258077/save.zip) | cking.sav 8966 bytes OK md5 17607301 |
| `ZeldaWWHDRecomp_issue90_33265997` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/90](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/90#issuecomment-6088683332) | (comment) | [user.zip](https://github.com/user-attachments/files/33265997/user.zip) | cking.sav 8966 bytes OK md5 752500bd |
| `wwstate-only/ZeldaWWHDRecomp_issue255_33762781` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/255](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/255#issuecomment-6313314445) | (comment) | [slot1.zip](https://github.com/user-attachments/files/33762781/slot1.zip) | 1 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue273_33826092` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/273](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/273#issuecomment-6343736015) | (comment) | [slot1.zip](https://github.com/user-attachments/files/33826092/slot1.zip) | 1 .wwstate |
| `ZeldaWWHDRecomp_issue278_33885712` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/278](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/278#issuecomment-6372079575) | (comment) | [rocknroll-one.zip](https://github.com/user-attachments/files/33885712/rocknroll-one.zip) | not kept (not a save: video/fonts) |
| `ZeldaWWHDRecomp_issue312_34189274` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/312](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/312#issuecomment-6526794523) | (comment) | [user.zip](https://github.com/user-attachments/files/34189274/user.zip) | cking.sav 8966 bytes OK md5 279d5358 |
| `wwstate-only/ZeldaWWHDRecomp_issue405_34493263` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/405](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/405#issuecomment-6691681156) | (comment) | [states.zip](https://github.com/user-attachments/files/34493263/states.zip) | 2 .wwstate |
| `wwstate-only/ZeldaWWHDRecomp_issue405_34503108` | [ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/405](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp/issues/405#issuecomment-6697590201) | (comment) | [slot2.zip](https://github.com/user-attachments/files/34503108/slot2.zip) | 1 .wwstate |
| `SwitchWakerHD_issue151_34682722` | [centollOS/SwitchWakerHD/issues/151](https://github.com/centollOS/SwitchWakerHD/issues/151) | Crash in cinematic | [Save.and.state.zip](https://github.com/user-attachments/files/34682722/Save.and.state.zip) | cking.sav 8966 bytes OK md5 40f25e0d; 1 .wwstate |
| `wwstate-only/SwitchWakerHD_issue150_34654035` | [centollOS/SwitchWakerHD/issues/150](https://github.com/centollOS/SwitchWakerHD/issues/150) | Jump Anywhere option doesn't work | [Savestate.tar.gz](https://github.com/user-attachments/files/34654035/Savestate.tar.gz) | 1 .wwstate |
| `SwitchWakerHD_issue141_34550678` | [centollOS/SwitchWakerHD/issues/141](https://github.com/centollOS/SwitchWakerHD/issues/141) | Moon jump does not work on v1.2.2, the newest update | [State.zip](https://github.com/user-attachments/files/34550678/State.zip) | cking.sav 8966 bytes OK md5 cbd59735; 1 .wwstate |
| `SwitchWakerHD_issue126_34516588` | [centollOS/SwitchWakerHD/issues/126](https://github.com/centollOS/SwitchWakerHD/issues/126) | Puppet Ganon Crash | [Puppet.Ganon.Crash.zip](https://github.com/user-attachments/files/34516588/Puppet.Ganon.Crash.zip) | cking.sav 8966 bytes OK md5 c0f3f3c8 |
| `wwstate-only/SwitchWakerHD_issue52_33731178` | [centollOS/SwitchWakerHD/issues/52](https://github.com/centollOS/SwitchWakerHD/issues/52) | dragon roost cave CRASH | [slot1.wwstate.txt](https://github.com/user-attachments/files/33731178/slot1.wwstate.txt) | 1 .wwstate |
| `SwitchWakerHD_issue52_33731181` | [centollOS/SwitchWakerHD/issues/52](https://github.com/centollOS/SwitchWakerHD/issues/52) | dragon roost cave CRASH | [cking.sav.txt](https://github.com/user-attachments/files/33731181/cking.sav.txt) | cking.sav.txt 8966 bytes OK md5 e8eb447b |
| `wwstate-only/SwitchWakerHD_issue52_33731152` | [centollOS/SwitchWakerHD/issues/52](https://github.com/centollOS/SwitchWakerHD/issues/52) | dragon roost cave CRASH | [slot1.wwstate.txt](https://github.com/user-attachments/files/33731152/slot1.wwstate.txt) | 1 .wwstate |
| `SwitchWakerHD_issue52_33731154` | [centollOS/SwitchWakerHD/issues/52](https://github.com/centollOS/SwitchWakerHD/issues/52) | dragon roost cave CRASH | [cking.sav.txt](https://github.com/user-attachments/files/33731154/cking.sav.txt) | cking.sav.txt 8966 bytes OK md5 e8eb447b |
| `SwitchWakerHD_issue46_33631753` | [centollOS/SwitchWakerHD/issues/46](https://github.com/centollOS/SwitchWakerHD/issues/46) | Game crash on Shark Island | [cking.sav.txt](https://github.com/user-attachments/files/33631753/cking.sav.txt) | cking.sav.txt 8966 bytes OK md5 c05532e7 |
| `wwstate-only/SwitchWakerHD_issue46_33631752` | [centollOS/SwitchWakerHD/issues/46](https://github.com/centollOS/SwitchWakerHD/issues/46) | Game crash on Shark Island | [slot1.wwstate.txt](https://github.com/user-attachments/files/33631752/slot1.wwstate.txt) | 1 .wwstate |
| `SwitchWakerHD_issue42_33470586` | [centollOS/SwitchWakerHD/issues/42](https://github.com/centollOS/SwitchWakerHD/issues/42) | Crash | [save.zip](https://github.com/user-attachments/files/33470586/save.zip) | cking.sav 8966 bytes OK md5 bc7b1eec; 1 .wwstate |
| `SwitchWakerHD_issue32_33360541` | [centollOS/SwitchWakerHD/issues/32](https://github.com/centollOS/SwitchWakerHD/issues/32) | Green blur on the right edge of the screen during the Helmaroc King tower flooding cutscene (Forsaken Fortress) with bloom/effects on | [Slot.1.Pre-Helmaroc.Forsaken.Fortress.2.-.State.inside.the.flooding.tower.zip](https://github.com/user-attachments/files/33360541/Slot.1.Pre-Helmaroc.Forsaken.Fortress.2.-.State.inside.the.flooding.tower.zip) | cking.sav 8966 bytes OK md5 bb3b676b; 1 .wwstate |
| `SwitchWakerHD_issue12_33297201` | [centollOS/SwitchWakerHD/issues/12](https://github.com/centollOS/SwitchWakerHD/issues/12) | Island text issue | [save.zip](https://github.com/user-attachments/files/33297201/save.zip) | cking.sav 8966 bytes OK md5 bf343ed7 |

### HD sources that could not be downloaded

| Source | URL | Why | Notes |
|---|---|---|---|
| GBAtemp thread attachment (post on page 6) | https://gbatemp.net/attachments/the-legend-of-zelda-wind-waker-hd-bcze01-zip.52250/ | Cloudflare check + GBAtemp login for attachments | Probably the same file as one of the Drive links (USA) |
| GBAtemp thread attachment (post 10505510, page 64) | https://gbatemp.net/attachments/cking-zip.461562/ | same | 21.4 KB `cking.zip`; same description as Drive #07 (ckingv2.zip) |
| GBAtemp download centre "The Legends Of Zelda Wind Waker HD Save 100 %" (kevstar91) | https://gbatemp.net/download/the-legends-of-zelda-wind-waker-hd-save-100.36994/ | Cloudflare check + login to download | Three slots incl. Normal Quest 100%; very likely the same as gbatemp #06 |
| r/cemu save request thread | https://www.reddit.com/r/cemu/comments/1kvda6y/ | Reddit returns 403 to scripts | A request (Windfall Island save); unknown whether anyone posted a file |
| Wind Waker speedrunning Discord (practice-ROM channel, HD practice files) | linked from https://github.com/CGF95/tww-gz and https://github.com/TotSpeedRuns/TWWHD-GZ | Discord login | TWWHD-GZ itself ships no `cking.sav`, only route checkpoint JSON |
| archive.org item "wii u" (9.4 GB) | https://archive.org/details/wiiu_20260722 | Not inspected: size suggests game data, which is out of scope | |

Checked and found to contain no Wind Waker HD saves: archive.org `wii-u-100-saves-verified`;
GitHub repos NelsWebDev/wwhd-save-editor, JakeButf/twwhd-save-editor, deep40k/windwakerhd-saveeditor,
vishnu350/windwaker-hd-editor, TotSpeedRuns/TWWHD-GZ, SuperDude88/TWWHD-Randomizer,
ZeldaWWHDRecomp/ZeldaWWHDRecomp (repository tree), asadsi/wwhd-recomp-mods;
zeldaspeedruns.com/twwhd (no resources page). The archive.org "Zelda Saves Compilation
2019-09-01" has one WWHD zip that is byte-identical to gbatemp #06.

---

## GameCube saves: `gc/`

All `.gci` below are 98368 bytes and start with the game code shown.

| Folder | Source URL | Files | Region | What the uploader says |
|---|---|---|---|---|
| `cryze` | https://github.com/CryZe/WindWakerSaves (commit e8b4aa6) | 167 | mostly GZLJ01, some GZLE01 | Speedrun practice saves by category (100%, Any%, Casual, ...) |
| `pack1` | https://retromaggedon.com/index.php/the-legend-of-zelda-the-wind-waker-ngc-save-files/ (`WindWakerSaves.7z`) | 10 | GZLE01 | "These saves have been tested on dolphin and Retroarch"; one save per point of the game, described in `Note saves.txt` |
| `github-cbartondock_windwaker` | https://github.com/cbartondock/Windwaker (`Save States/USA_Saves`) | 7 | GZLE01 | Mid-game USA saves made in Dolphin "as I go": 1_outset, 2_pirateship, 3_forsaken, 4_windfall, 5_dragonroost, 6_foresthaven, 7_windfall |
| `github-pdale-boop_ww-save-editor` | https://github.com/pdale-boop/ww-save-editor (`presets/`) | 7 | GZLE01 | "Reference saves from my own playthrough" (BlueWake PC port), named in `presets.json`: wake up, need a sail, Dragon Roost Cavern entrance, Forbidden Woods entrance, one orb left (Tower of the Gods), got the Master Sword, boots and bracelets before Earth Temple |
| `gc-saves.com` | https://gc-saves.com/game/90 | 3 | GZLE01, GZLJ01, GZLP01 | USA: 100% complete, second costume and all figurines. JP: second playthrough, ready for the final battle. PAL: slot 1 100% second quest, slot 3 end of first quest. Descriptions match the GameFAQs entries by CAHowell, Abelian and TheRealJDAdams |
| `archive-org-zeldasaves` | https://archive.org/details/zeldasaves ("Zelda Saves Compilation 2019-09-01", `Zelda SAVES.rar`, only the three Wind Waker files extracted) | 3 | GZLE01, GZLJ01, GZLP01 | "Saves compilation of the Zelda saga ... for hardware and emulation. All regions"; no per-file description. The PAL file is byte-identical to the gc-saves.com PAL file |
| `archive-org-memcard-251-us` | https://archive.org/details/20250206-dol-memcard-bak | 1 raw card image (2 MB) + 1 extracted `.gci` | GZLE01 | Raw dump of a second-hand US Memory Card 251, "all data present has been left untouched", saves from 2002 on: a real console save of unknown progress. `extracted-gci/01-GZLE-gczelda.gci` was cut out of the image by me following the card's directory and block table |
| `github-zephiles_twwsavefilehacker` | https://github.com/Zephiles/TWWSaveFileHacker (`TestSaves/saves`) | 6 | 2 each GZLE01/GZLJ01/GZLP01 | Test saves of a save-exploit tool: `Vanilla/` (unmodified) and `Hacked_File_3/` (file 3 modified to load a REL; not a normal save) |
| `github-minimini352_tww-100-saves` | https://github.com/minimini352/TWW-100-Saves | 16 | GZLJ01 | Speedrun practice saves, Early Earth Temple 100% route; each save has 2 practice files (files 2 and 3) |
| `github-minimini352_tww-any-saves` | https://github.com/minimini352/TWW-Any-Saves | 8 | GZLJ01 | Practice saves for Any% |
| `github-minimini352_tww-any-no-mss-saves` | https://github.com/minimini352/TWW-Any-No-MSS-Saves | 6 | GZLJ01 | Practice saves for Any% No MSS |
| `github-minimini352_tww-glitchless-saves` | https://github.com/minimini352/TWW-Glitchless-Saves | 13 | GZLJ01 | Practice saves for Bug Limit (glitchless) |
| `github-minimini352_tww-il-saves` | https://github.com/minimini352/TWW-IL-Saves | 7 | GZLJ01 | Individual-level saves, one per dungeon (DRC, FW, TotG, ET, WT, Savage, Trials); files 1-2 Any%, file 3 100% |
| `github-samrg97_tww-gz_save_tools` | https://github.com/samrg97/tww-gz_save_tools (`categories/any_no_mss/saves/gci`) | 6 | GZLJ01 | Any% No MSS practice saves used to build tww-gz practice files |
| `github-cgf95_tww-gz/rejected` | https://github.com/CGF95/tww-gz (`res/save_files`) | 343 `.bin` | n/a | Practice-ROM save files: raw save blocks (mostly 1904 bytes), not `.gci`, so they fail the `GZL` header check. Kept in `rejected/` as possible extra material |

Git sources have the commit hash in `COMMIT.txt`. Speedrun practice saves are made with glitches
and may hold flag combinations that normal play cannot produce.

### GC sources that could not be downloaded

| Source | URL | Why | Notes |
|---|---|---|---|
| GameFAQs save page | https://gamefaqs.gamespot.com/gamecube/469050-the-legend-of-zelda-the-wind-waker/saves | Cloudflare 403 for scripts (page and files) | Listing (from a 2010 Wayback copy): USA `zelda_the_wind_waker.gcs` (Dhaos10, "Got Everything"), `zelda_wind_waker_second.gci` (Xyton, all three files ready for second quest), `zelda_wind_waker.gci` (goldmario, all Triforce pieces, Ganon's Tower not complete), `zelda_wind_waker_a.gci` (Biospark3, everything completed), `zelda_wind_waker_b.gci` (CAHowell, complete + second costume + all figures); JP `zelda_wind_waker_jp.gci`; EU `zelda_the_wind_waker_eu.sav` (MaxDrive), `zelda_the_wind_waker_eu.gci`. File base URL was `db.gamefaqs.com/console/gamecube/save/`. The files are not in the Wayback Machine. The `.gcs` and `.sav` entries would be useful for the non-GCI container formats |
| Dolphin forum threads | https://forums.dolphin-emu.org/Thread-wind-waker-save-file-request , https://forums.dolphin-emu.org/Thread-wind-waker-savegame--29135 | Bot check on the live site | Wayback copies show requests only, no attachments |
| GBAtemp "Wind Waker Save Files" | https://gbatemp.net/threads/wind-waker-save-files.511325/ | Cloudflare check | Wayback copy only links to CryZe/WindWakerSaves and GameFAQs |
| zsrtww/tww-gz (upstream practice ROM) | https://github.com/zsrtww/tww-gz | Not cloned; the CGF95 fork was taken instead | Same kind of raw `.bin` practice files |

Checked, no Wind Waker saves: archive.org `saves_202408` (Nintendont raw cards), the EU/JP
cards of `0059b-2023-07-jul-03-14-55-24`, `gamecube-100-saves-verified`, several personal
Dolphin backup repos on GitHub, gc-forever thread t=1553 (a request).
