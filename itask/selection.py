#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Selection(object):

    def __init__(self, active_line, constraints={'top': None, 'bottom': None}):
        self.active_line = active_line
        self.selected_lines = []
        self._constraints = constraints.copy()
        self._listeners = {'changed': []}

    def register_listener(self, event, listener):
        self._listeners[event].append(listener)

    def remove_listener(self, event, listener):
        self._listeners[event].delete(listener)

    def _notify_listeners(self, event, *args, **kwargs):
        for listener in self._listeners[event]:
            listener(origin=self, *args, **kwargs)

    def _is_new_active_line_valid(self, new_line):
        if self._constraints['top'] and self._constraints['bottom']:
            return new_line in range(self._constraints['top'], self._constraints['bottom'])

        return True

    def move(self, action, cells=1):
        if action == 'down':
            new_line = self.active_line + cells
        elif action == 'up':
            new_line = self.active_line - cells

        if self._is_new_active_line_valid(new_line):
            old_line = self.active_line

            self.active_line = new_line

            self._notify_listeners('changed', old_line=old_line, new_line=new_line)

            return True

        return False

    def toggle_active_line_selected(self):
        if self.active_line not in self.selected_lines:
            self.selected_lines.append(self.active_line)
        else:
            self.selected_lines.remove(self.active_line)

        # FIXME Generate another event for this case
        self._notify_listeners('changed', old_line=-1, new_line=-1)

    def clear(self):
        self.selected_lines = []
