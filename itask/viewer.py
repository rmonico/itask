#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import collections
import re
import sys

from itask import console

viewer_width_default = 'terminal_columns'
viewer_height_default = 'terminal_lines'


class Region(object):

    def __init__(self, size, position={'left': 0, 'top': 0}, horizontal_constraints={'left': 0, 'right': 'width'},
                 vertical_constraints={'top': 0, 'bottom': 'height'}):
        """
            size: A dictionary with "width" and "height" entries.
            position: A dictionary with "left" and "top" entries.
            horizontal_constraints: A dictionary with "top" and "bottom" entries.
            vertical_constraints: A dictionary with "left" and "right" entries.
        """
        self._size = size
        self._position = position.copy()

        self._left_constraints = {'min': horizontal_constraints['left'], 'max': 0}
        if horizontal_constraints['right'] == 'width':
            self._left_constraints['max'] = self._size['width']
        else:
            self._left_constraints['max'] = horizontal_constraints['right']
        self._left_constraints['max'] -= size['width']

        self._top_constraints = {'min': vertical_constraints['top'], 'max': 0}
        if vertical_constraints['bottom'] == 'height':
            self._top_constraints['max'] = self._size['height']
        else:
            self._top_constraints['max'] = vertical_constraints['bottom']
        self._top_constraints['max'] -= self._size['height']

        self._listeners = {'horizontal move': [], 'vertical move': []}

    def register_listener(self, event, listener):
        self._listeners[event].append(listener)

    def remove_listener(self, event, listener):
        self._listeners[event].delete(listener)

    def _notify_listeners(self, event, *args, **kwargs):
        for listener in self._listeners[event]:
            listener(origin=self, *args, **kwargs)

    def _horizontal_move(self, cells):
        new_left = self._position['left'] + cells

        if new_left in range(self._left_constraints['min'], self._left_constraints['max'] + 1):
            old_left = self._position['left']

            self._position['left'] = new_left

            self._notify_listeners('horizontal move', old_left=old_left, new_left=new_left)

            return True

        return False

    def _vertical_move(self, cells):
        new_top = self._position['top'] + cells

        if new_top in range(self._top_constraints['min'], self._top_constraints['max'] + 1):
            old_top = self._position['top']

            self._position['top'] = new_top

            self._notify_listeners('vertical move', old_top=old_top, new_top=new_top)

            return True

        return False

    def move(self, direction, cells=1):
        if direction == 'set top':
            diff = cells - self._position['top']

            return self._vertical_move(diff)
        elif direction == 'set bottom':
            diff = cells - self._position['top'] - self._size['height'] + 1

            return self._vertical_move(diff)
        elif direction == 'left':
            return self._horizontal_move(-1)
        elif direction == 'right':
            return self._horizontal_move(1)
        elif direction == 'up':
            return self._vertical_move(-1)
        elif direction == 'down':
            return self._vertical_move(1)
        elif direction == 'top':
            cells_to_top = self._top_constraints['min'] - self._position['top']

            return self._vertical_move(cells_to_top)
        elif direction == 'bottom':
            cells_to_bottom = self._top_constraints['max'] - self._position['top']

            return self._vertical_move(cells_to_bottom)
        elif direction == 'begin':
            cells_to_begin = self._left_constraints['min'] - self._position['left']

            return self._horizontal_move(cells_to_begin)
        elif direction == 'end':
            cells_to_end = self._left_constraints['max'] - self._position['left']

            return self._horizontal_move(cells_to_end)

    @property
    def top(self):
        return self._position['top']

    @property
    def left(self):
        return self._position['left']

    @property
    def width(self):
        return self._size['width']

    @property
    def height(self):
        return self._size['height']

    @property
    def bottom(self):
        return self._position['top'] + self._size['height'] - 1


