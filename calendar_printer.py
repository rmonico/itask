#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import datetime
import calendar as calendar_


class CalendarViewer(object):

    _days_in_week = 7
    _weekday_names = [
        'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo'
    ]
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
        self._events = {
            datetime.date(2021, 8, 10): [
                (datetime.time(16, 30), "Daily meeting 1"),
                (datetime.time(16, 30), "Daily meeting 2"),
                (datetime.time(16, 30), "Daily meeting 3"),
            ],
            datetime.date(2021, 8, 12): [
                (datetime.time(16, 30), "Daily meeting 1"),
                (datetime.time(16, 30), "Daily meeting 2"),
                (datetime.time(16, 30), "Daily meeting 3"),
                (datetime.time(16, 30), "Daily meeting 4"),
                (datetime.time(16, 30), "Daily meeting 5"),
            ],
            datetime.date(2021, 8, 26): [
                (datetime.time(16, 30), "Daily meeting"),
            ],
        }
        self._terminal_size = shutil.get_terminal_size()

        today = datetime.date.today()
        print(today.strftime('%B ·· %Y'))

        self._day_width = (
            self._terminal_size.columns -
            (CalendarViewer._days_in_week + 1)) // CalendarViewer._days_in_week

        self._print_ruler()

        cal = calendar_.Calendar(6)
        for week in cal.monthdatescalendar(today.year, today.month):
            line = '|'
            for day in week:
                label = f' {day.strftime("%d/%b (%a)")}'

                line += label + (' ' *
                                 (self._day_width - len(label) - 1)) + ' |'

            print(line)

            index = 0
            some_event_found = True
            while some_event_found:
                line = '|'
                some_event_found = False
                for day in week:
                    day_events = self._events.get(day, None)
                    if day_events and len(day_events) > index:
                        # import ipdb; ipdb.set_trace()
                        event = f' {day_events[index][0].strftime("%H:%M")}  {day_events[index][1]}'
                        some_event_found = True
                    else:
                        event = ''

                    line += event + (' ' *
                                     (self._day_width - len(event) - 1)) + ' |'

                print(line)

                index += 1

            self._print_ruler()

    def _get_events_for_day(self, day):
        events_of_day = list()

        for date, events in self._events:
            if date == day:
                events.extend(events_of_day)

        return events_of_day


if __name__ == '__main__':
    viewer = CalendarViewer()

    viewer.print()
