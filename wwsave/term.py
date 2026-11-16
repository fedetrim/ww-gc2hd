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
    on for the standard output and error consoles, and report whether that worked."""
    global _vt
    if _vt is None:
        try:
            import ctypes
            kernel = ctypes.windll.kernel32
            _vt = True
            for handle in (-11, -12):               # STD_OUTPUT_HANDLE, STD_ERROR_HANDLE
                h, mode = kernel.GetStdHandle(handle), ctypes.c_uint32()
                if kernel.GetConsoleMode(h, ctypes.byref(mode)):        # fails for a redirected stream
                    if not kernel.SetConsoleMode(h, mode.value | 0x0004):
                        _vt = False
        except Exception:
            _vt = False
    return _vt


def terminal(stream=None):
    stream = stream or sys.stdout
    return bool(hasattr(stream, "isatty") and stream.isatty())


def styled(stream=None):
    return (terminal(stream) and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"
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
