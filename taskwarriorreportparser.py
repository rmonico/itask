#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re


class TaskwarriorReportParser(object):

    def __init__(self):
        self._id_column_start = None
        self._id_column_end = None

        # TODO Get this data from taskwarrior configs
        self._id_location_column_regex = re.compile('( |^)ID +')

    def set_header_line(self, header_line):
        match = self._id_location_column_regex.search(header_line)

        self._id_column_start = match.start()
        self._id_column_end = match.end() - 1

    def idColumnWidth(self):
        # TODO Put a warning saiyng that ID column must be the first
        return self._id_column_end - self._id_column_start + 1

    def getId(self, line):
        str_id = line[self._id_column_start:self._id_column_end].lstrip()

        if str_id.isdigit():
            return int(str_id)
