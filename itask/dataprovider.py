# -*- coding: utf-8 -*-

class DataSize:

    def __init__(self, lines, largest_line):
        super().__init__()

        self.lines = lines
        self.largest_line = largest_line


class DataProvider:

    def __init__(self):
        self.lines = None
        self.size = None

    def update(self, stream):
        self.lines = []

        largest_line = 0

        for line in stream.split('\n'):
            self.lines.append(line)

            if len(line) > largest_line:
                largest_line = len(line)

        self.size = DataSize(len(self.lines), largest_line)
