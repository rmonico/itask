#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil


class CalendarViewer(object):

    _days_in_week = 7
    _weekday_names = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
    _weekday_names_abrev = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']

    def __init__(self, weeknumber=4):
        self._weeknumber = weeknumber

    def _print_ruler(self):
        s = '+'

        for i in range(0, CalendarViewer._days_in_week):
            s += '-' * self._day_width
            s += '+'

        print(s)

    def _print_line(self, data):
        s = '|'

        for i in range(0, CalendarViewer._days_in_week):
            padding = ' ' * (self._day_width - (len(data[i]) if i < len(data) else 0) - 2)

            s += ' {}{} |'.format(data[i] if i < len(data) else '', padding)

        print(s)

    def print(self):
        self._terminal_size = shutil.get_terminal_size()

        print("Junho ·· 2018")

        self._day_width = (self._terminal_size.columns - (CalendarViewer._days_in_week + 1)) // CalendarViewer._days_in_week

        self._print_ruler()

        data = []
        for i in range(0, CalendarViewer._days_in_week):
            data.append('{}· {}'.format(i + 1, CalendarViewer._weekday_names_abrev[i]))

        self._print_line(data)
        self._print_line([])


if __name__ == '__main__':
    viewer = CalendarViewer()

    viewer.print()