class Viewer(object):
    """
        For method move('top'/'bottom') work fine vertical_constraints must be set! (idem to move('begin'/'end'))
    """

    # Refatorar para colocar o screen_left e top em um dicionário
    def __init__(self, data_provider, region, selection=None, screen_left=0, screen_top=0):
        """
            region: Region on file being visualized by this Viewer
        """
        self.data_provider = data_provider

        self.region = region
        region.register_listener('vertical move', self.region_vertically_moved)
        region.register_listener('horizontal move', self.region_horizontally_moved)

        self._selection = selection

        if selection:
            selection.register_listener('changed', self.active_line_changed)

        self._screen_left = screen_left
        self._screen_top = screen_top
        self._dirty = True

    def invalidate(self):
        self._dirty = True

    def active_line_changed(self, origin, old_line, new_line):
        if new_line > self.region.bottom:
            self.region.move('set bottom', new_line)
        elif new_line < self.region.top:
            self.region.move('set top', new_line)

        self._dirty = True

    def region_vertically_moved(self, origin, old_top, new_top):
        if self._selection.active_line < origin.top:
            self._selection.active_line = origin.top
        elif self._selection.active_line > origin.bottom:
            self._selection.active_line = origin.bottom

        self._dirty = True

    def region_horizontally_moved(self, origin, old_left, new_left):
        self._dirty = True

    def update(self):
        if not self._dirty:
            return

        read_lines = -1
        printed_lines = 0

        b_left = bytes(str(self._screen_left + 1), sys.stdout.encoding)

        for raw_line in self.data_provider.lines:
            read_lines += 1

            if read_lines < self.region.top:
                continue

            line = raw_line[
                   self.region.left:self.region.left + self.region.width]

            if line != '' and line[-1] == '\n':
                line = line[:-1]

            b_top = bytes(str(self._screen_top + printed_lines + 1),
                          sys.stdout.encoding)

            line_itens = [b'\033[', b_top, b';', b_left, b'H']

            colored_line = False

            if self._selection:
                if self._selection.active_line == read_lines:
                    if read_lines in self._selection.selected_lines:
                        line_itens += [console.SEQUENCE_ESCAPES['cyan background']]
                    else:
                        line_itens += [console.SEQUENCE_ESCAPES['blue background']]
                    colored_line = True
                elif read_lines in self._selection.selected_lines:
                    line_itens += [console.SEQUENCE_ESCAPES['white background']]
                    colored_line = True

            line_itens += [bytes(line, sys.stdout.encoding)]

            if len(line) < self.region.width:
                line_itens += [b' ' * (self.region.width - len(line))]

            if colored_line:
                line_itens += [console.SEQUENCE_ESCAPES['color reset']]

            sys.stdout.buffer.write(b''.join(line_itens))

            printed_lines += 1

            if printed_lines == self.region.height:
                break

        self._dirty = False


_size_pattern = re.compile(
    '^([0-9]+|' + viewer_width_default + ')x([0-9]+|' + viewer_height_default +
    ')$')


def _size(value):
    matchs = _size_pattern.match(value)

    size = collections.namedtuple('Size', ['width', 'height'])

    # TODO Check for parsing errors

    size.width = str(matchs.group(1))

    if size.width != viewer_width_default:
        size.width = int(size.width)

    size.height = str(matchs.group(2))

    if size.height != viewer_height_default:
        size.height = int(size.height)

    return size


_position_pattern = re.compile('^([0-9]+)x([0-9]+)$')


def _position(value):
    matchs = _position_pattern.search(value)

    position = collections.namedtuple('Position', ['left', 'top'])

    # TODO Check for parsing errors

    position.left = int(matchs.group(1))
    position.top = int(matchs.group(2))

    return position


def parse_command_line():
    parser = argparse.ArgumentParser()

    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("-vs", "--viewer-size", type=_size,
                        default=viewer_width_default + 'x' +
                                viewer_height_default,
                        help="Viewer's size. Format: <width>x<height>. \"" +
                             viewer_width_default + "\" and \"" +
                             viewer_height_default + "\" can be used too.")
    parser.add_argument("-fp", "--file-position", type=_position, default='0x0',
                        help="Position of data to be clipped, 0 indexed. Format: <left>x<top>. Default: \"0x0\"")
    parser.add_argument("-sp", "--screen-position", type=_position, default='0x0',
                        help="Position of screen to paste data, 0 indexed. Format: <left>x<top>. Default: \"0x0\"")
    parser.add_argument("-f", "--file", type=argparse.FileType("rt"), default=sys.stdin,
                        help="File to be viewed. Defaults to stdin")

    args = parser.parse_args()

    if args.verbose:
        print('file: {}'.format(args.file))
        print('viewer_size.width: {}'.format(args.viewer_size.width))
        print('viewer_size.height: {}'.format(args.viewer_size.height))
        print('file_position.left: {}'.format(args.file_position.left))
        print('file_position.top: {}'.format(args.file_position.top))
        print('screen_position.left: {}'.format(args.screen_position.left))
        print('screen_position.top: {}'.format(args.screen_position.top))

    return args


def main():
    args = parse_command_line()

    viewer = Viewer(args.file, data_ruler(args.file), args.viewer_size.width, args.viewer_size.height,
                    args.file_position.left,
                    args.file_position.top, args.screen_position.left, args.screen_position.top)

    viewer.update()

    args.file.close()


if __name__ == '__main__':
    main()
