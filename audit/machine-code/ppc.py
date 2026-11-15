#!/usr/bin/env python3
"""Minimal PowerPC constant tracker (module, not run by itself).

Follows li/lis/addi/addis/ori/andi./rlwinm/mr/extsb/extsh and lwz from a constant address through one
function and reports, at every `bl`, the possible constant values of r3..r8 (sets, merged at forward branch
joins; loop heads and jump tables are handled conservatively). A value that is not a constant is reported
as unknown, never guessed. Used by gc_extract.py and hd_extract.py (scan_function), gtitm.py and
audit/leftovers/i8_direct.py (per-instruction hook).

Inputs: none (the caller passes a read32 function).  Output: none.
"""
import struct

MAXSET = 12
VOLATILE = [0] + list(range(3, 13))


def sx16(v):
    return v - 0x10000 if v & 0x8000 else v


def rotl(v, n):
    v &= 0xFFFFFFFF
    return ((v << n) | (v >> (32 - n))) & 0xFFFFFFFF if n else v


def mask(mb, me):
    m = 0
    i = mb
    while True:
        m |= 1 << (31 - i)
        if i == me:
            break
        i = (i + 1) & 31
    return m


LOGICAL_XO = {28, 444, 316, 476, 124, 60, 284, 412, 24, 536, 792, 824, 26, 922, 954}
NODEST_XO = {0, 32, 151, 215, 407, 663, 727, 695, 759, 183, 247, 439, 662, 918, 150, 467, 144, 54, 86, 246, 278,
             1014, 598, 982, 470, 4, 661, 725, 983, 210, 242, 146, 178}


def dest_regs(ins):
    """registers written by ins (GPR numbers)"""
    op = ins >> 26
    rD = ins >> 21 & 31
    rA = ins >> 16 & 31
    if op in (7, 8, 12, 13, 14, 15):
        return [rD]
    if op in (20, 21, 23, 24, 25, 26, 27, 28, 29):
        return [rA]
    if op in (32, 34, 40, 42):
        return [rD]
    if op in (33, 35, 41, 43):
        return [rD, rA]
    if op in (37, 39, 45, 49, 51, 53, 55):
        return [rA]
    if op == 46:
        return list(range(rD, 32))
    if op == 31:
        xo = ins >> 1 & 0x3FF
        if xo in LOGICAL_XO:
            return [rA]
        if xo in NODEST_XO:
            return [rA] if xo in (183, 247, 439, 695, 759) else []
        if xo in (55, 119, 311, 375, 567, 631):   # load with update indexed
            return [rD, rA]
        return [rD]
    return []


def branch_target(ins, pc):
    op = ins >> 26
    if op == 18:
        li = ins & 0x03FFFFFC
        if li & 0x02000000:
            li -= 0x04000000
        return (li if ins & 2 else pc + li) & 0xFFFFFFFF
    if op == 16:
        bd = ins & 0xFFFC
        if bd & 0x8000:
            bd -= 0x10000
        return (bd if ins & 2 else pc + bd) & 0xFFFFFFFF
    return None


def plain(s):
    return all(t is None for t, x in s)


def merge(a, b):
    if a is None:
        return dict(b)
    out = {}
    for r in a:
        if r in b:
            s = a[r] | b[r]
            if len(s) <= MAXSET:
                out[r] = s
    return out


