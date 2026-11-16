"""Terminal output: styles (bold, colours) and line width. Styles are used only when the stream is a
terminal, NO_COLOR is not set and TERM is not 'dumb'; otherwise every function returns plain text, so
redirected output is the same as it always was."""
import os
import shutil
import sys
import textwrap

CODES = {"bold": 1, "dim": 2, "italic": 3, "red": 31, "green": 32, "yellow": 33, "cyan": 36}
PLAIN_WIDTH = 100


def styled(stream=None):
    stream = stream or sys.stdout
    return (hasattr(stream, "isatty") and stream.isatty() and "NO_COLOR" not in os.environ
            and os.environ.get("TERM") != "dumb")


def paint(text, *names, stream=None):
    if not names or not styled(stream):
        return text
    return "\033[%sm%s\033[0m" % (";".join(str(CODES[n]) for n in names), text)


def width():
    """Line width for wrapped text: the terminal's, at most PLAIN_WIDTH; PLAIN_WIDTH when redirected."""
    if not sys.stdout.isatty():
        return PLAIN_WIDTH
    return max(40, min(PLAIN_WIDTH, shutil.get_terminal_size().columns - 1))


def wrap(text, first="", rest="", wide=None):
    """`text` wrapped as lines, the first after `first`, the others after `rest` (both plain text)."""
    return textwrap.wrap(text, wide or width(), initial_indent=first, subsequent_indent=rest,
                         break_long_words=False, break_on_hyphens=False) or [first]
