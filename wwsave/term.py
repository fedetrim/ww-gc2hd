"""Terminal output: styles (bold, colours) and line width. Styles are used only when the stream is a
terminal, NO_COLOR is not set and TERM is not 'dumb'; otherwise text is plain. In a terminal
text is wrapped to the window; redirected output keeps the form it had (only the report's change lines
are wrapped, at PLAIN_WIDTH)."""
import os
import shutil
import sys
import textwrap

CODES = {"bold": 1, "dim": 2, "italic": 3, "red": 31, "green": 32, "yellow": 33, "cyan": 36}
PLAIN_WIDTH = 100


_vt = {}


def _windows_console(stream, enable_vt=False):
    """On Windows: whether the stream is a console (isatty() is also true for NUL), and with `enable_vt`
    whether virtual terminal processing could be turned on for it: without it a console shows escape
    codes as text."""
    key = (stream.fileno(), enable_vt)
    if key not in _vt:
        try:
            import ctypes
            import msvcrt
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.GetConsoleMode.restype = wintypes.BOOL
            kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.SetConsoleMode.restype = wintypes.BOOL
            handle, mode = msvcrt.get_osfhandle(stream.fileno()), wintypes.DWORD()
            ok = bool(kernel.GetConsoleMode(handle, ctypes.byref(mode)))
            if ok and enable_vt:
                ok = bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))
            _vt[key] = ok
        except Exception:
            _vt[key] = False
    return _vt[key]


STDOUT = object()            # default argument: sys.stdout at the time of the call


def terminal(stream=STDOUT):
    stream = sys.stdout if stream is STDOUT else stream   # a closed standard stream is None: no terminal
    try:
        if stream is None or not hasattr(stream, "isatty") or not stream.isatty():
            return False
        return os.name != "nt" or _windows_console(stream)
    except (ValueError, OSError):                         # a stream that was closed, or has no descriptor
        return False


def styled(stream=STDOUT):
    return (terminal(stream) and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"
            and (os.name != "nt" or _windows_console(sys.stdout if stream is STDOUT else stream, enable_vt=True)))


def paint(text, *names, stream=STDOUT):
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
