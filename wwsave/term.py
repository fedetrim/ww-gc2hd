"""Terminal output: styles (bold, colours) and line width. Styles are used only when the stream is a
terminal, NO_COLOR is not set and TERM is not 'dumb'; otherwise text is plain. Text is wrapped to
the window only in a terminal: redirected output keeps its one-line form."""
import os
import shutil
import sys
import textwrap

CODES = {"bold": 1, "dim": 2, "italic": 3, "red": 31, "green": 32, "yellow": 33, "cyan": 36}
PLAIN_WIDTH = 100


_vt = None


def _windows_vt():
    """On Windows a console shows escape codes as text unless virtual terminal processing is on: turn it
    on for the standard output and error consoles, and report whether that worked. Where neither stream
    is a console (a terminal emulator that passes a pipe), TERM says whether there is a terminal."""
    global _vt
    if _vt is None:
        try:
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetStdHandle.argtypes, kernel.GetStdHandle.restype = [wintypes.DWORD], wintypes.HANDLE
            kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.GetConsoleMode.restype = wintypes.BOOL
            kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.SetConsoleMode.restype = wintypes.BOOL
            consoles, ok = 0, True
            for handle in (-11, -12):               # STD_OUTPUT_HANDLE, STD_ERROR_HANDLE
                h, mode = kernel.GetStdHandle(wintypes.DWORD(handle & 0xFFFFFFFF)), wintypes.DWORD()
                if kernel.GetConsoleMode(h, ctypes.byref(mode)):        # fails for a stream that is no console
                    consoles += 1
                    ok = ok and bool(kernel.SetConsoleMode(h, mode.value | 0x0004))
            _vt = ok if consoles else bool(os.environ.get("TERM"))
        except Exception:
            _vt = False
    return _vt


def terminal(stream=None):
    stream = sys.stdout if stream is None else stream     # a closed standard stream is None
    return bool(stream is not None and hasattr(stream, "isatty") and stream.isatty())


def styled(stream=None):
    return (terminal(stream) and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"
            and (os.name != "nt" or _windows_vt()))


def paint(text, *names, stream=None):
    if not names or not styled(stream):
        return text
    return "\033[%sm%s\033[0m" % (";".join(str(CODES[n]) for n in names), text)


def width():
    """Line width for wrapped text: the terminal's, at most PLAIN_WIDTH; PLAIN_WIDTH when redirected."""
    if not terminal():
        return PLAIN_WIDTH
    return max(40, min(PLAIN_WIDTH, shutil.get_terminal_size().columns - 1))


def wrap(text, first="", rest="", wide=None):
    """`text` wrapped as lines, the first after `first`, the others after `rest` (both plain text)."""
    return textwrap.wrap(text, wide or width(), initial_indent=first, subsequent_indent=rest,
                         break_long_words=False, break_on_hyphens=False) or [first]


def labelled(indent, label, text, *names, rest=None):
    """`indent``label` `text`. In a terminal the text is wrapped to the window, continuing under `rest`
    (default: the indent and two spaces), and the label is painted; redirected, it is one plain line."""
    if not terminal():
        return "%s%s %s" % (indent, label, text)
    lines = wrap(text, indent + label + " ", indent + "  " if rest is None else rest)
    lines[0] = indent + paint(label, *names) + lines[0][len(indent) + len(label):]
    return "\n".join(lines)
