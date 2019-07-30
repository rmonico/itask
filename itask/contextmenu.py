#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itask.imenu import Menu, MenuItem, Navigable, BackMenuItem
from itask import console


class ContextMenu(Navigable):

    def __init__(self, taskwarrior_wrapper):
        self._binary_wrapper = taskwarrior_wrapper

        self.menu = Menu(redraw=False, back=False)

        self.menu.items.append(
            MenuItem(title='Set', hotkey='s', action=self._set))
        self.menu.items.append(
            MenuItem(title='Cancel', hotkey='c', action=self._cancel))

        self.menu.append_navigation_keys(self)

    def run(self):
        self.menu.run()

    def _set(self):
        print('TODO (set)')

        console.wait()

    def _cancel(self):
        print('TODO (cancel)')

        console.wait()
