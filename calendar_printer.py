#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import datetime
import calendar as calendar_


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


    def print(self):
        self._terminal_size = shutil.get_terminal_size()

        today = datetime.date.today()
        print(today.strftime('%B ·· %Y'))

        self._day_width = (self._terminal_size.columns - (CalendarViewer._days_in_week + 1)) // CalendarViewer._days_in_week

        self._print_ruler()

        cal = calendar_.Calendar(6)
        for week in cal.monthdatescalendar(today.year, today.month):
            line = '|'
            for day in week:
                label = f' {day.strftime("%d/%b (%a)")}'

                line += label + (' ' * (self._day_width - len(label) - 1)) + ' |'

            print(line)

            self._print_ruler()



if __name__ == '__main__':
    viewer = CalendarViewer()

    viewer.print()