def scan_function(read32, start, end, on_call, init=None, on_ins=None):
    """read32(addr)->int. on_call(pc, target, regs) with regs: {reg: frozenset(values)}.
    init: optional initial register state."""
    code = [(pc, read32(pc)) for pc in range(start, end, 4)]
    # loop heads: backward branches -> registers written in [target, pc] are unknown at target
    loop_kill = {}
    for pc, ins in code:
        op = ins >> 26
        if op in (16, 18) and not ins & 1:
            t = branch_target(ins, pc)
            if t is not None and start <= t <= pc:
                ks = loop_kill.setdefault(t, set())
                for p2 in range(t, pc + 4, 4):
                    i2 = code[(p2 - start) // 4][1]
                    ks.update(dest_regs(i2))
                    if i2 >> 26 == 18 and i2 & 1 or i2 >> 26 == 16 and i2 & 1 or i2 >> 26 == 19 and i2 & 1:
                        ks.update(VOLATILE)
    incoming = {}
    state = dict(init or {})
    sw_state = None
    for pc, ins in code:
        if pc in incoming:
            state = merge(state, incoming.pop(pc)) if state is not None else incoming.pop(pc)
        if state is None:
            # not reached by forward flow: a jump-table case (use the state at the dispatch) or unknown
            state = dict(sw_state) if sw_state is not None else {}
        if pc in loop_kill:
            for r in loop_kill[pc]:
                state.pop(r, None)
        op = ins >> 26
        rD = ins >> 21 & 31
        rA = ins >> 16 & 31
        imm = ins & 0xFFFF
        if on_ins is not None:
            on_ins(pc, ins, state)
        if op == 14 or op == 15:
            v = sx16(imm) << (16 if op == 15 else 0)
            if rA == 0:
                state[rD] = frozenset([(None, v & 0xFFFFFFFF)])
            elif rA in state:
                state[rD] = frozenset((t, (x + v) & 0xFFFFFFFF) for t, x in state[rA])
            else:
                state.pop(rD, None)
        elif op == 24 or op == 25:
            v = imm << (16 if op == 25 else 0)
            if rD in state and plain(state[rD]):
                state[rA] = frozenset((None, x | v) for t, x in state[rD])
            else:
                state.pop(rA, None)
        elif op == 28:  # andi.
            if rD in state and plain(state[rD]):
                state[rA] = frozenset((None, x & imm) for t, x in state[rD])
            else:
                state.pop(rA, None)
        elif op == 21:
            sh, mb, me = ins >> 11 & 31, ins >> 6 & 31, ins >> 1 & 31
            if rD in state and plain(state[rD]):
                m = mask(mb, me)
                state[rA] = frozenset((None, rotl(x, sh) & m) for t, x in state[rD])
            elif rD in state and sh == 0 and mb >= 16 and me == 31 and all(isinstance(t, str) for t, x in state[rD]):
                state[rA] = state[rD]       # zero-extension of an incoming argument: keep it symbolic
            else:
                state.pop(rA, None)
        elif op == 31 and (ins >> 1 & 0x3FF) == 444 and rD == (ins >> 11 & 31):   # mr
            if rD in state:
                state[rA] = state[rD]
            else:
                state.pop(rA, None)
        elif op == 31 and (ins >> 1 & 0x3FF) in (922, 954):  # extsh/extsb
            if rD in state and all(isinstance(t, str) for t, x in state[rD]):
                state[rA] = state[rD]
            elif rD in state and plain(state[rD]):
                if (ins >> 1 & 0x3FF) == 922:
                    state[rA] = frozenset((None, sx16(x & 0xFFFF) & 0xFFFFFFFF) for t, x in state[rD])
                else:
                    state[rA] = frozenset((None, ((x & 0xFF) - 0x100 if x & 0x80 else x & 0xFF) & 0xFFFFFFFF) for t, x in state[rD])
            else:
                state.pop(rA, None)
        elif op in (32, 33):   # lwz/lwzu from a constant address -> symbolic "*(addr)"
            src = state.get(rA) if rA else None
            if src is not None and len(src) == 1 and plain(src):
                a = (next(iter(src))[1] + sx16(imm)) & 0xFFFFFFFF
                if op == 33:
                    state[rA] = frozenset([(None, a)])
                state[rD] = frozenset([(a, 0)])
            else:
                state.pop(rD, None)
                if op == 33:
                    state.pop(rA, None)
        elif op == 18:
            t = branch_target(ins, pc)
            if ins & 1:
                if on_call(pc, t, state) != "keep":
                    for r in VOLATILE:
                        state.pop(r, None)
            else:
                if start <= t < end and t > pc:
                    incoming[t] = merge(incoming.get(t), state)
                elif not (start <= t < end):
                    on_call(pc, t, state)      # tail call
                state = None
        elif op == 16:
            t = branch_target(ins, pc)
            if ins & 1:
                for r in VOLATILE:
                    state.pop(r, None)
            elif t is not None and start <= t < end and t > pc:
                incoming[t] = merge(incoming.get(t), state)
            if (ins >> 21 & 0x14) == 0x14 and not ins & 1:
                state = None
        elif op == 19:
            xo = ins >> 1 & 0x3FF
            if xo in (16, 528):
                if ins & 1:
                    on_call(pc, None, state)
                    for r in VOLATILE:
                        state.pop(r, None)
                elif (ins >> 21 & 0x14) == 0x14:
                    if xo == 528:
                        sw_state = {r: v for r, v in state.items() if r not in (0, 11, 12)}
                    state = None
        else:
            for r in dest_regs(ins):
                state.pop(r, None)
