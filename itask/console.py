#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

SEQUENCE_ESCAPES = {
    'blue background': b'\033[48;5;4m',
    'cyan background': b'\033[48;5;12m',
    'white background': b'\033[30;47m',
    'color reset': b'\033[0m'}


def move_cursor(x, y):
    sys.stdout.buffer.write('\033[{};{}H'.format(
        y, x).encode(sys.stdout.encoding))


def clear_screen():
    sys.stdout.buffer.write(b'\033[2J\033[1;1H')
    sys.stdout.flush()


def change_cursor_visibility(visible):
    if visible:
        sys.stdout.buffer.write(b'\033[?25h')
    else:
        sys.stdout.buffer.write(b'\033[?25l')


def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys
    import tty

    def _getch():
        fd = sys.stdin.fileno()
        old_settings = tty.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            tty.tcsetattr(fd, tty.TCSADRAIN, old_settings)

        return ch

    return _getch


getch = _find_getch()


def wait(message='Press any key to continue...'):
    print(message)
    getch()


def change_getch_echo(enabled):
    import os
    import platform

    if platform.system() == 'Linux':
        if enabled:
            os.system('stty echo')
        else:
            os.system('stty -echo')

    # TODO Implement on Windows...


def set_terminal_title(title):
    sys.stdout.buffer.write("\x1b]2;{}\x07".format(title).encode("utf-8"))
