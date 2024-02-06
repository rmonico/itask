#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itask import configs

import shutil
import sys

from itask import console
import signal


class MenuItem(object):

    def __init__(self, hotkey, title='', action=None, visible=True, interactive=True):
        self.hotkey = hotkey
        self.title = title
        self.action = action
        self.visible = visible
        self.interactive = interactive

    def run(self):
        if self.action:
            return self.action()


class QuitMenuItem(MenuItem):

    def __init__(self, hotkey=None, title='Quit', action=None):
        super(QuitMenuItem, self).__init__(title=title, hotkey=hotkey or configs.get('actions.quit'), action=action)

    def run(self):
        result = super(QuitMenuItem, self).run()

        return 'quit' if not result else result


class BackMenuItem(MenuItem):

    def __init__(self, hotkey='b', title='Back', action=lambda: 'back'):
        super(BackMenuItem, self).__init__(title=title, hotkey=hotkey, action=action)

    def run(self):
        result = super(BackMenuItem, self).run()

        return 'back' if not result else result


class Navigable(object):

    # Vertical
    def activate_next(self):
        pass

    def activate_previous(self):
        pass

    def viewer_down(self):
        pass

    def viewer_up(self):
        pass

    def activate_first(self):
        pass

    def activate_last(self):
        pass

    # Horizontal
    def viewer_left(self):
        pass

    def viewer_right(self):
        pass

    def viewer_begin(self):
        pass

    def viewer_end(self):
        pass

    # Selection
    def toggle_selected(self):
        pass


class Menu(object):

    def __init__(self, title='', redraw=True, back=True):
        self.title = title

        self.items = []

        if redraw:
            self.items += [MenuItem(title='Redraw', hotkey=configs.get('navigation.move.reload'))]

        if back:
            self.items += [MenuItem(title='Back', hotkey='b')]

        self._listeners = {'render': [], 'item chosen': [], 'after action': [], 'terminal resized': []}

        signal.signal(signal.SIGWINCH, self._terminal_resized)

    def register_listener(self, event, listener):
        self._listeners[event].append(listener)

    def remove_listener(self, event, listener):
        self._listeners[event].delete(listener)

    def _notify_listeners(self, event, *args, **kwargs):
        for listener in self._listeners[event]:
            listener(origin=self, *args, **kwargs)

    def append_quit(self, action):
        quit_item = QuitMenuItem(action=action)
        self.items.append(quit_item)

        return quit_item

    def append_navigation_keys(self, navigable):
        # Vertical
        self.items.append(MenuItem(configs.get('navigation.move.next'), action=navigable.activate_next, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.move.previous'), action=navigable.activate_previous, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.scroll.down'), action=navigable.viewer_down, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.scroll.up'), action=navigable.viewer_up, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.move.first'), action=navigable.activate_first, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.move.last'), action=navigable.activate_last, visible=False, interactive=False))

        # Horizontal
        self.items.append(MenuItem(configs.get('navigation.scroll.left'), action=navigable.viewer_left, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.scroll.right'), action=navigable.viewer_right, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.scroll.begin'), action=navigable.viewer_begin, visible=False, interactive=False))
        self.items.append(MenuItem(configs.get('navigation.scroll.end'), action=navigable.viewer_end, visible=False, interactive=False))

        # Selection
        self.items.append(MenuItem(configs.get('navigation.toggle_selected'), action=navigable.toggle_selected, visible=False, interactive=False))

    def _initialize(self):
        visible_items = []
        for item in self.items:
            if item.visible:
                visible_items.append('  ')
                visible_items.append(item.hotkey)
                visible_items.append(' ')
                visible_items.append(item.title)

        self._itens_string = ''.join(visible_items)[2:]

    def run(self):
        console.clear_screen()

        self._initialize()

        key = None
        result = None

        while result not in ('quit', 'back'):
            self._notify_listeners('render')

            self.render()

            key = console.getch()

            item_found = False
            for item in self.items:
                if item.hotkey == key:
                    self._notify_listeners('item chosen', item=item)
                    result = item.run()

                    item_found = True

                    break

            self._notify_listeners('after action', item=item if item_found else None)

    def render(self):
        terminal_size = shutil.get_terminal_size()

        console.move_cursor(1, terminal_size.lines - 1)
        title_string = '[{}]'.format(self.title)[:terminal_size.columns - 1]
        sys.stdout.write(title_string)

        sys.stdout.flush()

        console.move_cursor(1, terminal_size.lines)
        itens_string = '{}'.format(self._itens_string)[:terminal_size.columns - 1]
        sys.stdout.write(itens_string)

        sys.stdout.flush()

    def _terminal_resized(self, signal_number, stack):
        if hasattr(stack, '__len__'):
            stack[len(stack)].f_back()

        size = shutil.get_terminal_size()

        self._notify_listeners('terminal resized', columns=size.columns, lines=size.lines)
